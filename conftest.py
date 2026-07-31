"""Configuração global do pytest para o projeto Recreio nas Férias."""

from __future__ import annotations

import os

import pytest


def pytest_configure(config: pytest.Config) -> None:
    """Registra o marker `postgres` usado por `@pytest.mark.postgres`."""
    config.addinivalue_line(
        "markers",
        "postgres: indica que o teste deve rodar em Postgres ao invés de "
        "SQLite em memória. Por padrão esses testes são skipados; para "
        "executá-los rode com PYTEST_USE_POSTGRES=1.",
    )


def pytest_collection_modifyitems(
    config: pytest.Config,
    items: list[pytest.Item],
) -> None:
    """Pula testes marcados com `@pytest.mark.postgres`.

    Evita que um teste marcado para Postgres caia silenciosamente em SQLite
    em memória. Para rodá-lo, execute o pytest com PYTEST_USE_POSTGRES=1.
    """
    if os.getenv("PYTEST_USE_POSTGRES", "0") == "1":
        return
    skip_postgres = pytest.mark.skip(
        reason="Teste marcado com @pytest.mark.postgres; "
        "rode com PYTEST_USE_POSTGRES=1 para executá-lo.",
    )
    for item in items:
        if "postgres" in item.keywords:
            item.add_marker(skip_postgres)
