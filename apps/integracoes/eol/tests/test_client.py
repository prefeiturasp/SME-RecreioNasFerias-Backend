"""Testes unitarios do client EOL."""

from __future__ import annotations

from typing import Any

import pytest
import requests

from apps.integracoes.eol.client import EolClient
from apps.integracoes.eol.exceptions import (
    EolConfigError,
    EolContratoError,
    EolIndisponivelError,
)

TEST_EOL = "094633"
TEST_CARGO = 3360


class FakeResponse:
    """Response minima para testes do client."""

    def __init__(
        self,
        *,
        status_code: int,
        data: object | None = None,
        text: str = "",
        content: bytes = b"",
    ) -> None:
        """Inicializa a resposta fake com status, payload e corpo bruto."""
        self.status_code = status_code
        self._data = data
        self.text = text
        self.content = content

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


def _configurar_ambiente(settings: Any) -> None:
    """Define a configuração mínima da integração para os testes."""
    settings.AUTH_API_BASE_URL = "https://eol.exemplo.gov.br"
    settings.AUTH_API_EOL_KEY = "api-key"
    settings.AUTH_API_CONNECT_TIMEOUT_SECONDS = 5
    settings.AUTH_API_TIMEOUT_SECONDS = 60


def test_listar_todas_unidades_envia_requisicao_esperada(
    settings: Any,
) -> None:
    """Garante o request HTTP esperado do catalogo de unidades."""
    _configurar_ambiente(settings)

    response = FakeResponse(
        status_code=200,
        data=[{"codigoEscola": TEST_EOL, "nomeEscola": "EMEF Teste"}],
    )
    session = FakeSession(response)

    dados = EolClient(session=session).listar_todas_unidades()

    assert dados == [{"codigoEscola": TEST_EOL, "nomeEscola": "EMEF Teste"}]
    assert session.request_args == {
        "method": "GET",
        "url": "https://eol.exemplo.gov.br/api/escolas/todas-unidades",
        "headers": {"x-api-eol-key": "api-key"},
        "timeout": (5, 60),
    }


def test_listar_todas_unidades_ignora_itens_nao_dicionarios(
    settings: Any,
) -> None:
    """Filtra itens invalidos do catalogo bruto de unidades."""
    _configurar_ambiente(settings)

    response = FakeResponse(
        status_code=200,
        data=[
            {"codigoEscola": TEST_EOL},
            "item-invalido",
            {"codigoEscola": "121000"},
        ],
    )

    dados = EolClient(session=FakeSession(response)).listar_todas_unidades()

    assert dados == [{"codigoEscola": TEST_EOL}, {"codigoEscola": "121000"}]


def test_obter_dados_unidade_retorna_payload_bruto(settings: Any) -> None:
    """Devolve o payload bruto de dados detalhados da unidade."""
    _configurar_ambiente(settings)

    response = FakeResponse(status_code=200, data={"nome": "EMEF Teste"})
    session = FakeSession(response)

    dados = EolClient(session=session).obter_dados_unidade(TEST_EOL)

    assert dados == {"nome": "EMEF Teste"}
    assert session.request_args == {
        "method": "GET",
        "url": f"https://eol.exemplo.gov.br/api/escolas/dados/{TEST_EOL}",
        "headers": {"x-api-eol-key": "api-key"},
        "timeout": (5, 60),
    }


def test_obter_dados_unidade_retorna_none_para_404(settings: Any) -> None:
    """Trata unidade nao encontrada como ausencia de dados."""
    _configurar_ambiente(settings)

    response = FakeResponse(status_code=404, data={})

    dados = EolClient(session=FakeSession(response)).obter_dados_unidade(
        TEST_EOL
    )

    assert dados is None


def test_obter_funcionarios_por_cargo_retorna_lista(settings: Any) -> None:
    """Devolve a lista bruta de funcionarios no cargo informado."""
    _configurar_ambiente(settings)

    response = FakeResponse(
        status_code=200,
        data=[{"nomeServidor": "Diretor Teste"}],
        content=b"[{}]",
    )
    session = FakeSession(response)

    funcionarios = EolClient(session=session).obter_funcionarios_por_cargo(
        TEST_EOL, TEST_CARGO
    )

    assert funcionarios == [{"nomeServidor": "Diretor Teste"}]
    assert session.request_args == {
        "method": "GET",
        "url": (
            f"https://eol.exemplo.gov.br/api/escolas/{TEST_EOL}/"
            f"funcionarios/cargos/{TEST_CARGO}"
        ),
        "headers": {"x-api-eol-key": "api-key"},
        "timeout": (5, 60),
    }


def test_obter_funcionarios_por_cargo_retorna_vazio_para_404(
    settings: Any,
) -> None:
    """Trata unidade sem funcionarios no cargo como lista vazia."""
    _configurar_ambiente(settings)

    response = FakeResponse(status_code=404, data={})

    funcionarios = EolClient(
        session=FakeSession(response)
    ).obter_funcionarios_por_cargo(TEST_EOL, TEST_CARGO)

    assert funcionarios == []


def test_client_falha_sem_configuracao(settings: Any) -> None:
    """Impede a consulta sem URL e chave configuradas."""
    settings.AUTH_API_BASE_URL = ""
    settings.AUTH_API_EOL_KEY = ""

    with pytest.raises(EolConfigError):
        EolClient(
            session=FakeSession(FakeResponse(status_code=200, data=[]))
        ).listar_todas_unidades()


def test_client_mapeia_erro_de_rede_para_indisponibilidade(
    settings: Any,
) -> None:
    """Converte erros de rede em indisponibilidade da integração."""
    _configurar_ambiente(settings)

    with pytest.raises(EolIndisponivelError):
        EolClient(
            session=FakeSession(requests.RequestException("falha de rede"))
        ).listar_todas_unidades()


def test_client_mapeia_5xx_para_indisponibilidade(settings: Any) -> None:
    """Converte erro HTTP 5xx em indisponibilidade da integração."""
    _configurar_ambiente(settings)

    response = FakeResponse(status_code=503, data={"detail": "indisponivel"})

    with pytest.raises(EolIndisponivelError, match="indisponivel"):
        EolClient(session=FakeSession(response)).listar_todas_unidades()


def test_client_rejeita_json_invalido(settings: Any) -> None:
    """Rejeita resposta 200 sem JSON valido."""
    _configurar_ambiente(settings)

    response = FakeResponse(status_code=200, data=ValueError("json invalido"))

    with pytest.raises(EolContratoError):
        EolClient(session=FakeSession(response)).listar_todas_unidades()


def test_client_rejeita_lista_inesperada_em_unidades(settings: Any) -> None:
    """Rejeita resposta de unidades que nao seja uma lista."""
    _configurar_ambiente(settings)

    response = FakeResponse(status_code=200, data={"unidades": []})

    with pytest.raises(EolContratoError):
        EolClient(session=FakeSession(response)).listar_todas_unidades()


def test_client_rejeita_dados_inesperados_na_unidade(settings: Any) -> None:
    """Rejeita resposta de dados da unidade que nao seja um dicionario."""
    _configurar_ambiente(settings)

    response = FakeResponse(status_code=200, data=[{"nome": "EMEF"}])

    with pytest.raises(EolContratoError):
        EolClient(session=FakeSession(response)).obter_dados_unidade(TEST_EOL)
