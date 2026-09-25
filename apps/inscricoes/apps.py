"""Configuração do domínio de inscrições."""

from django.apps import AppConfig


class InscricoesConfig(AppConfig):
    """Define a configuração padrão do domínio."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.inscricoes"
    label = "inscricoes"
    verbose_name = "Inscrições"
