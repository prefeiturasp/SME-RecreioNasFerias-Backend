"""Serializers das definições de polos."""

from rest_framework import serializers

from apps.definicoes_polos.models import DefinicaoPolo
from apps.edicoes.api.serializers.edicao_serializer import (
    EdicaoResumoSerializer,
)
from apps.edicoes.models import Edicao
from apps.polos.api.serializers.polo_serializer import PoloSerializer
from apps.polos.models import Polo


class DefinicaoPoloSerializer(serializers.ModelSerializer):
    """Contrato de entrada e saída de uma participação."""

    polo = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=Polo.objects.all(),
    )
    edicao = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=Edicao.objects.all(),
    )

    class Meta:
        """Configuração do serializer de participação."""

        model = DefinicaoPolo
        fields = (
            "uuid",
            "polo",
            "edicao",
            "tipo",
            "projecao_inscritos",
            "total_inscritos",
            "ponto_focal_nome",
            "ponto_focal_telefone",
            "ponto_focal_email",
            "ativo",
            "criado_em",
            "atualizado_em",
        )
        read_only_fields = (
            "uuid",
            "total_inscritos",
            "ativo",
            "criado_em",
            "atualizado_em",
        )


class DefinicaoPoloDetalhamentoSerializer(serializers.ModelSerializer):
    """Retorna a participação com todos os dados cadastrais do polo."""

    polo = PoloSerializer(read_only=True)
    edicao = EdicaoResumoSerializer(read_only=True)

    class Meta:
        """Configuração do serializer de detalhamento."""

        model = DefinicaoPolo
        fields = (
            "uuid",
            "polo",
            "edicao",
            "tipo",
            "projecao_inscritos",
            "total_inscritos",
            "ponto_focal_nome",
            "ponto_focal_telefone",
            "ponto_focal_email",
            "ativo",
            "criado_em",
            "atualizado_em",
        )
        read_only_fields = fields


class DefinicaoPoloHistoricoSerializer(serializers.ModelSerializer):
    """Retorna uma participação histórica com sua edição identificada."""

    edicao = EdicaoResumoSerializer(read_only=True)

    class Meta:
        """Configuração do serializer de histórico."""

        model = DefinicaoPolo
        fields = (
            "uuid",
            "edicao",
            "tipo",
            "projecao_inscritos",
            "total_inscritos",
            "ponto_focal_nome",
            "ponto_focal_telefone",
            "ponto_focal_email",
            "criado_em",
            "atualizado_em",
        )
        read_only_fields = fields


class PoloComDefinicaoSerializer(serializers.ModelSerializer):
    """Representa uma linha da listagem consolidada de polos."""

    polo_uuid = serializers.UUIDField(source="uuid", read_only=True)
    definicao_uuid = serializers.UUIDField(read_only=True, allow_null=True)
    edicao_uuid = serializers.UUIDField(read_only=True, allow_null=True)
    nome_edicao = serializers.CharField(read_only=True, allow_null=True)
    tipo_polo_edicao = serializers.CharField(read_only=True, allow_null=True)
    projecao_inscritos_edicao = serializers.IntegerField(
        read_only=True, allow_null=True
    )
    total_inscritos_edicao = serializers.IntegerField(
        read_only=True, allow_null=True
    )

    class Meta:
        """Configuração do serializer da listagem consolidada."""

        model = Polo
        fields = (
            "polo_uuid",
            "codigo_eol",
            "nome_polo",
            "dre_nome",
            "dre_codigo_eol",
            "tipo_ue",
            "gestao",
            "status",
            "ativo",
            "definicao_uuid",
            "edicao_uuid",
            "nome_edicao",
            "tipo_polo_edicao",
            "projecao_inscritos_edicao",
            "total_inscritos_edicao",
        )
