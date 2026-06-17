"""
Modelos de dados do app de usuários (conta CoreSSO, cargos e logs).

Persiste contas sincronizadas após login, cargos SIGPAE autorizados e
trilha de auditoria de tentativas de autenticação na API.
"""

import uuid

from auditlog.models import AuditlogHistoryField
from auditlog.registry import auditlog
from common.models import ModeloAtualizavel, ModeloBase
from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser, ModeloAtualizavel):
    """Conta local sincronizada após login no CoreSSO.

    A senha Django permanece inutilizável; a credencial é validada no
    provedor externo. O login usa RF (``USERNAME_FIELD``) em vez de username.
    Permissões RBAC do CoreSSO são armazenadas em JSON para consulta local.

    Attributes:
        rf (str): Registro funcional único do servidor.
        nome_completo (str): Nome retornado pela integração SIGPAE.
        cpf (str): CPF truncado em 11 caracteres.
        contexto (str): Contexto de acesso CoreSSO.
        permissoes_rbac (list): Permissões normalizadas pós-login.
        inexistente_eol (bool): Indica ausência no cadastro EOL.
    """

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
        """Configuração ORM e rótulos para a tabela ``usuarios_conta``."""

        db_table = "usuarios_conta"
        verbose_name = "usuário"
        verbose_name_plural = "usuários"

    def __str__(self) -> str:
        """Representação legível para logs e interfaces de consulta.

        Returns:
            str: RF do usuário ou representação da chave primária se RF vazio.
        """
        return self.rf or str(self.pk)


class UserModel(ModeloBase):
    """Modelo ORM legado para CRUD de exemplo em ``/api/usuarios/``.

    Mantido para demonstração de arquitetura em camadas; não representa a
    conta autenticada via CoreSSO (ver ``Usuario``).
    """

    history = AuditlogHistoryField(pk_indexable=False)
    id = models.UUIDField(primary_key=True, editable=False)
    nome = models.CharField(max_length=100)
    email = models.EmailField(unique=True)

    class Meta:
        """Mapeamento para tabela ``usuarios`` com histórico auditlog."""

        db_table = "usuarios"


class CargoPermitidoModel(ModeloBase):
    """Códigos de cargo SIGPAE autorizados a autenticar na aplicação.

    Populada via migrações de dados; consultada em cada login
    por ``CargosPermitidosRepository``.
    """

    history = AuditlogHistoryField(pk_indexable=False)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo_cargo = models.IntegerField(unique=True)
    descricao_cargo = models.CharField(max_length=512)

    class Meta:
        """Mapeamento para tabela ``usuarios_cargos_permitidos``."""

        db_table = "usuarios_cargos_permitidos"


class LogLoginModel(ModeloBase):
    """Registro de tentativas de login na API (sucesso ou falha).

    Armazena IP, user-agent, código HTTP, mensagem e cargo associado em
    logins bem-sucedidos para auditoria e suporte operacional.
    """

    sucesso = models.BooleanField()
    login_tentativa = models.CharField(max_length=32, blank=True, default="")
    codigo_http = models.PositiveSmallIntegerField()
    mensagem = models.TextField(blank=True, default="")
    endereco_ip = models.CharField(max_length=45, blank=True, default="")
    user_agent = models.TextField(blank=True, default="")
    codigo_cargo = models.IntegerField(blank=True, null=True)
    descricao_cargo = models.CharField(max_length=500, blank=True, default="")

    class Meta(ModeloBase.Meta):
        """Herda ordenação de ``ModeloBase``; tabela ``usuarios_logs_login``."""

        db_table = "usuarios_logs_login"


auditlog.register(Usuario)
auditlog.register(UserModel)
auditlog.register(CargoPermitidoModel)
