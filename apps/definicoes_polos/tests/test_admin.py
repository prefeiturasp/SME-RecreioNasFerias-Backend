"""Testes do Django Admin de definições de polos."""

from django.contrib import admin
from django.test import RequestFactory

from apps.definicoes_polos.admin import DefinicaoPoloAdmin
from apps.definicoes_polos.models import DefinicaoPolo


def test_definicao_polo_esta_registrada_no_admin() -> None:
    """O modelo está registrado com o ModelAdmin correto."""
    assert DefinicaoPolo in admin.site._registry
    assert isinstance(admin.site._registry[DefinicaoPolo], DefinicaoPoloAdmin)


def test_admin_exibe_total_como_somente_leitura() -> None:
    """O total calculado não pode ser editado no Admin."""
    model_admin = DefinicaoPoloAdmin(DefinicaoPolo, admin.site)
    request = RequestFactory().get(
        "/admin/definicoes_polos/definicaopolo/add/"
    )
    formulario = model_admin.get_form(request)

    assert "total_inscritos" not in formulario.base_fields
    assert "total_inscritos" in model_admin.readonly_fields
