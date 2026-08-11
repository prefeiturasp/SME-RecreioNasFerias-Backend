"""Cobertura dos placeholders da integracao `coresso`."""

import pytest

from apps.integracoes.coresso.adapter import CoressoAdapter
from apps.integracoes.coresso.client import CoressoClient
from apps.integracoes.coresso.exceptions import (
    CoressoAutenticacaoError,
    CoressoIndisponivelError,
)


def test_coresso_placeholders_lancam_not_implemented() -> None:
    """Garante que adapter e client continuam em modo stub."""
    adapter = CoressoAdapter()
    client = CoressoClient()

    with pytest.raises(NotImplementedError):
        adapter.autenticar("123", "senha")

    with pytest.raises(NotImplementedError):
        adapter.obter_dados_usuario("token")

    with pytest.raises(NotImplementedError):
        client.autenticar("123", "senha")

    with pytest.raises(NotImplementedError):
        client.obter_dados_usuario("token")


def test_coresso_exceptions_sao_instanciaveis() -> None:
    """Garante a existencia das excecoes publicas da integracao."""
    assert isinstance(CoressoIndisponivelError("erro"), Exception)
    assert isinstance(CoressoAutenticacaoError("erro"), Exception)
