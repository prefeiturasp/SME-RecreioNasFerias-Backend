"""Adaptador da integração com a SME Integração/EOL.

Implementa o contrato consumido pelos domínios e centraliza a normalização
dos payloads brutos e o enriquecimento das unidades escolares.
"""

from __future__ import annotations

from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Protocol, cast

from apps.integracoes.eol.client import EolClient
from apps.integracoes.eol.constants import (
    CODIGO_CARGO_DIRETOR_ESCOLA,
    MAX_WORKERS_PADRAO,
    SIGLAS_TIPO_UE_RECREIO,
)
from apps.integracoes.eol.exceptions import (
    EolContratoError,
    EolIndisponivelError,
)
from apps.integracoes.eol.port import (
    AlunoEol,
    DadosUnidadeEol,
    DreEol,
    EolPort,
    InformacoesAlunoEol,
    ParticipanteRedeEol,
    TipoEscolaEol,
    UnidadeEol,
    UnidadeRecreioEol,
)


class EolEscolasClient(Protocol):
    """Protocolo mínimo do client HTTP usado pelo adaptador."""

    def listar_tipos_escola(self) -> list[dict[str, Any]]:
        """Devolve a lista bruta de tipos de escola do catálogo da EOL."""

    def listar_dres(self) -> list[dict[str, Any]]:
        """Devolve a lista bruta de Diretorias Regionais de Educação."""

    def listar_todas_unidades(self) -> list[dict[str, Any]]:
        """Devolve a lista bruta de unidades escolares."""

    def obter_dados_unidade(self, codigo_eol: str) -> dict[str, Any] | None:
        """Devolve os dados brutos de uma unidade ou ``None``."""

    def obter_funcionarios_por_cargo(
        self,
        codigo_eol: str,
        codigo_cargo: int,
    ) -> list[dict[str, Any]]:
        """Devolve a lista bruta de funcionários no cargo informado."""

    def listar_alunos(self, codigo_eol: str) -> list[dict[str, Any]]:
        """Devolve a lista bruta de alunos pelo código EOL."""

    def obter_informacoes_aluno(
        self,
        codigo_aluno: str,
    ) -> dict[str, Any] | None:
        """Devolve a ficha bruta do aluno ou ``None``."""


class EolAdapter(EolPort):
    """Normaliza e enriquece os dados da integração de escolas da SME."""

    def __init__(
        self,
        client: EolEscolasClient | None = None,
        *,
        max_workers: int | None = None,
    ) -> None:
        """Inicializa o adaptador com o client HTTP.

        Args:
            client: Client HTTP concreto a ser usado pelo adaptador. Quando
                omitido, utiliza a implementação padrão do projeto.
            max_workers: Limite de requisições paralelas no enriquecimento.
                Quando omitido, usa o padrão do projeto.
        """
        self.client = client or EolClient()
        self.max_workers = max_workers or MAX_WORKERS_PADRAO

    def listar_tipos_escola(self) -> tuple[TipoEscolaEol, ...]:
        """Normaliza o catálogo de tipos de escola da integração."""
        return tuple(
            self._normalizar_tipo_escola(tipo)
            for tipo in self.client.listar_tipos_escola()
        )

    def listar_dres(self) -> tuple[DreEol, ...]:
        """Normaliza o catálogo de DREs da integração."""
        return tuple(
            self._normalizar_dre(dre) for dre in self.client.listar_dres()
        )

    def listar_todas_unidades(self) -> tuple[UnidadeEol, ...]:
        """Normaliza o catálogo bruto de unidades em contratos tipados."""
        unidades = self.client.listar_todas_unidades()
        return tuple(self._normalizar_unidade(u) for u in unidades)

    def obter_dados_unidade(self, codigo_eol: str) -> DadosUnidadeEol | None:
        """Normaliza os dados detalhados de uma unidade escolar.

        Args:
            codigo_eol: Código EOL da escola.

        Returns:
            Dados normalizados ou ``None`` quando a unidade não é encontrada.
        """
        dados = self.client.obter_dados_unidade(codigo_eol)
        if dados is None:
            return None
        return self._normalizar_dados(dados)

    def obter_nome_diretor(
        self,
        codigo_eol: str,
        codigo_cargo: int | None = None,
    ) -> str:
        """Obtém o nome do primeiro diretor retornado pela integração.

        Args:
            codigo_eol: Código EOL da escola.
            codigo_cargo: Código do cargo. Quando ``None``, usa o código padrão
                de Diretor de Escola.

        Returns:
            Nome do diretor ou string vazia quando ausente.
        """
        cargo = codigo_cargo or CODIGO_CARGO_DIRETOR_ESCOLA
        funcionarios = self.client.obter_funcionarios_por_cargo(
            codigo_eol,
            cargo,
        )
        if not funcionarios:
            return ""
        return self._texto(funcionarios[0].get("nomeServidor"))

    def filtrar_unidades_recreio(
        self,
        unidades: Iterable[UnidadeEol],
    ) -> tuple[UnidadeEol, ...]:
        """Filtra unidades pelos tipos de UE elegíveis ao programa."""
        return tuple(
            unidade
            for unidade in unidades
            if self._texto(unidade.sigla_tipo_escola) in SIGLAS_TIPO_UE_RECREIO
        )

    def enriquecer_unidades(
        self,
        unidades: Iterable[UnidadeEol],
    ) -> tuple[UnidadeRecreioEol, ...]:
        """Enriquece unidades com dados detalhados e nome do diretor.

        O enriquecimento é paralelo e tolerante a falhas pontuais: quando uma
        unidade não consegue ser enriquecida, os dados básicos do catálogo são
        mantidos.

        Returns:
            Unidades enriquecidas ordenadas por nome de escola e código EOL.
        """
        lista = list(unidades)
        if not lista:
            return ()

        workers = min(self.max_workers, len(lista))
        enriquecidas: list[UnidadeRecreioEol] = []
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futuros = {
                executor.submit(self._enriquecer_unidade, unidade): unidade
                for unidade in lista
            }
            for futuro in as_completed(futuros):
                unidade = futuros[futuro]
                try:
                    enriquecidas.append(futuro.result())
                except Exception:  # noqa: BLE001 - falha pontual não aborta
                    enriquecidas.append(
                        self._unidade_sem_enriquecimento(unidade)
                    )

        enriquecidas.sort(
            key=lambda item: (item.nome_escola.casefold(), item.codigo_eol)
        )
        return tuple(enriquecidas)

    def listar_unidades_diretas_recreio(
        self,
        *,
        limite: int | None = None,
    ) -> tuple[UnidadeRecreioEol, ...]:
        """Lista unidades elegíveis já enriquecidas para a sincronização.

        Args:
            limite: Quando informado, limita a quantidade de unidades filtradas
                antes do enriquecimento (útil para testes).
        """
        filtradas = self.filtrar_unidades_recreio(self.listar_todas_unidades())
        if limite is not None:
            filtradas = filtradas[: max(0, limite)]
        return self.enriquecer_unidades(filtradas)

    def listar_alunos(self, codigo_eol: str) -> tuple[AlunoEol, ...]:
        """Normaliza a lista bruta de alunos da consulta por código EOL.

        Args:
            codigo_eol: Código EOL do aluno.

        Returns:
            Alunos normalizados. Tupla vazia significa código não encontrado.
        """
        return tuple(
            self._normalizar_aluno(aluno)
            for aluno in self.client.listar_alunos(codigo_eol)
        )

    def obter_informacoes_aluno(
        self,
        codigo_eol: str,
    ) -> InformacoesAlunoEol | None:
        """Normaliza a ficha do aluno.

        Args:
            codigo_eol: Código EOL do aluno.

        Returns:
            Ficha normalizada ou ``None`` quando a integração responde 404.
        """
        dados = self.client.obter_informacoes_aluno(codigo_eol)
        if dados is None:
            return None
        return self._normalizar_informacoes(dados)

    def consultar_participante(
        self,
        codigo_eol: str,
    ) -> ParticipanteRedeEol | None:
        """Une o primeiro aluno à ficha.

        Lista vazia devolve ``None`` e não consulta a ficha. Quando a ficha
        não existe, o participante permanece com os dados do aluno e o
        endereço vazio.

        Args:
            codigo_eol: Código EOL do aluno.

        Returns:
            Participante unido ou ``None`` quando não há aluno.
        """
        alunos = self.listar_alunos(codigo_eol)
        if not alunos:
            return None
        ficha = self.obter_informacoes_aluno(codigo_eol)
        return self._montar_participante(alunos[0], ficha)

    def _normalizar_unidade(self, payload: dict[str, Any]) -> UnidadeEol:
        """Converte um item do catálogo bruto em ``UnidadeEol``."""
        return UnidadeEol(
            codigo_eol=self._texto(payload.get("codigoEscola")),
            nome_escola=self._texto(payload.get("nomeEscola")),
            sigla_tipo_escola=self._texto(payload.get("siglaTipoEscola")),
            nome_dre=self._texto(payload.get("nomeDRE")),
            sigla_dre=self._texto(payload.get("siglaDRE")),
            codigo_dre=self._texto(payload.get("codigoDRE")),
        )

    def _normalizar_aluno(self, payload: dict[str, Any]) -> AlunoEol:
        """Converte um item bruto de aluno em ``AlunoEol``."""
        return AlunoEol(
            codigo_aluno=self._inteiro(payload.get("codigoAluno")),
            tipo_turno=self._inteiro(payload.get("tipoTurno")),
            ano_letivo=self._inteiro(payload.get("anoLetivo")),
            nome_aluno=self._texto(payload.get("nomeAluno")),
            nome_social_aluno=self._texto(payload.get("nomeSocialAluno")),
            codigo_situacao_matricula=self._inteiro(
                payload.get("codigoSituacaoMatricula"),
            ),
            situacao_matricula=self._texto(payload.get("situacaoMatricula")),
            data_situacao=self._texto(payload.get("dataSituacao")),
            data_nascimento=self._texto(payload.get("dataNascimento")),
            numero_aluno_chamada=self._texto(
                payload.get("numeroAlunoChamada"),
            ),
            codigo_turma=self._inteiro(payload.get("codigoTurma")),
            nome_responsavel=self._texto(payload.get("nomeResponsavel")),
            tipo_responsavel=self._texto(payload.get("tipoResponsavel")),
            celular_responsavel=self._texto(
                payload.get("celularResponsavel"),
            ),
            data_atualizacao_contato=self._texto(
                payload.get("dataAtualizacaoContato"),
            ),
            codigo_tipo_turma=self._inteiro(payload.get("codigoTipoTurma")),
            turma_nome=self._texto(payload.get("turmaNome")),
            etapa_ensino=self._texto(payload.get("etapaEnsino")),
            ciclo_ensino=self._texto(payload.get("cicloEnsino")),
            desc_etapa_ensino=self._texto(payload.get("descEtapaEnsino")),
            desc_ciclo_ensino=self._texto(payload.get("descCicloEnsino")),
            data_atualizacao_tabela=self._texto(
                payload.get("dataAtualizacaoTabela"),
            ),
        )

    def _normalizar_informacoes(
        self,
        payload: dict[str, Any],
    ) -> InformacoesAlunoEol:
        """Converte a ficha bruta em ``InformacoesAlunoEol``."""
        endereco = payload.get("endereco")
        if not isinstance(endereco, dict):
            endereco = {}
        return InformacoesAlunoEol(
            nome_mae=self._texto(payload.get("nomeMae")),
            sexo=self._texto(payload.get("sexo")),
            grupo_etnico=self._texto(payload.get("grupoEtnico")),
            nacionalidade=self._texto(payload.get("nacionalidade")),
            eh_imigrante=self._booleano(payload.get("ehImigrante")),
            nis=self._texto(payload.get("nis")),
            cns=self._texto(payload.get("cns")),
            numero=self._texto(endereco.get("nro")),
            complemento=self._texto(endereco.get("complemento")),
            bairro=self._texto(endereco.get("bairro")),
            cep=self._formatar_cep(endereco.get("cep")),
            cidade=self._texto(endereco.get("nomeMunicipio")),
            uf=self._texto(endereco.get("siglaUF")),
            tipo_logradouro=self._texto(endereco.get("tipologradouro")),
            logradouro=self._texto(endereco.get("logradouro")),
        )

    def _montar_participante(
        self,
        aluno: AlunoEol,
        ficha: InformacoesAlunoEol | None,
    ) -> ParticipanteRedeEol:
        """Copia a ficha por cima do aluno.

        Ficha ausente preenche mãe, documentos e endereço com vazio.
        """
        dados = ficha if ficha is not None else self._informacoes_vazias()
        return ParticipanteRedeEol(
            codigo_aluno=aluno.codigo_aluno,
            tipo_turno=aluno.tipo_turno,
            ano_letivo=aluno.ano_letivo,
            nome_aluno=aluno.nome_aluno,
            nome_social_aluno=aluno.nome_social_aluno,
            codigo_situacao_matricula=aluno.codigo_situacao_matricula,
            situacao_matricula=aluno.situacao_matricula,
            data_situacao=aluno.data_situacao,
            data_nascimento=aluno.data_nascimento,
            numero_aluno_chamada=aluno.numero_aluno_chamada,
            codigo_turma=aluno.codigo_turma,
            nome_responsavel=aluno.nome_responsavel,
            tipo_responsavel=aluno.tipo_responsavel,
            celular_responsavel=aluno.celular_responsavel,
            data_atualizacao_contato=aluno.data_atualizacao_contato,
            codigo_tipo_turma=aluno.codigo_tipo_turma,
            turma_nome=aluno.turma_nome,
            etapa_ensino=aluno.etapa_ensino,
            ciclo_ensino=aluno.ciclo_ensino,
            desc_etapa_ensino=aluno.desc_etapa_ensino,
            desc_ciclo_ensino=aluno.desc_ciclo_ensino,
            data_atualizacao_tabela=aluno.data_atualizacao_tabela,
            nome_mae=dados.nome_mae,
            sexo=dados.sexo,
            grupo_etnico=dados.grupo_etnico,
            nacionalidade=dados.nacionalidade,
            eh_imigrante=dados.eh_imigrante,
            nis=dados.nis,
            cns=dados.cns,
            numero=dados.numero,
            complemento=dados.complemento,
            bairro=dados.bairro,
            cep=dados.cep,
            cidade=dados.cidade,
            uf=dados.uf,
            tipo_logradouro=dados.tipo_logradouro,
            logradouro=dados.logradouro,
        )

    @staticmethod
    def _informacoes_vazias() -> InformacoesAlunoEol:
        """Devolve a ficha vazia usada quando a EOL responde 404."""
        return InformacoesAlunoEol(
            nome_mae="",
            sexo="",
            grupo_etnico="",
            nacionalidade="",
            eh_imigrante=False,
            nis="",
            cns="",
            numero="",
            complemento="",
            bairro="",
            cep="",
            cidade="",
            uf="",
            tipo_logradouro="",
            logradouro="",
        )

    def _normalizar_tipo_escola(
        self, payload: dict[str, Any]
    ) -> TipoEscolaEol:
        """Converte um item do catálogo bruto em ``TipoEscolaEol``."""
        return TipoEscolaEol(
            codigo=int(payload.get("codigo", 0)),
            descricao_sigla=self._texto(payload.get("descricaoSigla")),
        )

    def _normalizar_dre(self, payload: dict[str, Any]) -> DreEol:
        """Converte uma DRE do payload externo para o contrato interno."""
        return DreEol(
            codigo_dre=self._texto(payload.get("codigoDRE")),
            nome_dre=self._texto(payload.get("nomeDRE")),
            sigla_dre=self._texto(payload.get("siglaDRE")),
        )

    def _normalizar_dados(self, payload: dict[str, Any]) -> DadosUnidadeEol:
        """Converte o payload de dados detalhados em ``DadosUnidadeEol``."""
        return DadosUnidadeEol(
            nome=self._texto(payload.get("nome")),
            codigo_eol=self._texto(payload.get("codigo")),
            sigla_tipo_escola=self._texto(payload.get("siglaTipoEscola")),
            nome_dre=self._texto(payload.get("nomeDRE")),
            sigla_dre=self._texto(payload.get("siglaDRE")),
            codigo_dre=self._texto(payload.get("codigoDRE")),
            email=self._texto(payload.get("email")),
            telefone=self._texto(payload.get("telefone")),
            cep=self._formatar_cep(payload.get("cep")),
            tipo_logradouro=self._texto(payload.get("tipoLogradouro")),
            logradouro=self._texto(payload.get("logradouro")),
            bairro=self._texto(payload.get("bairro")),
            numero=self._texto(payload.get("numero")),
            complemento=self._texto(payload.get("complemento")),
            municipio=self._texto(payload.get("municipio")),
            uf=self._texto(payload.get("uf")),
        )

    def _enriquecer_unidade(self, unidade: UnidadeEol) -> UnidadeRecreioEol:
        """Agrega dados detalhados e nome do diretor a uma unidade."""
        codigo_eol = unidade.codigo_eol
        dados = self._consultar_dados_unidade_seguro(codigo_eol)
        nome_diretor = self._consultar_diretor_seguro(codigo_eol)

        return UnidadeRecreioEol(
            codigo_eol=codigo_eol,
            nome_escola=self._escolher_campo(
                dados,
                "nome",
                unidade.nome_escola,
            ),
            sigla_tipo_escola=self._escolher_campo(
                dados,
                "sigla_tipo_escola",
                unidade.sigla_tipo_escola,
            ),
            nome_dre=self._escolher_campo(dados, "nome_dre", unidade.nome_dre),
            sigla_dre=self._escolher_campo(
                dados,
                "sigla_dre",
                unidade.sigla_dre,
            ),
            codigo_dre=self._escolher_campo(
                dados,
                "codigo_dre",
                unidade.codigo_dre,
            ),
            email=dados.email if dados else "",
            telefone=dados.telefone if dados else "",
            cep=dados.cep if dados else "",
            tipo_logradouro=dados.tipo_logradouro if dados else "",
            logradouro=dados.logradouro if dados else "",
            bairro=dados.bairro if dados else "",
            numero=dados.numero if dados else "",
            complemento=dados.complemento if dados else "",
            nome_diretor=nome_diretor,
        )

    def _consultar_dados_unidade_seguro(
        self,
        codigo_eol: str,
    ) -> DadosUnidadeEol | None:
        """Consulta dados detalhados sem propagar falha pontual."""
        try:
            return self.obter_dados_unidade(codigo_eol)
        except (EolIndisponivelError, EolContratoError):
            return None

    def _consultar_diretor_seguro(self, codigo_eol: str) -> str:
        """Consulta o diretor da unidade sem propagar falha pontual."""
        try:
            return self.obter_nome_diretor(codigo_eol)
        except (EolIndisponivelError, EolContratoError):
            return ""

    @staticmethod
    def _escolher_campo(
        dados: DadosUnidadeEol | None,
        campo: str,
        fallback: str,
    ) -> str:
        """Prefere o campo detalhado; usa o catálogo como fallback."""
        if dados is not None:
            valor = cast(str, getattr(dados, campo))
            if valor:
                return valor
        return fallback

    @staticmethod
    def _unidade_sem_enriquecimento(unidade: UnidadeEol) -> UnidadeRecreioEol:
        """Mantém os dados do catálogo quando o enriquecimento falha."""
        return UnidadeRecreioEol(
            codigo_eol=unidade.codigo_eol,
            nome_escola=unidade.nome_escola,
            sigla_tipo_escola=unidade.sigla_tipo_escola,
            nome_dre=unidade.nome_dre,
            sigla_dre=unidade.sigla_dre,
            codigo_dre=unidade.codigo_dre,
            email="",
            telefone="",
            cep="",
            tipo_logradouro="",
            logradouro="",
            bairro="",
            numero="",
            complemento="",
            nome_diretor="",
        )

    @staticmethod
    def _texto(valor: object) -> str:
        """Converte valor em string sem espaços nas bordas."""
        if valor is None:
            return ""
        return str(valor).strip()

    @staticmethod
    def _inteiro(valor: object) -> int:
        """Converte valor inteiro. Ausente ou inválido vira zero."""
        if isinstance(valor, int) and not isinstance(valor, bool):
            return valor
        return 0

    @staticmethod
    def _booleano(valor: object) -> bool:
        """Aceita somente bool. Qualquer outro valor vira ``False``."""
        if isinstance(valor, bool):
            return valor
        return False

    @staticmethod
    def _formatar_cep(cep: object) -> str:
        """Normaliza CEP numérico ou textual para o padrão ``00000-000``."""
        digitos = "".join(ch for ch in str(cep or "") if ch.isdigit())
        if not digitos:
            return ""
        digitos = digitos.zfill(8)[-8:]
        return f"{digitos[:5]}-{digitos[5:]}"
