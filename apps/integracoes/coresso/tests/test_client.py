"""Smoke tests do client CoreSSO."""

from apps.integracoes.coresso.client import CoressoClient


def test_import_client() -> None:
    """Garante que o client pode ser importado na estrutura atual."""
    assert CoressoClient is not None
