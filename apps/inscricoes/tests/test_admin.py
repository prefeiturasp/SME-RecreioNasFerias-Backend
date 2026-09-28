"""Testes do Django Admin de inscrições."""

from django.contrib import admin
from django.test import RequestFactory

from apps.inscricoes.admin import InscricaoAdmin
from apps.inscricoes.models import Inscricao


def test_inscricao_esta_registrada_no_admin() -> None:
    """O modelo está registrado com o ModelAdmin correto."""
    assert Inscricao in admin.site._registry
    assert isinstance(admin.site._registry[Inscricao], InscricaoAdmin)


def test_admin_exibe_campos_de_endereco_no_formulario() -> None:
    """O formulário do Admin permite editar o tipo de logradouro."""
    model_admin = InscricaoAdmin(Inscricao, admin.site)
    request = RequestFactory().get("/admin/inscricoes/inscricao/add/")
    formulario = model_admin.get_form(request)

    assert "tipo_logradouro" in formulario.base_fields
    assert "status" in formulario.base_fields
