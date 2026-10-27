"""Serializers do catálogo público de perfis RBAC."""

from rest_framework import serializers


class PermissaoPerfilSerializer(serializers.Serializer):
    """Representa uma permissão de recurso associada ao perfil."""

    codigo = serializers.CharField()
    recurso = serializers.CharField()
    nome_recurso = serializers.CharField()
    acao = serializers.CharField()


class PerfilSerializer(serializers.Serializer):
    """Representa um grupo disponível para atribuição a um usuário."""

    id = serializers.IntegerField(allow_null=True)
    codigo = serializers.CharField()
    nome = serializers.CharField()
    descricao = serializers.CharField()
    permissoes = PermissaoPerfilSerializer(many=True)
