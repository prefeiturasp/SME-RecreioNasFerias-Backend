import os

import pytest

os.environ.setdefault("DJANGO_SECRET_KEY", "test-only-secret-key")


@pytest.fixture(autouse=True)
def habilitar_crud_usuarios_nos_testes(settings):
    """Mantém rotas de CRUD de usuários ativas durante a suíte de testes."""
    settings.USUARIOS_CRUD_ENABLED = True
