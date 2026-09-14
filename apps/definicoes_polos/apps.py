"""Configuração do app `definicoes_polos`."""

from django.apps import AppConfig


class DefinicoesPolosConfig(AppConfig):
    """Define a configuração padrão do domínio."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.definicoes_polos"
    label = "definicoes_polos"
    verbose_name = "Definições de Polos"
