"""Casos de uso do domínio de polos."""

from __future__ import annotations

from typing import Any

from django.db import transaction
from django.db.models import Q, QuerySet

from apps.integracoes.eol.adapter import EolAdapter
from apps.integracoes.eol.port import DreEol, EolPort, TipoEscolaEol
from apps.polos.constants import StatusPolo, TipoPolo
from apps.polos.models import Polo


def _normalizar(valor: str | None) -> str:
    """Remove espaços nas bordas, tratando valores ausentes como vazios."""
    return (valor or "").strip()


class PoloService:
    """Orquestra criação, consulta e alteração de polos."""

    def __init__(self, eol: EolPort | None = None) -> None:
        """Inicializa o serviço adiando a criação da integração EOL."""
        self._eol = eol

    @property
    def eol(self) -> EolPort:
        """Cria a integração EOL apenas quando ela é efetivamente usada."""
        if self._eol is None:
            self._eol = EolAdapter()
        return self._eol

    def listar_tipos_escola(self) -> tuple[TipoEscolaEol, ...]:
        """Lista tipos de escola normalizados pela integração EOL."""
        return self.eol.listar_tipos_escola()

    def listar_dres(self) -> tuple[DreEol, ...]:
        """Lista DREs normalizadas pela integração EOL."""
        return self.eol.listar_dres()

    def listar(
        self,
        *,
        dre_codigo_eol: str | None = None,
        tipo_ue: str | None = None,
        busca: str | None = None,
    ) -> QuerySet[Polo]:
        """Lista polos aplicando os filtros informados."""
        consulta = Polo.objects.all()

        dre_codigo_eol = _normalizar(dre_codigo_eol)
        if dre_codigo_eol:
            consulta = consulta.filter(dre_codigo_eol=dre_codigo_eol)

        tipo_ue = _normalizar(tipo_ue)
        if tipo_ue:
            consulta = consulta.filter(tipo_ue=tipo_ue)

        busca = _normalizar(busca)
        if busca:
            consulta = consulta.filter(
                Q(nome_polo__icontains=busca) | Q(nome_osc__icontains=busca)
            )

        return consulta

    def obter(self, uuid: object) -> Polo:
        """Obtém um polo pelo UUID público."""
        return Polo.objects.get(uuid=uuid)

    @transaction.atomic
    def criar(self, **dados: Any) -> Polo:
        """Cria um polo sempre pendente e ativo."""
        dados.pop("tipo", None)
        dados.pop("status", None)
        polo = Polo(
            tipo=TipoPolo.PENDENTE,
            status=StatusPolo.ATIVO,
            **dados,
        )
        polo.save()
        return polo

    @transaction.atomic
    def atualizar(self, polo: Polo, **dados: Any) -> Polo:
        """Atualiza um polo e reaplica as validações do domínio."""
        dados.pop("ativo", None)
        for campo, valor in dados.items():
            setattr(polo, campo, valor)
        polo.save()
        return polo

    @transaction.atomic
    def excluir(self, polo: Polo) -> None:
        """Exclui um polo cadastrado."""
        polo.delete()
