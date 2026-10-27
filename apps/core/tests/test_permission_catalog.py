"""Verifica a consistência entre catálogo, grupos e migration RBAC."""

from importlib import import_module

import pytest
from django.contrib.auth.models import Group

from apps.core.permission_catalog import (
    PERFIS,
    PERMISSOES_PERSONALIZADAS_USUARIO,
)

pytestmark = pytest.mark.django_db

migration_rbac = import_module(
    "apps.core.migrations.0005_permissionamento_customizado"
)


def _permissoes_do_catalogo_por_perfil() -> dict[str, set[str]]:
    """Indexa as permissões de cada perfil declaradas no catálogo da API."""
    return {
        str(perfil["codigo"]): set(perfil["permissoes"])
        for perfil in PERFIS
    }


def test_migration_rbac_corresponde_ao_catalogo_da_api() -> None:
    """Mantém definições e permissões dos perfis alinhadas na origem."""
    assert set(migration_rbac.PERMISSOES_PERFIL) == set(
        _permissoes_do_catalogo_por_perfil()
    )

    permissoes_da_migration = {
        perfil: set(permissoes)
        for perfil, permissoes in migration_rbac.PERMISSOES_PERFIL.items()
    }
    assert permissoes_da_migration == _permissoes_do_catalogo_por_perfil()
    assert dict(migration_rbac.PERMISSOES_PERSONALIZADAS) == dict(
        PERMISSOES_PERSONALIZADAS_USUARIO
    )


def test_grupos_criados_pela_migration_correspondem_ao_catalogo() -> None:
    """Confere no banco se cada grupo recebeu as permissões do catálogo."""
    permissoes_esperadas = _permissoes_do_catalogo_por_perfil()
    grupos = {
        grupo.name: grupo
        for grupo in Group.objects.filter(name__in=permissoes_esperadas)
    }

    assert set(grupos) == set(permissoes_esperadas)

    for codigo_perfil, grupo in grupos.items():
        permissoes_atuais = set(
            grupo.permissions.values_list(
                "content_type__app_label",
                "codename",
            )
        )
        assert permissoes_atuais == {
            ("core", codename)
            for codename in permissoes_esperadas[codigo_perfil]
        }
