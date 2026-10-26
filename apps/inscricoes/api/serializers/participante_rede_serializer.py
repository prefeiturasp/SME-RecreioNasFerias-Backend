"""Serializer da consulta de participante da rede."""

from __future__ import annotations

from datetime import date

from rest_framework import serializers

from apps.inscricoes.validators import calcular_idade_cheia


class ParticipanteRedeSerializer(serializers.Serializer):
    """Contrato público do participante usado no formulário."""

    codigo_eol = serializers.CharField(source="codigo_aluno")
    nome_participante = serializers.CharField(source="nome_aluno")
    data_nascimento = serializers.CharField()
    idade = serializers.SerializerMethodField()
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
    nome_turma = serializers.CharField()
    ano = serializers.CharField()
    unidade_educacional = serializers.CharField()
    unidade_educacional_codigo_eol = serializers.CharField()
    unidade_educacional_tipo = serializers.CharField()

    def get_idade(self, participante: object) -> int | None:
        """Devolve a idade em anos cheios a partir da data textual."""
        texto = str(getattr(participante, "data_nascimento", "") or "").strip()
        if len(texto) < 10:
            return None
        return calcular_idade_cheia(date.fromisoformat(texto[:10]))
