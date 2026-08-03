"""Smoke tests dos modelos base do `core`."""

import uuid

import pytest

from apps.core.models import CargoPermitido

pytestmark = pytest.mark.django_db


def test_modelo_base_define_timestamps() -> None:
    """Verifica se o modelo base preenche identificadores e timestamps."""
    cargo = CargoPermitido.objects.create()

    assert cargo.id is not None
    assert isinstance(cargo.uuid, uuid.UUID)
    assert cargo.criado_em is not None
    assert cargo.atualizado_em is not None
