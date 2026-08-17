"""Configuração do app `core`."""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Define a configuração padrão do app `core`."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    label = "core"
    verbose_name = "Core"

    def ready(self) -> None:
        """Carrega extensões locais do drf-spectacular."""
        from apps.core import spectacular_ext  # noqa: F401
