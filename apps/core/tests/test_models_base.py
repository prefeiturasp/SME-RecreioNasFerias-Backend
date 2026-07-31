"""Smoke tests dos modelos base do `core`."""

import pytest

from apps.core.models import CargoPermitido

pytestmark = pytest.mark.django_db


def test_modelo_base_define_timestamps() -> None:
    """Verifica se o modelo base preenche criação e atualização."""
    cargo = CargoPermitido.objects.create()

    assert cargo.id is not None
    assert cargo.criado_em is not None
    assert cargo.atualizado_em is not None
