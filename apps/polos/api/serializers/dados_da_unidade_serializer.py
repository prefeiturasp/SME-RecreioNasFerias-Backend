"""Serializer para os dados de uma unidade obtidos pela integração EOL.

Este serializer é utilizado para normalizar e validar os dados retornados
pela integração com a EOL, garantindo que a aplicação receba informações
consistentes sobre as unidades educacionais.
"""
from rest_framework import serializers

class DadosUnidadeSerializer(serializers.Serializer):
    nome = serializers.CharField()
    codigo_eol = serializers.CharField()
    sigla_tipo_escola = serializers.CharField()
    nome_dre = serializers.CharField()
    sigla_dre = serializers.CharField()
    codigo_dre = serializers.CharField()
    email = serializers.EmailField(allow_null=True, required=False)
    telefone = serializers.CharField(allow_null=True, required=False)
    cep = serializers.CharField(allow_null=True, required=False)
    tipo_logradouro = serializers.CharField(allow_null=True, required=False)
    logradouro = serializers.CharField(allow_null=True, required=False)
    bairro = serializers.CharField(allow_null=True, required=False)
    numero = serializers.CharField(allow_null=True, required=False)
    complemento = serializers.CharField(allow_null=True, required=False)
    municipio = serializers.CharField(allow_null=True, required=False)
    uf = serializers.CharField(allow_null=True, required=False)
    