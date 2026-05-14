"""Modelos de dados do app de usuários."""

import uuid

from django.db import models


class UserModel(models.Model):
    """Modelo ORM para persistência de usuários."""

    id = models.UUIDField(primary_key=True, editable=False)
    nome = models.CharField(max_length=100)
    email = models.EmailField(unique=True)

    class Meta:
        db_table = "usuarios"


class UsuarioAcessoModel(models.Model):
    """Modelo local para contexto e permissões após autenticação."""

    rf = models.CharField(max_length=7, unique=True)
    contexto = models.CharField(max_length=100, blank=True, default="")
    permissoes = models.JSONField(default=list)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "usuarios_acessos"


class CargoPermitidoModel(models.Model):
    """Códigos de cargo (integração SIGPAE/CoreSSO) autorizados a autenticar na aplicação."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo_cargo = models.IntegerField(unique=True)
    descricao_cargo = models.CharField(max_length=512)

    class Meta:
        db_table = "usuarios_cargos_permitidos"


class LogLoginModel(models.Model):
    """Registro de tentativas de login na API (sucesso ou falha)."""

    criado_em = models.DateTimeField(auto_now_add=True)
    sucesso = models.BooleanField()
    login_tentativa = models.CharField(max_length=32, blank=True, default="")
    codigo_http = models.PositiveSmallIntegerField()
    mensagem = models.TextField(blank=True, default="")
    endereco_ip = models.CharField(max_length=45, blank=True, default="")
    user_agent = models.TextField(blank=True, default="")
    codigo_cargo = models.IntegerField(blank=True, null=True)
    descricao_cargo = models.CharField(max_length=500, blank=True, default="")

    class Meta:
        db_table = "usuarios_logs_login"
        ordering = ("-criado_em",)
