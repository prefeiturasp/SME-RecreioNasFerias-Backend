"""Client HTTP do CoreSSO.

Encapsula as chamadas de rede necessárias para login institucional e
consulta de perfil do usuário autenticado.
"""

from __future__ import annotations

from typing import Any, Protocol, cast

import requests
from django.conf import settings

from apps.integracoes.coresso.exceptions import (
    CoressoAutenticacaoError,
    CoressoConfigError,
    CoressoContratoError,
    CoressoIndisponivelError,
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

    def json(self) -> object:
        """Retorna o payload JSON bruto da resposta."""


class CoressoClient:
    """Encapsula chamadas HTTP do CoreSSO."""

    def __init__(self, session: RequestSession | None = None) -> None:
        """Inicializa o client com uma sessao HTTP reutilizavel."""
        self.session: RequestSession = session or cast(
            RequestSession,
            requests.Session(),
        )

    def autenticar(self, rf: str, senha: str) -> dict[str, Any]:
        """Executa a chamada HTTP do endpoint unificado de autenticacao.

        Args:
            rf: Registro funcional enviado pelo usuário.
            senha: Senha institucional enviada pelo usuário.

        Returns:
            Resposta bruta da autenticação institucional.

        Raises:
            CoressoConfigError: Quando a configuração obrigatoria estiver
                ausente.
            CoressoAutenticacaoError: Quando o provedor rejeitar as
                credenciais.
            CoressoIndisponivelError: Quando houver erro de rede ou HTTP 5xx.
            CoressoContratoError: Quando a resposta nao seguir o contrato
                esperado.
        """
        self._validar_configuracao()

        url = f"{settings.AUTH_API_BASE_URL}/api/v1/autenticacao/externa"
        payload = {
            "usuario": rf,
            "senha": senha,
            "codigoSistema": settings.AUTH_CODIGO_SISTEMA,
        }

        try:
            response = self.session.request(
                "POST",
                url,
                json=cast(Any, payload),
                headers=self._cabecalhos(),
                timeout=self._timeout(),
            )
        except requests.RequestException as exc:
            raise CoressoIndisponivelError() from exc

        if response.status_code >= 500:
            raise CoressoIndisponivelError(
                self._extrair_mensagem_erro(response),
                status_code=response.status_code,
            )

        if response.status_code >= 400:
            raise CoressoAutenticacaoError(
                self._extrair_mensagem_erro(response),
                status_code=response.status_code,
            )

        try:
            dados = response.json()
        except ValueError as exc:
            raise CoressoContratoError() from exc

        if not isinstance(dados, dict):
            raise CoressoContratoError()

        return dados

    @staticmethod
    def _cabecalhos() -> dict[str, str]:
        """Monta os headers obrigatorios do CoreSSO."""
        return {"x-api-eol-key": settings.AUTH_API_EOL_KEY}

    @staticmethod
    def _timeout() -> tuple[int, int]:
        """Retorna o timeout de conexao e leitura da integracao."""
        return (
            settings.AUTH_API_CONNECT_TIMEOUT_SECONDS,
            settings.AUTH_API_AUTH_TIMEOUT_SECONDS,
        )

    @staticmethod
    def _validar_configuracao() -> None:
        """Valida a configuração mínima para autenticar no CoreSSO."""
        if not settings.AUTH_API_BASE_URL:
            raise CoressoConfigError("AUTH_API_BASE_URL nao configurada.")
        if not settings.AUTH_API_EOL_KEY:
            raise CoressoConfigError("AUTH_API_EOL_KEY nao configurada.")

    @staticmethod
    def _extrair_mensagem_erro(response: ResponseLike) -> str:
        """Extrai uma mensagem legivel de erro da resposta HTTP."""
        try:
            dados = response.json()
        except ValueError:
            texto = response.text.strip()
            return texto or "Falha ao autenticar no CoreSSO."

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
                if isinstance(valor, list) and valor:
                    primeiro_item = valor[0]
                    if (
                        isinstance(primeiro_item, str)
                        and primeiro_item.strip()
                    ):
                        return primeiro_item.strip()

        return "Falha ao autenticar no CoreSSO."
