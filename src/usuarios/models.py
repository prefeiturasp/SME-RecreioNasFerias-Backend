"""Modelos de dados do app de usuários."""

import uuid

from auditlog.models import AuditlogHistoryField
from auditlog.registry import auditlog
from common.models import ModeloAtualizavel, ModeloBase
from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser, ModeloAtualizavel):
    """Conta local sincronizada após login no CoreSSO (senha validada externamente)."""

    history = AuditlogHistoryField()
    username = None
    rf = models.CharField("RF", max_length=32, unique=True)
    nome_completo = models.CharField(max_length=255, blank=True, default="")
    cpf = models.CharField(max_length=11, blank=True, default="")
    contexto = models.CharField(max_length=100, blank=True, default="")
    permissoes_rbac = models.JSONField(default=list)
    inexistente_eol = models.BooleanField(default=False)

    USERNAME_FIELD = "rf"
    REQUIRED_FIELDS = ["email"]

    class Meta:
        db_table = "usuarios_conta"
        verbose_name = "usuário"
        verbose_name_plural = "usuários"

    def __str__(self) -> str:
        """Representação legível para admin e logs."""
        return self.rf or str(self.pk)


class UserModel(ModeloBase):
    """Modelo ORM para persistência de usuários (cadastro de exemplo / legado)."""

    history = AuditlogHistoryField(pk_indexable=False)
    id = models.UUIDField(primary_key=True, editable=False)
    nome = models.CharField(max_length=100)
    email = models.EmailField(unique=True)

    class Meta:
        db_table = "usuarios"


class CargoPermitidoModel(ModeloBase):
    """Códigos de cargo (integração SIGPAE/CoreSSO) autorizados a autenticar na aplicação."""

    history = AuditlogHistoryField(pk_indexable=False)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo_cargo = models.IntegerField(unique=True)
    descricao_cargo = models.CharField(max_length=512)

    class Meta:
        db_table = "usuarios_cargos_permitidos"


class LogLoginModel(ModeloBase):
    """Registro de tentativas de login na API (sucesso ou falha)."""

    sucesso = models.BooleanField()
    login_tentativa = models.CharField(max_length=32, blank=True, default="")
    codigo_http = models.PositiveSmallIntegerField()
    mensagem = models.TextField(blank=True, default="")
    endereco_ip = models.CharField(max_length=45, blank=True, default="")
    user_agent = models.TextField(blank=True, default="")
    codigo_cargo = models.IntegerField(blank=True, null=True)
    descricao_cargo = models.CharField(max_length=500, blank=True, default="")

    class Meta(ModeloBase.Meta):
        db_table = "usuarios_logs_login"


auditlog.register(Usuario)
auditlog.register(UserModel)
auditlog.register(CargoPermitidoModel)
