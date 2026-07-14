"""
Configuração do app Django de polos parceiros.

Registra o app ``polos`` em ``INSTALLED_APPS`` e define metadados
padrão para criação dos modelos.
"""

from django.apps import AppConfig


class PolosConfig(AppConfig):
    """Metadados do app ``polos`` (models, views e migrações).

    Referenciado em ``config.settings.INSTALLED_APPS`` como
    ``polos.apps.PolosConfig``.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "polos"
