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
    DadosUnidadeEol,
    TipoEscolaEol,
    DreEol,
    EolPort,
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

    def _normalizar_tipo_escola(self, payload: dict[str, Any]) -> TipoEscolaEol:
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
    def _formatar_cep(cep: object) -> str:
        """Normaliza CEP numérico ou textual para o padrão ``00000-000``."""
        digitos = "".join(ch for ch in str(cep or "") if ch.isdigit())
        if not digitos:
            return ""
        digitos = digitos.zfill(8)[-8:]
        return f"{digitos[:5]}-{digitos[5:]}"
