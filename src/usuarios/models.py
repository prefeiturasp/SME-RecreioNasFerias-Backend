"""Modelos de dados do app de usuários."""

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
