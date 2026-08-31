"""Serializers HTTP do domínio de edições."""

from rest_framework import serializers

from apps.edicoes.models import Edicao


class EdicaoSerializer(serializers.ModelSerializer):
    """Representa o contrato de entrada e saída de uma edição."""

    class Meta:
        """Configuração do serializer de edição."""

        model = Edicao
        fields = (
            "uuid",
            "nome",
            "data_inicio",
            "data_fim",
            "inscricoes_inicio",
            "inscricoes_fim",
            "quantidade_inscritos",
            "quantidade_atendimento_efetivo",
            "quantidade_passeios",
            "quantidade_apresentacoes",
            "status",
            "ativo",
            "criado_em",
            "atualizado_em",
        )
        read_only_fields = (
            "uuid",
            "quantidade_inscritos",
            "quantidade_atendimento_efetivo",
            "quantidade_passeios",
            "quantidade_apresentacoes",
            "status",
            "ativo",
            "criado_em",
            "atualizado_em",
        )
