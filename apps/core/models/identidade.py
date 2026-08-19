"""Modelos locais ligados a identidade e auditoria."""

from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.core.models.modelo_base import ModeloBase


class CargoPermitido(ModeloBase):
    """Representa a whitelist local de cargos autorizados do sistema."""

    codigo_cargo = models.IntegerField(unique=True)
    descricao_cargo = models.CharField(max_length=512, blank=True, default="")

    def __str__(self) -> str:
        """Representação textual do cargo permitido."""
        if self.descricao_cargo:
            return f"{self.codigo_cargo} - {self.descricao_cargo}"
        return str(self.codigo_cargo)


class Usuario(AbstractUser, ModeloBase):
    """Usuario autenticado via CoreSSO com RF armazenado localmente."""

    rf = models.CharField(
        "RF",
        max_length=32,
        unique=True,
        blank=True,
        null=True,
    )
    nome_completo = models.CharField(max_length=255, blank=True, default="")
    cpf = models.CharField(max_length=11, blank=True, default="")
    cargo_permitido = models.ForeignKey(
        CargoPermitido,
        to_field="uuid",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="usuarios",
    )

    class Meta:
        """Metadados do modelo de usuário local."""

        verbose_name = "user"
        verbose_name_plural = "users"
        swappable = "AUTH_USER_MODEL"

    def __str__(self) -> str:
        """Representação textual curta do usuário."""
        return self.rf or self.username or str(self.pk)


class LogLogin(ModeloBase):
    """Mantém o registro local das tentativas de login."""

    sucesso = models.BooleanField()
    login_tentativa = models.CharField(max_length=32, blank=True, default="")
    codigo_http = models.PositiveSmallIntegerField()
    mensagem = models.TextField(blank=True, default="")
    endereco_ip = models.CharField(max_length=45, blank=True, default="")
    user_agent = models.TextField(blank=True, default="")
    codigo_cargo = models.IntegerField(blank=True, null=True)
    descricao_cargo = models.CharField(max_length=500, blank=True, default="")
