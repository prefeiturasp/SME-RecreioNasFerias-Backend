"""
Configuração do app Django de edições.

Registra o app ``edicoes`` em ``INSTALLED_APPS`` e define metadados
padrão para criação dos modelos.
"""

from django.apps import AppConfig


class EdicoesConfig(AppConfig):
    """Metadados do app ``edicoes`` (models, admin e migrações).

    Referenciado em ``config.settings.INSTALLED_APPS`` como
    ``edicoes.apps.EdicoesConfig``.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "edicoes"
