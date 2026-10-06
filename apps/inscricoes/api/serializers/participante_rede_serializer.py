"""Serializer da consulta de participante da rede."""

from rest_framework import serializers


class ParticipanteRedeSerializer(serializers.Serializer):
    """Contrato público do participante usado no formulário."""

    codigo_eol = serializers.CharField(source="codigo_aluno")
    nome_participante = serializers.CharField(source="nome_aluno")
    data_nascimento = serializers.CharField()
    responsavel_nome = serializers.CharField(source="nome_responsavel")
    responsavel_nome_social = serializers.CharField()
    cep = serializers.CharField()
    logradouro = serializers.CharField()
    numero = serializers.CharField()
    complemento = serializers.CharField()
    bairro = serializers.CharField()
    cidade = serializers.CharField()
    telefone_contato_1 = serializers.CharField(source="celular_responsavel")
    telefone_contato_2 = serializers.CharField()
    email = serializers.CharField()
