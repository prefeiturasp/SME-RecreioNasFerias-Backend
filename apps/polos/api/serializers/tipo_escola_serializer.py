"""Serializer HTTP do catálogo de Tipos de Escola."""

from rest_framework import serializers


class TipoEscolaSerializer(serializers.Serializer):
    """Representa um tipo de escola no contrato público do domínio de Polos."""

    codigo = serializers.IntegerField()
    descricao_sigla = serializers.CharField()
    
