"""Serviço de autenticação institucional do app `core`."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.core.models import CargoPermitido
from apps.integracoes.coresso.adapter import CoressoAdapter
from apps.integracoes.coresso.port import (
    CargoCoresso,
    CoressoIdentity,
    CoressoPort,
)


@dataclass(frozen=True, slots=True)
class AuthenticatedSessionData:
    """Snapshot interno do usuário autenticado após o login."""

    usuario: Any
    rf: str
    nome: str
    email: str | None
    cpf: str | None
    cargo: CargoPermitido


class CargoNaoAutorizadoError(Exception):
    """Indica que nenhum cargo efetivo do usuário está autorizado."""


class AuthService:
    """Orquestra o login via CoreSSO e a sincronização local do usuário."""

    def __init__(self, coresso: CoressoPort | None = None) -> None:
        """Inicializa a dependência da borda externa de autenticação."""
        self.coresso = coresso or CoressoAdapter()

    def login(self, login: str, senha: str) -> AuthenticatedSessionData:
        """Autentica no CoreSSO, valida cargos e sincroniza o usuário local."""
        identidade = self.coresso.autenticar(login, senha)
        cargo_permitido = self._obter_cargo_autorizado(
            identidade.cargos_efetivos
        )

        if cargo_permitido is None:
            raise CargoNaoAutorizadoError(
                "Cargo nao autorizado para o sistema."
            )

        usuario = self._persistir_usuario(identidade, cargo_permitido)

        return AuthenticatedSessionData(
            usuario=usuario,
            rf=identidade.rf,
            nome=identidade.nome,
            email=identidade.email,
            cpf=identidade.cpf,
            cargo=cargo_permitido,
        )

    @staticmethod
    def _extrair_codigos_cargo(
        cargos: Iterable[CargoCoresso],
    ) -> list[int]:
        """Extrai os códigos válidos dos cargos efetivos na ordem recebida."""
        return [
            cargo.codigo_cargo
            for cargo in cargos
            if cargo.codigo_cargo is not None
        ]

    @staticmethod
    def _obter_cargo_autorizado(
        cargos: Iterable[CargoCoresso],
    ) -> CargoPermitido | None:
        """Seleciona o cargo autorizado que deve vincular o usuário local."""
        codigos_cargo = AuthService._extrair_codigos_cargo(cargos)
        if not codigos_cargo:
            return None

        cargos_autorizados = CargoPermitido.objects.filter(
            codigo_cargo__in=codigos_cargo,
        )
        cargos_por_codigo = {
            cargo.codigo_cargo: cargo for cargo in cargos_autorizados
        }

        for codigo_cargo in codigos_cargo:
            cargo_permitido = cargos_por_codigo.get(codigo_cargo)
            if cargo_permitido is not None:
                return cargo_permitido

        return None

    def _persistir_usuario(
        self,
        identidade: CoressoIdentity,
        cargo_permitido: CargoPermitido,
    ) -> Any:
        """Cria ou atualiza o usuário local sincronizado pelo login."""
        usuario_model = get_user_model()
        usuario = usuario_model.objects.filter(
            Q(rf=identidade.rf) | Q(username=identidade.rf)
        ).first()

        if usuario is None:
            usuario = usuario_model(username=identidade.rf, rf=identidade.rf)

        usuario.username = identidade.rf
        usuario.rf = identidade.rf
        usuario.nome_completo = identidade.nome
        usuario.email = identidade.email or ""
        usuario.cpf = identidade.cpf or ""
        usuario.cargo_permitido = cargo_permitido
        usuario.is_active = True
        usuario.last_login = timezone.now()

        with transaction.atomic():
            usuario.set_unusable_password()
            usuario.save()

        return usuario
