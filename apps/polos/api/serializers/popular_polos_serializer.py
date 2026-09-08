"""Serializer HTTP da população de polos diretos."""

from rest_framework import serializers

from apps.polos.api.serializers.polo_serializer import PoloSerializer


class PopularUnidadesDiretasSerializer(serializers.Serializer):
    """Representa o resultado da população de unidades diretas."""

    total_consultados = serializers.IntegerField()
    total_novos = serializers.IntegerField()
    total_ja_existentes = serializers.IntegerField()
    unidades_novas = PoloSerializer(many=True)
    executada = serializers.BooleanField()
    motivo_ignorada = serializers.CharField(
        allow_null=True,
        allow_blank=True,
        required=False,
    )
    ultima_execucao_em = serializers.DateTimeField(allow_null=True)
