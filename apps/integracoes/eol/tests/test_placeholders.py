"""Cobertura dos placeholders da integracao `eol`."""

import pytest

from apps.integracoes.eol.adapter import EolAdapter
from apps.integracoes.eol.client import EolClient
from apps.integracoes.eol.exceptions import (
    EolIndisponivelError,
    EolRespostaInvalidaError,
)


def test_eol_placeholders_lancam_not_implemented() -> None:
    """Garante que adapter e client continuam em modo stub."""
    adapter = EolAdapter()
    client = EolClient()

    with pytest.raises(NotImplementedError):
        adapter.obter_unidades()

    with pytest.raises(NotImplementedError):
        adapter.obter_cargos()

    with pytest.raises(NotImplementedError):
        client.obter_unidades()

    with pytest.raises(NotImplementedError):
        client.obter_cargos()


def test_eol_exceptions_sao_instanciaveis() -> None:
    """Garante a existencia das excecoes publicas da integracao."""
    assert isinstance(EolIndisponivelError("erro"), Exception)
    assert isinstance(EolRespostaInvalidaError("erro"), Exception)
