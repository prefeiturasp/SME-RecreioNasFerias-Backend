"""Contrato da integração com a SME Integração/EOL.

Define a fronteira que os domínios consomem para sincronizar unidades
escolares sem depender do client HTTP concreto.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class TipoEscolaEol:
    """Tipo de escola normalizado a partir do catálogo bruto de tipos."""

    codigo: int
    descricao_sigla: str


@dataclass(frozen=True, slots=True)
class DreEol:
    """Diretoria Regional de Educação normalizada da EOL."""

    codigo_dre: str
    nome_dre: str
    sigla_dre: str


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
    codigo_eol: str
    sigla_tipo_escola: str
    nome_dre: str
    sigla_dre: str
    codigo_dre: str
    email: str
    telefone: str
    cep: str
    tipo_logradouro: str
    logradouro: str
    bairro: str
    numero: str
    complemento: str
    municipio: str
    uf: str


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
    tipo_logradouro: str
    logradouro: str
    bairro: str
    numero: str
    complemento: str
    nome_diretor: str


@dataclass(frozen=True, slots=True)
class AlunoEol:
    """Aluno normalizado a partir da consulta por código EOL."""

    codigo_aluno: int
    tipo_turno: int
    ano_letivo: int
    nome_aluno: str
    nome_social_aluno: str
    codigo_situacao_matricula: int
    situacao_matricula: str
    data_situacao: str
    data_nascimento: str
    numero_aluno_chamada: str
    codigo_turma: int
    nome_responsavel: str
    tipo_responsavel: str
    celular_responsavel: str
    data_atualizacao_contato: str
    codigo_tipo_turma: int
    turma_nome: str
    etapa_ensino: str
    ciclo_ensino: str
    desc_etapa_ensino: str
    desc_ciclo_ensino: str
    data_atualizacao_tabela: str


@dataclass(frozen=True, slots=True)
class InformacoesAlunoEol:
    """Ficha normalizada do aluno, com endereço em campos soltos."""

    nome_mae: str
    sexo: str
    grupo_etnico: str
    nacionalidade: str
    eh_imigrante: bool
    nis: str
    cns: str
    numero: str
    complemento: str
    bairro: str
    cep: str
    cidade: str
    uf: str
    tipo_logradouro: str
    logradouro: str


@dataclass(frozen=True, slots=True)
class ParticipanteRedeEol:
    """Aluno da rede já unido à ficha, pronto para o restante do sistema."""

    codigo_aluno: int
    tipo_turno: int
    ano_letivo: int
    nome_aluno: str
    nome_social_aluno: str
    codigo_situacao_matricula: int
    situacao_matricula: str
    data_situacao: str
    data_nascimento: str
    numero_aluno_chamada: str
    codigo_turma: int
    nome_responsavel: str
    tipo_responsavel: str
    celular_responsavel: str
    data_atualizacao_contato: str
    codigo_tipo_turma: int
    turma_nome: str
    etapa_ensino: str
    ciclo_ensino: str
    desc_etapa_ensino: str
    desc_ciclo_ensino: str
    data_atualizacao_tabela: str
    nome_mae: str
    sexo: str
    grupo_etnico: str
    nacionalidade: str
    eh_imigrante: bool
    nis: str
    cns: str
    numero: str
    complemento: str
    bairro: str
    cep: str
    cidade: str
    uf: str
    tipo_logradouro: str
    logradouro: str
    responsavel_nome_social: str = ""
    telefone_contato_2: str = ""
    email: str = ""


class EolPort(ABC):
    """Define as operações esperadas da integração de escolas da SME."""

    @abstractmethod
    def listar_tipos_escola(self) -> tuple[TipoEscolaEol, ...]:
        """Lista os tipos de escola do catálogo bruto da EOL."""

    @abstractmethod
    def listar_dres(self) -> tuple[DreEol, ...]:
        """Lista as Diretorias Regionais de Educação."""

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

    @abstractmethod
    def listar_alunos(self, codigo_eol: str) -> tuple[AlunoEol, ...]:
        """Lista os alunos normalizados pelo código EOL."""

    @abstractmethod
    def obter_informacoes_aluno(
        self,
        codigo_eol: str,
    ) -> InformacoesAlunoEol | None:
        """Obtém a ficha normalizada do aluno, ou ``None`` quando ausente."""

    @abstractmethod
    def consultar_participante(
        self,
        codigo_eol: str,
    ) -> ParticipanteRedeEol | None:
        """Une aluno e ficha. ``None`` quando a lista de alunos vem vazia."""
