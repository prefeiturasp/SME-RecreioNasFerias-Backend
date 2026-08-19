"""Configuração do app `polos`."""

from django.apps import AppConfig


class PolosConfig(AppConfig):
    """Define a configuração padrão do app `polos`."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.polos"
    label = "polos"
    verbose_name = "Polos"
