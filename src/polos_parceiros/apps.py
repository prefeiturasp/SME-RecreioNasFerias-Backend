"""
Configuração do app Django de polos parceiros.

Registra o app ``polos_parceiros`` em ``INSTALLED_APPS`` e define metadados
padrão para criação dos modelos.
"""

from django.apps import AppConfig


class PolosParceirosConfig(AppConfig):
    """Metadados do app ``polos_parceiros`` (models, views e migrações).

    Referenciado em ``config.settings.INSTALLED_APPS`` como
    ``polos_parceiros.apps.PolosParceirosConfig``.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "polos_parceiros"
