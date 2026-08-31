"""Serializer HTTP do catálogo de DREs."""

from rest_framework import serializers


class DreSerializer(serializers.Serializer):
    """Representa uma DRE no contrato público do domínio de Polos."""

    codigo_dre = serializers.CharField()
    nome_dre = serializers.CharField()
    sigla_dre = serializers.CharField()
