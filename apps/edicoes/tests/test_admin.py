"""Testes da integração de edições com o Django Admin."""

from unittest.mock import patch

from django.contrib import admin
from django.test import RequestFactory

from apps.edicoes.admin import EdicaoAdmin
from apps.edicoes.models import Edicao


def test_edicao_esta_registrada_no_admin() -> None:
    """O modelo de edição está registrado com o ModelAdmin correto."""
    assert Edicao in admin.site._registry
    assert isinstance(admin.site._registry[Edicao], EdicaoAdmin)


def test_admin_get_queryset_sincroniza_status() -> None:
    """A consulta do Admin sincroniza status antes de retornar registros."""
    model_admin = EdicaoAdmin(Edicao, admin.site)
    request = RequestFactory().get("/admin/edicoes/edicao/")

    with patch(
        "apps.edicoes.admin.EdicaoService.sincronizar_status"
    ) as sincronizar_status:
        queryset = model_admin.get_queryset(request)

    sincronizar_status.assert_called_once_with()
    assert queryset.model is Edicao
