"""Testes da integração de polos com o Django Admin."""

from django.contrib import admin
from django.test import RequestFactory

from apps.polos.admin import PoloAdmin
from apps.polos.models import Polo


def test_polo_esta_registrado_no_admin() -> None:
    """O modelo de polo está registrado com o ModelAdmin correto."""
    assert Polo in admin.site._registry
    assert isinstance(admin.site._registry[Polo], PoloAdmin)


def test_admin_exibe_complemento_opcional_e_gestao_obrigatoria() -> None:
    """O Admin reflete blank=True e a obrigatoriedade de gestão."""
    model_admin = PoloAdmin(Polo, admin.site)
    request = RequestFactory().get("/admin/polos/polo/add/")
    formulario = model_admin.get_form(request)

    assert formulario.base_fields["complemento"].required is False
    assert formulario.base_fields["gestao"].required is True
