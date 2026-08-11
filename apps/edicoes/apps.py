"""Configuração do app `edicoes`."""

from django.apps import AppConfig


class EdicoesConfig(AppConfig):
    """Define a configuração padrão do app `edicoes`."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.edicoes"
    label = "edicoes"
    verbose_name = "Edições"
