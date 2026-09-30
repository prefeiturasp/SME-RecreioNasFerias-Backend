"""Fixtures compartilhadas dos testes da aplicação."""

import pytest
from datetime import date, timedelta
from rest_framework.test import APIClient

from apps.factories import (
    DefinicaoPoloFactory,
    EdicaoFactory,
    PoloFactory,
    UsuarioFactory,
    InscricaoFactory,
)

@pytest.fixture
def inscricao_factory():
    """Disponibiliza a factory local de inscrições."""
    return InscricaoFactory


@pytest.fixture
def inscricao_completa_factory(
    polo_factory,
    edicao_factory,
    definicao_polo_factory,
    inscricao_factory,
):
    """Cria uma inscrição completa vinculada a polo oficialmente definido."""
    contador = [0]

    def criar(**kwargs):
        polo = kwargs.pop("polo", None) or polo_factory()
        edicao = kwargs.pop("edicao", None)
        if edicao is None:
            inicio = date(2099, 1, 1) + timedelta(days=contador[0] * 40)
            contador[0] += 1
            edicao = edicao_factory(
                data_inicio=inicio,
                data_fim=inicio + timedelta(days=20),
                inscricoes_inicio=inicio - timedelta(days=10),
                inscricoes_fim=inicio + timedelta(days=20),
            )
        definicao_polo_factory(
            polo=polo,
            edicao=edicao,
            tipo="oficial",
        )
        dados = {
            "polo": polo,
            "edicao": edicao,
            "dre_codigo_eol": polo.dre_codigo_eol,
            "dre_nome": polo.dre_nome,
        }
        dados.update(kwargs)
        return inscricao_factory(**dados)

    return criar

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
