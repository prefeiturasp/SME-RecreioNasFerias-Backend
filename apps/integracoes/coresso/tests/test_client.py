"""Testes unitarios do client CoreSSO."""

from __future__ import annotations

from typing import Any

import pytest
import requests

from apps.integracoes.coresso.client import CoressoClient
from apps.integracoes.coresso.exceptions import (
    CoressoAutenticacaoError,
    CoressoConfigError,
    CoressoContratoError,
    CoressoIndisponivelError,
)

TEST_RF = "0000001"
TEST_AUTH_INPUT = "credencial-teste"


class FakeResponse:
    """Response minima para testes do client."""

    def __init__(
        self,
        *,
        status_code: int,
        data: object | None = None,
        text: str = "",
    ) -> None:
        """Inicializa a resposta fake com status, payload e texto bruto."""
        self.status_code = status_code
        self._data = data
        self.text = text

    def json(self) -> object:
        """Retorna o payload fake ou simula JSON invalido."""
        if isinstance(self._data, Exception):
            raise self._data
        return self._data


class FakeSession:
    """Sessao HTTP fake para inspeção do request emitido."""

    def __init__(self, response: FakeResponse | Exception) -> None:
        """Inicializa a sessão fake com a resposta a ser devolvida."""
        self.response = response
        self.request_args: dict[str, object] | None = None

    def request(self, method: str, url: str, **kwargs: object) -> FakeResponse:
        """Registra a chamada e retorna a resposta programada."""
        self.request_args = {
            "method": method,
            "url": url,
            **kwargs,
        }
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


def test_client_autenticar_envia_payload_esperado(settings: Any) -> None:
    """Garante o request HTTP esperado do endpoint unificado."""
    settings.AUTH_API_BASE_URL = "https://auth.exemplo.gov.br"
    settings.AUTH_API_EOL_KEY = "api-key"
    settings.AUTH_API_CONNECT_TIMEOUT_SECONDS = 5
    settings.AUTH_API_AUTH_TIMEOUT_SECONDS = 10

    response = FakeResponse(status_code=200, data={"codigoRf": TEST_RF})
    session = FakeSession(response)

    dados = CoressoClient(session=session).autenticar(TEST_RF, TEST_AUTH_INPUT)

    assert dados == {"codigoRf": TEST_RF}
    assert session.request_args == {
        "method": "POST",
        "url": "https://auth.exemplo.gov.br/api/v1/autenticacao/externa",
        "json": {
            "usuario": TEST_RF,
            "senha": TEST_AUTH_INPUT,
            "codigoSistema": 1009,
        },
        "headers": {"x-api-eol-key": "api-key"},
        "timeout": (5, 10),
    }


def test_client_falha_sem_configuracao(settings: Any) -> None:
    """Impede autenticação sem URL e chave configuradas."""
    settings.AUTH_API_BASE_URL = ""
    settings.AUTH_API_EOL_KEY = ""

    with pytest.raises(CoressoConfigError):
        CoressoClient(
            session=FakeSession(FakeResponse(status_code=200, data={}))
        ).autenticar(TEST_RF, TEST_AUTH_INPUT)


def test_client_mapeia_401_para_erro_de_autenticacao(settings: Any) -> None:
    """Converte erro funcional do provedor em exceção tipada."""
    settings.AUTH_API_BASE_URL = "https://auth.exemplo.gov.br"
    settings.AUTH_API_EOL_KEY = "api-key"

    response = FakeResponse(
        status_code=401,
        data={"detail": "Credenciais invalidas."},
    )

    with pytest.raises(
        CoressoAutenticacaoError, match="Credenciais invalidas"
    ):
        CoressoClient(session=FakeSession(response)).autenticar(
            TEST_RF, TEST_AUTH_INPUT
        )


def test_client_mapeia_erro_de_rede_para_indisponibilidade(
    settings: Any,
) -> None:
    """Converte erros de rede em indisponibilidade do CoreSSO."""
    settings.AUTH_API_BASE_URL = "https://auth.exemplo.gov.br"
    settings.AUTH_API_EOL_KEY = "api-key"

    with pytest.raises(CoressoIndisponivelError):
        CoressoClient(
            session=FakeSession(requests.RequestException("falha de rede"))
        ).autenticar(TEST_RF, TEST_AUTH_INPUT)


def test_client_rejeita_json_invalido(settings: Any) -> None:
    """Rejeita resposta 200 sem JSON valido."""
    settings.AUTH_API_BASE_URL = "https://auth.exemplo.gov.br"
    settings.AUTH_API_EOL_KEY = "api-key"

    response = FakeResponse(status_code=200, data=ValueError("json invalido"))

    with pytest.raises(CoressoContratoError):
        CoressoClient(session=FakeSession(response)).autenticar(
            TEST_RF, TEST_AUTH_INPUT
        )
