"""Contrato da integração com o CoreSSO.

Define a fronteira que o `core` consome para autenticação institucional sem
acoplamento direto à implementação HTTP.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class CargoCoresso:
    """Representa um cargo retornado pelo CoreSSO."""

    codigo_cargo: int | None
    descricao_cargo: str


@dataclass(frozen=True, slots=True)
class UnidadeCoresso:
    """Representa uma unidade retornada pelo CoreSSO."""

    codigo: str
    nome_unidade: str


@dataclass(frozen=True, slots=True)
class CoressoIdentity:
    """Identidade normalizada retornada pelo fluxo de autenticação."""

    usuario_id_externo: str | None
    rf: str
    nome: str
    email: str | None
    cpf: str | None
    cargos: tuple[CargoCoresso, ...]
    cargos_sobrepostos: tuple[CargoCoresso, ...]
    cargos_efetivos: tuple[CargoCoresso, ...]
    perfis: tuple[str, ...]
    unidades_lotacao: tuple[UnidadeCoresso, ...]
    unidade_exercicio: UnidadeCoresso | None
    payload_bruto: dict[str, Any]


class CoressoPort(ABC):
    """Define as operações esperadas para autenticação institucional."""

    @abstractmethod
    def autenticar(self, rf: str, senha: str) -> CoressoIdentity:
        """Autentica um usuário institucional.

        Args:
            rf: Registro funcional informado no login.
            senha: Senha institucional informada pelo usuário.

        Returns:
            Identidade normalizada retornada pela autenticação institucional.
        """
