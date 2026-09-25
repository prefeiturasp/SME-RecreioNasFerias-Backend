"""Serializers HTTP do domínio de polos."""

from rest_framework import serializers

from apps.polos.models import Polo


class PoloResumoSerializer(serializers.ModelSerializer):
    """Representa os dados essenciais do polo."""

    class Meta:
        """Configuração do serializer resumido de polo."""

        model = Polo
        fields = ("uuid", "nome_polo")
        read_only_fields = fields


class PoloSerializer(serializers.ModelSerializer):
    """Representa o contrato de entrada e saída de um polo."""

    endereco_completo = serializers.SerializerMethodField(read_only=True)

    def get_endereco_completo(self, obj) -> str:
        """Retorna o endereço completo do polo."""
        logradouro_completo_parts = [obj.tipo_logradouro, obj.logradouro]
        logradouro_completo = " ".join(filter(None, logradouro_completo_parts))

        partes = [
            logradouro_completo,
            obj.numero,
            obj.complemento,
            obj.bairro,
        ]
        endereco = ", ".join(filter(None, partes))
        return endereco

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
            "endereco_completo",
        )
        read_only_fields = (
            "uuid",
            "ativo",
        )
