"""Testes do endpoint de consulta dos perfis RBAC."""

import pytest
from django.contrib.auth.models import Group, Permission
from rest_framework import status
from rest_framework.test import APIClient

from apps.core.models import Usuario
from apps.core.permission_catalog import PERFIS

pytestmark = pytest.mark.django_db


@pytest.fixture
def cliente_com_permissao_de_consulta(
    api_client: APIClient,
    usuario: Usuario,
) -> APIClient:
    """Autentica usuário com a permissão individual de consultar perfis."""
    permissao = Permission.objects.get(
        content_type__app_label="core",
        codename="visualizar_usuarios",
    )
    usuario.user_permissions.add(permissao)
    api_client.force_authenticate(user=usuario)
    return api_client


def criar_grupos_do_catalogo() -> dict[str, Group]:
    """Garante os grupos declarados no catálogo de perfis."""
    grupos = {}
    for perfil in PERFIS:
        codigo = str(perfil["codigo"])
        grupo, _ = Group.objects.get_or_create(name=codigo)
        grupos[codigo] = grupo
    return grupos


def test_lista_perfis_e_permissoes_do_catalogo(
    cliente_com_permissao_de_consulta: APIClient,
) -> None:
    """Retorna grupos cadastrados com nomes e permissões do catálogo."""
    grupos = criar_grupos_do_catalogo()

    response = cliente_com_permissao_de_consulta.get("/api/v1/perfis/")

    assert response.status_code == status.HTTP_200_OK
    assert [perfil["codigo"] for perfil in response.data] == [
        str(perfil["codigo"]) for perfil in PERFIS
    ]
    perfil_admin = response.data[0]
    assert perfil_admin["id"] == grupos["ADMINISTRADOR_COCEU"].pk
    assert perfil_admin["codigo"] == "ADMINISTRADOR_COCEU"
    assert perfil_admin["nome"] == "Administrador COCEU"
    assert perfil_admin["descricao"] == (
        "Permissões de acordo com a matriz institucional."
    )
    assert [
        permissao
        for permissao in perfil_admin["permissoes"]
        if permissao["recurso"] == "usuarios"
    ] == [
        {
            "codigo": "core.visualizar_usuarios",
            "recurso": "usuarios",
            "nome_recurso": "Usuários",
            "acao": "Visualizar",
        },
        {
            "codigo": "core.criar_usuarios",
            "recurso": "usuarios",
            "nome_recurso": "Usuários",
            "acao": "Criar",
        },
        {
            "codigo": "core.editar_usuarios",
            "recurso": "usuarios",
            "nome_recurso": "Usuários",
            "acao": "Editar",
        },
        {
            "codigo": "core.excluir_usuarios",
            "recurso": "usuarios",
            "nome_recurso": "Usuários",
            "acao": "Excluir",
        },
    ]


def test_omite_perfil_sem_grupo_cadastrado(
    cliente_com_permissao_de_consulta: APIClient,
) -> None:
    """Ignora na resposta os perfis que ainda não existem no banco."""
    grupos = criar_grupos_do_catalogo()
    grupos["GESTOR_COGED"].delete()

    response = cliente_com_permissao_de_consulta.get("/api/v1/perfis/")

    assert response.status_code == status.HTTP_200_OK
    assert [perfil["codigo"] for perfil in response.data] == [
        str(perfil["codigo"])
        for perfil in PERFIS
        if str(perfil["codigo"]) != "GESTOR_COGED"
    ]


def test_rejeita_usuario_sem_permissao_de_consulta(
    api_client: APIClient,
    usuario: Usuario,
) -> None:
    """Exige visualizar usuários para consultar os perfis disponíveis."""
    api_client.force_authenticate(user=usuario)

    response = api_client.get("/api/v1/perfis/")

    assert response.status_code == status.HTTP_403_FORBIDDEN
