"""Testes dos caminhos auxiliares do serviço de autenticação."""

import pytest
from django.contrib.auth.models import Group, Permission

from apps.core.models import Usuario
from apps.core.services.auth_service import AuthService

pytestmark = pytest.mark.django_db


def test_obter_cargo_autorizado_sem_cargos_retorna_none() -> None:
    """Retorna None quando a identidade não informa cargos efetivos."""
    assert AuthService._obter_cargo_autorizado(()) is None


@pytest.mark.parametrize("origem_permissao", ["grupo", "individual"])
def test_nao_substitui_perfil_ou_permissao_existente(
    usuario: Usuario,
    origem_permissao: str,
) -> None:
    """Não adiciona Usuário UE se o usuário já tem acesso RBAC definido."""
    if origem_permissao == "grupo":
        grupo, _ = Group.objects.get_or_create(name="GESTOR_DICEU")
        usuario.groups.add(grupo)
    else:
        permissao = Permission.objects.get(
            content_type__app_label="core",
            codename="visualizar_usuarios",
        )
        usuario.user_permissions.add(permissao)

    AuthService._garantir_perfil_usuario_ue(usuario)

    assert not usuario.groups.filter(name="USUARIO_UE").exists()
