"""
Serviço HTTP para consulta de escolas na SME Integração API.

Consome ``/api/escolas/todas-unidades``, ``/api/escolas/dados/{eol}`` e
``/api/escolas/{eol}/funcionarios/cargos/{cargo}`` com o header
``x-api-eol-key``, reutilizando as variáveis ``AUTH_API_*``.
"""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import requests  # type: ignore[import-untyped]
from requests import exceptions as excecoes_requests

# Origem: campo ``codigoCargo`` do catálogo oficial de cargos SME
# (retorno da API SIGPAE / CoreSSO — ``nomeCargo`` = ``DIRETOR DE ESCOLA``).
# Mesmo código seedado em ``usuarios.migrations.0008_cargopermitidomodel``.
# Usado em ``GET /api/escolas/{eol}/funcionarios/cargos/{codigo}``.
# Configurável no ``.env`` via ``AUTH_API_CODIGO_CARGO_DIRETOR_ESCOLA``.
_CODIGO_CARGO_DIRETOR_ESCOLA_PADRAO = 3360

SIGLAS_TIPO_UE_RECREIO = frozenset(
    {
        "EMEF",
        "EMEI",
        "EMEI P FOM",
        "CEI DIRET",
        "CEI INDIR",
        "CEU",
        "CEU EMEI",
        "CEU CEI",
        "CEU CEMEI",
    }
)

_TIMEOUT_CONEXAO_PADRAO_SEGUNDOS = 10
_TIMEOUT_LEITURA_PADRAO_SEGUNDOS = 30
_MAX_WORKERS_PADRAO = 8


class EscolasIntegracaoIndisponivelError(Exception):
    """Indica falha de comunicação com a SME Integração API."""


class EscolasIntegracaoConfigError(Exception):
    """Indica ausência de configuração obrigatória da integração."""


def _inteiro_do_ambiente(nome: str, padrao: int) -> int:
    """Lê variável de ambiente inteira positiva ou retorna o padrão."""
    bruto = os.getenv(nome, "").strip()
    if not bruto:
        return padrao
    try:
        return max(1, int(bruto))
    except ValueError:
        return padrao


def codigo_cargo_diretor_escola() -> int:
    """Código do cargo Diretor de Escola usado na SME Integração API.

    Lê ``AUTH_API_CODIGO_CARGO_DIRETOR_ESCOLA`` do ambiente (``.env``);
    se ausente, usa o padrão documentado do catálogo SME (3360).
    """
    return _inteiro_do_ambiente(
        "AUTH_API_CODIGO_CARGO_DIRETOR_ESCOLA",
        _CODIGO_CARGO_DIRETOR_ESCOLA_PADRAO,
    )


# Alias do padrão documentado (útil em asserts de teste).
CODIGO_CARGO_DIRETOR_ESCOLA = _CODIGO_CARGO_DIRETOR_ESCOLA_PADRAO


class EscolasIntegracaoService:
    """Cliente HTTP das escolas na SME Integração API.

    Attributes:
        base_url: URL base sem barra final.
        api_eol_key: Valor do header ``x-api-eol-key``.
        connect_timeout_seconds: Timeout de conexão TCP.
        read_timeout_seconds: Timeout de leitura das respostas.
        max_workers: Limite de requisições paralelas no enriquecimento.
    """

    def __init__(
        self,
        base_url: str | None = None,
        api_eol_key: str | None = None,
        connect_timeout_seconds: int | None = None,
        read_timeout_seconds: int | None = None,
        max_workers: int | None = None,
    ) -> None:
        """Configura o cliente a partir do ambiente ou parâmetros explícitos."""
        origem_base = (
            os.getenv("AUTH_API_BASE_URL", "") if base_url is None else base_url
        )
        origem_chave = (
            os.getenv("AUTH_API_EOL_KEY", "") if api_eol_key is None else api_eol_key
        )
        self.base_url = origem_base.rstrip("/")
        self.api_eol_key = origem_chave.strip()
        self.connect_timeout_seconds = (
            _inteiro_do_ambiente(
                "AUTH_API_CONNECT_TIMEOUT_SECONDS",
                _TIMEOUT_CONEXAO_PADRAO_SEGUNDOS,
            )
            if connect_timeout_seconds is None
            else connect_timeout_seconds
        )
        self.read_timeout_seconds = (
            _inteiro_do_ambiente(
                "AUTH_API_TIMEOUT_SECONDS",
                _TIMEOUT_LEITURA_PADRAO_SEGUNDOS,
            )
            if read_timeout_seconds is None
            else read_timeout_seconds
        )
        self.max_workers = (
            _inteiro_do_ambiente(
                "ESCOLAS_INTEGRACAO_MAX_WORKERS",
                _MAX_WORKERS_PADRAO,
            )
            if max_workers is None
            else max(1, max_workers)
        )

    def _garantir_configuracao(self) -> None:
        """Valida presença de URL base e chave de API."""
        if not self.base_url:
            raise EscolasIntegracaoConfigError("AUTH_API_BASE_URL não configurada")
        if not self.api_eol_key:
            raise EscolasIntegracaoConfigError("AUTH_API_EOL_KEY não configurada")

    def _cabecalhos(self) -> dict[str, str]:
        """Retorna cabeçalhos obrigatórios das chamadas à integração."""
        return {"x-api-eol-key": self.api_eol_key}

    def _timeouts(self) -> tuple[int, int]:
        """Monta tupla ``(conexão, leitura)`` para ``requests``."""
        return (self.connect_timeout_seconds, self.read_timeout_seconds)

    def _requisicao(
        self,
        metodo: str,
        url: str,
    ) -> requests.Response:
        """Executa requisição HTTP e trata falhas de rede/serviço."""
        try:
            return requests.request(
                metodo,
                url,
                headers=self._cabecalhos(),
                timeout=self._timeouts(),
            )
        except excecoes_requests.RequestException as exc:
            raise EscolasIntegracaoIndisponivelError(
                "SME Integração API indisponível",
            ) from exc

    def listar_todas_unidades(self) -> list[dict[str, Any]]:
        """Busca a lista completa de unidades em ``/api/escolas/todas-unidades``.

        Returns:
            list[dict[str, Any]]: Unidades retornadas pela API.

        Raises:
            EscolasIntegracaoConfigError: Configuração ausente.
            EscolasIntegracaoIndisponivelError: Falha HTTP ou payload inválido.
        """
        self._garantir_configuracao()
        url = f"{self.base_url}/api/escolas/todas-unidades"
        resposta = self._requisicao("GET", url)

        if resposta.status_code >= 500 or not resposta.ok:
            raise EscolasIntegracaoIndisponivelError(
                f"Falha ao listar unidades (HTTP {resposta.status_code})",
            )

        try:
            dados = resposta.json()
        except ValueError as exc:
            raise EscolasIntegracaoIndisponivelError(
                "Resposta inválida ao listar unidades",
            ) from exc

        if not isinstance(dados, list):
            raise EscolasIntegracaoIndisponivelError(
                "Resposta de unidades em formato inesperado",
            )
        return [item for item in dados if isinstance(item, dict)]

    def filtrar_unidades_recreio(
        self,
        unidades: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Filtra unidades pelos tipos de UE do Recreio nas Férias.

        Args:
            unidades: Lista bruta de ``todas-unidades``.

        Returns:
            Unidades cuja ``siglaTipoEscola`` está em ``SIGLAS_TIPO_UE_RECREIO``.
        """
        filtradas: list[dict[str, Any]] = []
        for unidade in unidades:
            sigla = str(unidade.get("siglaTipoEscola") or "").strip()
            if sigla in SIGLAS_TIPO_UE_RECREIO:
                filtradas.append(unidade)
        return filtradas

    def obter_dados_unidade(self, codigo_eol: str) -> dict[str, Any] | None:
        """Consulta dados detalhados da unidade pelo código EOL.

        Args:
            codigo_eol: Código EOL da escola.

        Returns:
            Payload de dados ou ``None`` quando a unidade não é encontrada.

        Raises:
            EscolasIntegracaoConfigError: Configuração ausente.
            EscolasIntegracaoIndisponivelError: Falha de comunicação ou HTTP 5xx.
        """
        self._garantir_configuracao()
        codigo = str(codigo_eol).strip()
        url = f"{self.base_url}/api/escolas/dados/{codigo}"
        resposta = self._requisicao("GET", url)

        if resposta.status_code == 404:
            return None
        if resposta.status_code >= 500 or not resposta.ok:
            raise EscolasIntegracaoIndisponivelError(
                f"Falha ao obter dados da unidade {codigo} "
                f"(HTTP {resposta.status_code})",
            )

        try:
            dados = resposta.json()
        except ValueError as exc:
            raise EscolasIntegracaoIndisponivelError(
                f"Resposta inválida nos dados da unidade {codigo}",
            ) from exc

        if not isinstance(dados, dict):
            raise EscolasIntegracaoIndisponivelError(
                f"Dados da unidade {codigo} em formato inesperado",
            )
        return dados

    def obter_nome_diretor(
        self,
        codigo_eol: str,
        codigo_cargo: int | None = None,
    ) -> str:
        """Consulta o nome do diretor da unidade pelo cargo informado.

        Args:
            codigo_eol: Código EOL da unidade.
            codigo_cargo: Código do cargo. Se ``None``, usa
                ``codigo_cargo_diretor_escola()`` (``.env`` ou padrão 3360 —
                Diretor de Escola no catálogo SME).

        Returns:
            Nome do primeiro servidor encontrado ou string vazia se ausente
            (HTTP 204/404 ou lista vazia).

        Raises:
            EscolasIntegracaoConfigError: Configuração ausente.
            EscolasIntegracaoIndisponivelError: Falha de comunicação ou HTTP 5xx.
        """
        self._garantir_configuracao()
        codigo = str(codigo_eol).strip()
        cargo = (
            codigo_cargo_diretor_escola()
            if codigo_cargo is None
            else codigo_cargo
        )
        url = (
            f"{self.base_url}/api/escolas/{codigo}/funcionarios/cargos/{cargo}"
        )
        resposta = self._requisicao("GET", url)

        if resposta.status_code in (204, 404):
            return ""
        if resposta.status_code >= 500 or not resposta.ok:
            raise EscolasIntegracaoIndisponivelError(
                f"Falha ao obter diretor da unidade {codigo} "
                f"(HTTP {resposta.status_code})",
            )

        if not resposta.content:
            return ""

        try:
            dados = resposta.json()
        except ValueError as exc:
            raise EscolasIntegracaoIndisponivelError(
                f"Resposta inválida no cargo da unidade {codigo}",
            ) from exc

        if not isinstance(dados, list) or not dados:
            return ""

        primeiro = dados[0]
        if not isinstance(primeiro, dict):
            return ""
        return str(primeiro.get("nomeServidor") or "").strip()

    def _montar_endereco(self, dados: dict[str, Any]) -> str:
        """Compõe endereço legível a partir dos campos de dados da unidade."""
        partes = [
            str(dados.get("tipoLogradouro") or "").strip(),
            str(dados.get("logradouro") or "").strip(),
        ]
        numero = str(dados.get("numero") or "").strip()
        bairro = str(dados.get("bairro") or "").strip()
        logradouro = " ".join(parte for parte in partes if parte)
        if numero:
            logradouro = f"{logradouro}, {numero}" if logradouro else numero
        if bairro:
            logradouro = f"{logradouro} - {bairro}" if logradouro else bairro
        return logradouro

    def _formatar_cep(self, cep: Any) -> str:
        """Normaliza CEP numérico ou textual para o padrão ``00000-000``."""
        digitos = "".join(ch for ch in str(cep or "") if ch.isdigit())
        if not digitos:
            return ""
        digitos = digitos.zfill(8)[-8:]
        return f"{digitos[:5]}-{digitos[5:]}"

    @staticmethod
    def _texto(valor: Any) -> str:
        """Converte valor em string já sem espaços nas bordas."""
        return str(valor or "").strip()

    @staticmethod
    def _escolher_campo(
        dados: dict[str, Any] | None,
        chave_dados: str,
        unidade: dict[str, Any],
        chave_unidade: str,
    ) -> str:
        """Prefere o campo detalhado; usa o básico de ``todas-unidades``."""
        if dados and dados.get(chave_dados):
            return EscolasIntegracaoService._texto(dados.get(chave_dados))
        return EscolasIntegracaoService._texto(unidade.get(chave_unidade))

    def _consultar_dados_unidade_seguro(
        self,
        codigo_eol: str,
    ) -> dict[str, Any] | None:
        """Consulta dados da unidade sem propagar falha pontual."""
        try:
            return self.obter_dados_unidade(codigo_eol)
        except EscolasIntegracaoIndisponivelError:
            return None

    def _consultar_diretor_seguro(self, codigo_eol: str) -> str:
        """Consulta o diretor sem propagar falha pontual."""
        try:
            return self.obter_nome_diretor(codigo_eol)
        except EscolasIntegracaoIndisponivelError:
            return ""

    def _payload_basico_unidade(self, unidade: dict[str, Any]) -> dict[str, Any]:
        """Monta payload mínimo a partir dos dados de ``todas-unidades``."""
        return {
            "codigoEol": self._texto(unidade.get("codigoEscola")),
            "nomeEscola": self._texto(unidade.get("nomeEscola")),
            "siglaTipoEscola": self._texto(unidade.get("siglaTipoEscola")),
            "nomeDre": self._texto(unidade.get("nomeDRE")),
            "siglaDre": self._texto(unidade.get("siglaDRE")),
            "codigoDre": self._texto(unidade.get("codigoDRE")),
            "email": "",
            "telefone": "",
            "cep": "",
            "endereco": "",
            "nomeDiretor": "",
            "gestao": "Direta",
        }

    def _enriquecer_unidade(self, unidade: dict[str, Any]) -> dict[str, Any]:
        """Agrega dados detalhados e nome do diretor a uma unidade filtrada.

        Falhas pontuais na API de dados/diretor não interrompem a sincronização:
        nesse caso, usa os dados básicos de ``todas-unidades``.
        """
        codigo_eol = self._texto(unidade.get("codigoEscola"))
        dados: dict[str, Any] | None = None
        nome_diretor = ""

        if codigo_eol:
            dados = self._consultar_dados_unidade_seguro(codigo_eol)
            nome_diretor = self._consultar_diretor_seguro(codigo_eol)

        return {
            "codigoEol": codigo_eol,
            "nomeEscola": self._escolher_campo(
                dados,
                "nome",
                unidade,
                "nomeEscola",
            ),
            "siglaTipoEscola": self._escolher_campo(
                dados,
                "siglaTipoEscola",
                unidade,
                "siglaTipoEscola",
            ),
            "nomeDre": self._escolher_campo(dados, "nomeDRE", unidade, "nomeDRE"),
            "siglaDre": self._escolher_campo(dados, "siglaDRE", unidade, "siglaDRE"),
            "codigoDre": self._escolher_campo(
                dados,
                "codigoDRE",
                unidade,
                "codigoDRE",
            ),
            "email": self._texto((dados or {}).get("email")),
            "telefone": self._texto((dados or {}).get("telefone")),
            "cep": self._formatar_cep((dados or {}).get("cep")) if dados else "",
            "endereco": self._montar_endereco(dados) if dados else "",
            "nomeDiretor": nome_diretor,
            "gestao": "Direta",
        }

    def enriquecer_unidades(
        self,
        unidades: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Enriquece uma lista de unidades com dados e diretor, em paralelo.

        Args:
            unidades: Unidades no formato de ``todas-unidades``.

        Returns:
            Lista enriquecida ordenada por nome da escola.
        """
        if not unidades:
            return []

        enriquecidas: list[dict[str, Any]] = []
        workers = min(self.max_workers, len(unidades))
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futuros = {
                executor.submit(self._enriquecer_unidade, unidade): unidade
                for unidade in unidades
            }
            for futuro in as_completed(futuros):
                unidade_origem = futuros[futuro]
                try:
                    enriquecidas.append(futuro.result())
                except Exception:
                    # Garante persistência mínima mesmo com falha inesperada.
                    enriquecidas.append(self._payload_basico_unidade(unidade_origem))

        enriquecidas.sort(
            key=lambda item: (
                str(item.get("nomeEscola") or "").casefold(),
                str(item.get("codigoEol") or ""),
            ),
        )
        return enriquecidas

    def listar_unidades_diretas_recreio(
        self,
        *,
        limite: int | None = None,
    ) -> list[dict[str, Any]]:
        """Lista unidades diretas elegíveis ao Recreio, com dados e diretor.

        Fluxo:
            1. ``GET /api/escolas/todas-unidades``
            2. Filtro pelas siglas de tipo de UE do programa
            3. Para cada unidade: dados + diretor
               (``codigo_cargo_diretor_escola()``), em paralelo

        Args:
            limite: Quando informado, limita a quantidade de unidades
                enriquecidas (útil para testes).

        Returns:
            Lista de unidades enriquecidas ordenada por nome da escola.
        """
        unidades = self.filtrar_unidades_recreio(self.listar_todas_unidades())
        if limite is not None:
            unidades = unidades[: max(0, limite)]
        return self.enriquecer_unidades(unidades)
