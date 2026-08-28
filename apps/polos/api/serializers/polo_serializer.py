"""Serializers HTTP do domínio de polos."""

from rest_framework import serializers

from apps.polos.models import Polo


class PoloSerializer(serializers.ModelSerializer):
    """Representa o contrato de entrada e saída de um polo."""

    class Meta:
        """Configuração do serializer de polo."""

        model = Polo
        fields = (
            "uuid",
            "codigo_eol",
            "nome_polo",
            "nome_osc",
            "dre_nome",
            "dre_codigo_eol",
            "tipo",
            "status",
            "gestao",
            "tipo_ue",
            "quantidade_maxima_alunos",
            "cep",
            "tipo_logradouro",
            "logradouro",
            "bairro",
            "numero",
            "complemento",
            "nome_gestor",
            "email",
            "telefone",
            "observacoes_gerais",
            "ativo",
            "criado_em",
            "atualizado_em",
        )
        read_only_fields = (
            "uuid",
            "ativo",
            "criado_em",
            "atualizado_em",
        )
