"""
Configuração do app Django de usuários.

Registra o app ``usuarios`` em ``INSTALLED_APPS`` e define metadados padrão
de chave primária para models do pacote.
"""

from django.apps import AppConfig


class UsuariosConfig(AppConfig):
    """Metadados do app ``usuarios`` (models e rotas HTTP).

    Referenciado em ``config.settings.INSTALLED_APPS`` como
    ``usuarios.apps.UsuariosConfig``.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "usuarios"
