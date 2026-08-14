"""Contrato da integração com a SME Integração/EOL.

Define a fronteira que os domínios consomem para sincronizar unidades
escolares sem depender do client HTTP concreto.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class UnidadeEol:
    """Unidade escolar normalizada a partir do catálogo bruto de unidades."""

    codigo_eol: str
    nome_escola: str
    sigla_tipo_escola: str
    nome_dre: str
    sigla_dre: str
    codigo_dre: str


@dataclass(frozen=True, slots=True)
class DadosUnidadeEol:
    """Dados detalhados normalizados de uma unidade escolar."""

    nome: str
    sigla_tipo_escola: str
    nome_dre: str
    sigla_dre: str
    codigo_dre: str
    email: str
    telefone: str
    cep: str
    endereco: str


@dataclass(frozen=True, slots=True)
class UnidadeRecreioEol:
    """Unidade enriquecida pronta para a sincronização de polos diretos."""

    codigo_eol: str
    nome_escola: str
    sigla_tipo_escola: str
    nome_dre: str
    sigla_dre: str
    codigo_dre: str
    email: str
    telefone: str
    cep: str
    endereco: str
    nome_diretor: str


class EolPort(ABC):
    """Define as operações esperadas da integração de escolas da SME."""

    @abstractmethod
    def listar_todas_unidades(self) -> tuple[UnidadeEol, ...]:
        """Lista o catálogo bruto de unidades escolares."""

    @abstractmethod
    def obter_dados_unidade(self, codigo_eol: str) -> DadosUnidadeEol | None:
        """Obtém os dados detalhados de uma unidade pelo código EOL."""

    @abstractmethod
    def obter_nome_diretor(
        self,
        codigo_eol: str,
        codigo_cargo: int | None = None,
    ) -> str:
        """Obtém o nome do diretor da unidade pelo código de cargo."""

    @abstractmethod
    def filtrar_unidades_recreio(
        self,
        unidades: Iterable[UnidadeEol],
    ) -> tuple[UnidadeEol, ...]:
        """Filtra unidades pelos tipos de UE elegíveis ao programa."""

    @abstractmethod
    def enriquecer_unidades(
        self,
        unidades: Iterable[UnidadeEol],
    ) -> tuple[UnidadeRecreioEol, ...]:
        """Enriquece unidades com dados detalhados e nome do diretor."""

    @abstractmethod
    def listar_unidades_diretas_recreio(
        self,
        *,
        limite: int | None = None,
    ) -> tuple[UnidadeRecreioEol, ...]:
        """Lista unidades elegíveis já enriquecidas para a sincronização."""
