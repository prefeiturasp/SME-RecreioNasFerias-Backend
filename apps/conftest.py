"""Fixtures compartilhadas dos testes da aplicação."""

from datetime import date, timedelta

import pytest
from django.contrib.auth.models import Group, Permission
from rest_framework.test import APIClient

from apps.factories import (
    DefinicaoPoloFactory,
    EdicaoFactory,
    InscricaoFactory,
    PoloFactory,
    UsuarioFactory,
)


@pytest.fixture
def perfis_rbac():
    """Lista os perfis institucionais usados nos testes da matriz RBAC."""
    return (
        "ADMINISTRADOR_COCEU",
        "GESTOR_DICEU",
        "GESTOR_CODAE",
        "GESTOR_ASCOM",
        "GESTOR_COGED",
        "GESTOR_POLO",
        "USUARIO_UE",
    )


@pytest.fixture
def criar_usuario_rbac():
    """Cria usuário de teste com grupos e permissões individuais opcionais."""
    def criar(*, perfis=(), permissoes=()):
        usuario = UsuarioFactory.create()
        for perfil in perfis:
            grupo = Group.objects.get(name=perfil)
            usuario.groups.add(grupo)

        if permissoes:
            permissoes_encontradas = Permission.objects.filter(
                content_type__app_label="core",
                codename__in=permissoes,
            )
            codenames_encontrados = set(
                permissoes_encontradas.values_list("codename", flat=True)
            )
            assert codenames_encontrados == set(permissoes)
            usuario.user_permissions.add(*permissoes_encontradas)
        return usuario

    return criar

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
    """Autentica o cliente como Administrador COCEU, sem executar CoreSSO."""
    perfil_admin, _ = Group.objects.get_or_create(
        name="ADMINISTRADOR_COCEU"
    )
    usuario.groups.add(perfil_admin)
    api_client.force_authenticate(user=usuario)
    return api_client
