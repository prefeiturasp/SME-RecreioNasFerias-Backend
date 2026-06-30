"""Garante que o projeto não utilize o Django Admin."""

from django.conf import settings
from django.test import SimpleTestCase
from django.urls import get_resolver


class SemDjangoAdminTests(SimpleTestCase):
    """Valida ausência de configuração e rotas do Django Admin."""

    def test_installed_apps_nao_deve_incluir_django_admin(self) -> None:
        """Garante que ``django.contrib.admin`` não esteja em ``INSTALLED_APPS``."""
        self.assertNotIn("django.contrib.admin", settings.INSTALLED_APPS)

    def test_urls_nao_devem_expor_rota_admin(self) -> None:
        """Garante que não exista rota ``/admin/`` registrada no projeto."""
        padroes = [
            str(padrao.pattern)
            for padrao in get_resolver().url_patterns
        ]

        self.assertFalse(
            any(padrao.startswith("admin") for padrao in padroes),
            msg=f"Rotas admin encontradas: {padroes}",
        )
