"""Smoke tests do client EOL."""

from apps.integracoes.eol.client import EolClient


def test_import_client() -> None:
    """Garante que o client pode ser importado na estrutura atual."""
    assert EolClient is not None
