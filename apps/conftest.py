"""Fixtures compartilhadas dos testes de edições."""

import pytest
from rest_framework.test import APIClient

from apps.factories import EdicaoFactory, UsuarioFactory


@pytest.fixture
def edicao_factory():
    """Disponibiliza a factory de edições para os testes."""
    return EdicaoFactory


@pytest.fixture
def usuario(db):
    """Cria um usuário local para autenticação de testes."""
    return UsuarioFactory.create()


@pytest.fixture
def api_client() -> APIClient:
    """Cria um cliente DRF sem qualquer chamada externa."""
    return APIClient()


@pytest.fixture
def cliente_autenticado(api_client: APIClient, usuario) -> APIClient:
    """Autentica o cliente localmente, sem executar o fluxo CoreSSO."""
    api_client.force_authenticate(user=usuario)
    return api_client
