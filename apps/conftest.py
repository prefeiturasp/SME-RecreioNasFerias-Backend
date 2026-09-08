"""Fixtures compartilhadas dos testes da aplicação."""

import pytest
from rest_framework.test import APIClient

from apps.factories import (
    DefinicaoPoloFactory,
    EdicaoFactory,
    PoloFactory,
    UsuarioFactory,
)


@pytest.fixture
def edicao_factory():
    """Disponibiliza a factory de edições para os testes."""
    return EdicaoFactory


@pytest.fixture
def polo_factory():
    """Disponibiliza a factory de polos para os testes."""
    return PoloFactory


@pytest.fixture
def definicao_polo_factory():
    """Disponibiliza a factory de definições de polos."""
    return DefinicaoPoloFactory


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
