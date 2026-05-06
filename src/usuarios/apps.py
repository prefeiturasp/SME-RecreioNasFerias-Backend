"""Configuração do app Django de usuários."""

from django.apps import AppConfig


class UsuariosConfig(AppConfig):
    """Define metadados e configurações do app usuarios."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "usuarios"
