"""Client HTTP da SME Integração/EOL.

Encapsula as chamadas de rede dos três endpoints de escolas usados para
alimentar a sincronização de polos de gestão direta:

- ``GET /api/tiposEscolas``
- ``GET /api/DREs``
- ``GET /api/escolas/todas-unidades``
- ``GET /api/escolas/dados/{eol}``
- ``GET /api/escolas/{eol}/funcionarios/cargos/{codigo}``
"""

from __future__ import annotations

from typing import Any, Protocol, cast

import requests
from django.conf import settings

from apps.integracoes.eol.exceptions import (
    EolConfigError,
    EolContratoError,
    EolIndisponivelError,
)


class RequestSession(Protocol):
    """Protocolo mínimo da sessão HTTP usada pelo client."""

    def request(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> ResponseLike:
        """Executa uma requisição HTTP e retorna um response compatível."""


class ResponseLike(Protocol):
    """Protocolo mínimo da resposta HTTP usada pelo client."""

    status_code: int
    text: str
    content: bytes

    def json(self) -> object:
        """Retorna o payload JSON bruto da resposta."""


class EolClient:
    """Encapsula chamadas HTTP da SME Integração/EOL."""

    def __init__(self, session: RequestSession | None = None) -> None:
        """Inicializa o client com uma sessão HTTP reutilizável."""
        self.session: RequestSession = session or cast(
            RequestSession,
            requests.Session(),
        )

    def listar_tipos_escola(self) -> list[dict[str, Any]]:
        """Consulta o catálogo bruto de tipos de escola.

        Returns:
            Lista bruta de tipos de escola retornada pela integração.

        Raises:
            EolConfigError: Quando a configuração obrigatória estiver ausente.
            EolIndisponivelError: Quando houver erro de rede ou HTTP 4xx/5xx.
            EolContratoError: Quando a resposta não seguir o contrato esperado.
        """
        self._validar_configuracao()

        url = f"{settings.AUTH_API_BASE_URL}/api/escolas/tiposEscolas"
        response = self._requisicao("GET", url)
        self._garantir_sucesso_http(response, "listar tipos de escola")

        dados = self._parse_json(response)
        if not isinstance(dados, list):
            raise EolContratoError(
                "Resposta de tipos de escola em formato inesperado."
            )
        return [item for item in dados if isinstance(item, dict)]

    def listar_dres(self) -> list[dict[str, Any]]:
        """Consulta o catálogo bruto de Diretorias Regionais de Educação.

        Returns:
            Lista bruta de DREs retornada pela integração.

        Raises:
            EolConfigError: Quando a configuração obrigatória estiver ausente.
            EolIndisponivelError: Quando houver erro de rede ou HTTP 4xx/5xx.
            EolContratoError: Quando a resposta não seguir o contrato esperado.
        """
        self._validar_configuracao()

        url = f"{settings.AUTH_API_BASE_URL}/api/DREs"
        response = self._requisicao("GET", url)
        self._garantir_sucesso_http(response, "listar DREs")

        dados = self._parse_json(response)
        if not isinstance(dados, list):
            raise EolContratoError(
                "Resposta de DREs em formato inesperado."
            )
        return [item for item in dados if isinstance(item, dict)]

    def listar_todas_unidades(self) -> list[dict[str, Any]]:
        """Consulta o catálogo bruto de unidades escolares.

        Returns:
            Lista bruta de unidades retornada pela integração externa.

        Raises:
            EolConfigError: Quando a configuração obrigatória estiver ausente.
            EolIndisponivelError: Quando houver erro de rede ou HTTP 4xx/5xx.
            EolContratoError: Quando a resposta não seguir o contrato esperado.
        """
        self._validar_configuracao()

        url = f"{settings.AUTH_API_BASE_URL}/api/escolas/todas-unidades"
        response = self._requisicao("GET", url)
        self._garantir_sucesso_http(response, "listar unidades")

        dados = self._parse_json(response)
        if not isinstance(dados, list):
            raise EolContratoError(
                "Resposta de unidades em formato inesperado."
            )
        return [item for item in dados if isinstance(item, dict)]

    def obter_dados_unidade(self, codigo_eol: str) -> dict[str, Any] | None:
        """Consulta os dados detalhados de uma unidade pelo código EOL.

        Args:
            codigo_eol: Código EOL da escola.

        Returns:
            Payload bruto de dados ou ``None`` quando a unidade não é
            encontrada (HTTP 404).

        Raises:
            EolConfigError: Quando a configuração obrigatória estiver ausente.
            EolIndisponivelError: Quando houver erro de rede ou HTTP 4xx/5xx.
            EolContratoError: Quando a resposta não seguir o contrato esperado.
        """
        self._validar_configuracao()

        codigo = str(codigo_eol).strip()
        url = f"{settings.AUTH_API_BASE_URL}/api/escolas/dados/{codigo}"
        response = self._requisicao("GET", url)

        if response.status_code == 404:
            return None
        self._garantir_sucesso_http(
            response, f"obter dados da unidade {codigo}"
        )

        dados = self._parse_json(response)
        if not isinstance(dados, dict):
            raise EolContratoError(
                f"Dados da unidade {codigo} em formato inesperado."
            )
        return dados

    def obter_funcionarios_por_cargo(
        self,
        codigo_eol: str,
        codigo_cargo: int,
    ) -> list[dict[str, Any]]:
        """Consulta os funcionários da unidade por código de cargo.

        Args:
            codigo_eol: Código EOL da escola.
            codigo_cargo: Código do cargo consultado (ex.: diretor de escola).

        Returns:
            Lista bruta de funcionários ou lista vazia quando a unidade não
            possuir funcionários no cargo (HTTP 204/404 ou corpo vazio).

        Raises:
            EolConfigError: Quando a configuração obrigatória estiver ausente.
            EolIndisponivelError: Quando houver erro de rede ou HTTP 4xx/5xx.
            EolContratoError: Quando a resposta não seguir o contrato esperado.
        """
        self._validar_configuracao()

        codigo = str(codigo_eol).strip()
        url = (
            f"{settings.AUTH_API_BASE_URL}/api/escolas/{codigo}/"
            f"funcionarios/cargos/{codigo_cargo}"
        )
        response = self._requisicao("GET", url)

        if response.status_code in (204, 404):
            return []
        self._garantir_sucesso_http(
            response, f"obter diretor da unidade {codigo}"
        )

        if not response.content:
            return []

        dados = self._parse_json(response)
        if not isinstance(dados, list):
            raise EolContratoError(
                f"Cargo da unidade {codigo} em formato inesperado."
            )
        return [item for item in dados if isinstance(item, dict)]

    def _requisicao(self, metodo: str, url: str) -> ResponseLike:
        """Executa a requisição HTTP tratando falhas de rede."""
        try:
            return self.session.request(
                metodo,
                url,
                headers=self._cabecalhos(),
                timeout=self._timeout(),
            )
        except requests.RequestException as exc:
            raise EolIndisponivelError() from exc

    def _garantir_sucesso_http(
        self,
        response: ResponseLike,
        contexto: str,
    ) -> None:
        """Levanta erro de indisponibilidade quando o status não é 2xx."""
        if response.status_code < 400:
            return
        raise EolIndisponivelError(
            self._extrair_mensagem_erro(response, contexto),
            status_code=response.status_code,
        )

    @staticmethod
    def _parse_json(response: ResponseLike) -> object:
        """Extrai o JSON da resposta ou levanta erro de contrato."""
        try:
            return response.json()
        except ValueError as exc:
            raise EolContratoError() from exc

    @staticmethod
    def _cabecalhos() -> dict[str, str]:
        """Monta os headers obrigatórios da SME Integração/EOL."""
        return {"x-api-eol-key": settings.AUTH_API_EOL_KEY}

    @staticmethod
    def _timeout() -> tuple[int, int]:
        """Retorna o timeout de conexão e leitura da integração."""
        return (
            settings.AUTH_API_CONNECT_TIMEOUT_SECONDS,
            settings.AUTH_API_TIMEOUT_SECONDS,
        )

    @staticmethod
    def _validar_configuracao() -> None:
        """Valida a configuração mínima para consultar a SME Integração."""
        if not settings.AUTH_API_BASE_URL:
            raise EolConfigError("AUTH_API_BASE_URL nao configurada.")
        if not settings.AUTH_API_EOL_KEY:
            raise EolConfigError("AUTH_API_EOL_KEY nao configurada.")

    @staticmethod
    def _extrair_mensagem_erro(
        response: ResponseLike,
        contexto: str,
    ) -> str:
        """Extrai uma mensagem legível de erro da resposta HTTP."""
        try:
            dados = response.json()
        except ValueError:
            texto = response.text.strip()
            return texto or f"Falha ao {contexto}."

        if isinstance(dados, dict):
            for chave in (
                "mensagem",
                "message",
                "detail",
                "erro",
                "error",
                "title",
            ):
                valor = dados.get(chave)
                if isinstance(valor, str) and valor.strip():
                    return valor.strip()

            for valor in dados.values():
                if isinstance(valor, str) and valor.strip():
                    return valor.strip()

        return f"Falha ao {contexto}."
