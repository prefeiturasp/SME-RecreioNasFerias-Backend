"""Modelos locais ligados a identidade e auditoria."""

from django.contrib.auth.models import AbstractUser

from apps.core.models.modelo_base import ModeloAtualizavel, ModeloBase


class Usuario(AbstractUser, ModeloAtualizavel):
    """Usuario base do Recreio, pronto para evolucoes futuras."""

    class Meta:
        """Metadados do modelo de usuário local."""

        verbose_name = "user"
        verbose_name_plural = "users"
        swappable = "AUTH_USER_MODEL"


class CargoPermitido(ModeloBase):
    """Representa um cargo liberado para acesso ao sistema."""

    pass


class LogLogin(ModeloBase):
    """Mantém a estrutura mínima da futura auditoria de login."""

    pass
