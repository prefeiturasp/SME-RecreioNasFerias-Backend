"""Smoke tests do adaptador EOL."""

from apps.integracoes.eol.adapter import EolAdapter


def test_import_adapter() -> None:
    """Garante que o adaptador pode ser importado na estrutura atual."""
    assert EolAdapter is not None
