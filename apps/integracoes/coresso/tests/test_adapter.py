"""Smoke tests do adaptador CoreSSO."""

from apps.integracoes.coresso.adapter import CoressoAdapter


def test_import_adapter() -> None:
    """Garante que o adaptador pode ser importado na estrutura atual."""
    assert CoressoAdapter is not None
