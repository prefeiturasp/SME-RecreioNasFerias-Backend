"""Smoke tests dos modelos base do `core`."""

import uuid

import pytest

from apps.core.models import CargoPermitido, Usuario

pytestmark = pytest.mark.django_db

TEST_RF = "0000001"
TEST_EMAIL = "usuario.teste@example.test"
TEST_AUTH_INPUT = "credencial-teste"


def test_modelo_base_define_timestamps() -> None:
    """Verifica se o modelo base preenche identificadores e timestamps."""
    cargo = CargoPermitido.objects.create(
        codigo_cargo=8800101,
        descricao_cargo="CARGO TESTE",
    )

    assert cargo.id is not None
    assert isinstance(cargo.uuid, uuid.UUID)
    assert cargo.criado_em is not None
    assert cargo.atualizado_em is not None


def test_usuario_manager_cria_usuario_por_rf() -> None:
    """Garante criação de usuário com username padrão e RF armazenado."""
    cargo = CargoPermitido.objects.create(
        codigo_cargo=8800101,
        descricao_cargo="CARGO TESTE",
    )
    usuario = Usuario.objects.create_user(
        TEST_RF,
        TEST_EMAIL,
        TEST_AUTH_INPUT,
        rf=TEST_RF,
        cargo_permitido=cargo,
    )

    assert usuario.rf == TEST_RF
    assert usuario.username == TEST_RF
    assert usuario.email == TEST_EMAIL
    assert usuario.cargo_permitido == cargo
    assert usuario.check_password(TEST_AUTH_INPUT) is True
    assert str(usuario) == TEST_RF
