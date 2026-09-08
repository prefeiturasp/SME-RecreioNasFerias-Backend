"""Serializers de entrada das ações em massa."""

from rest_framework import serializers

from apps.definicoes_polos.api.serializers.definicao_polo_serializer import (
    DefinicaoPoloSerializer,
)
from apps.definicoes_polos.models import DefinicaoPolo


class PolosEmMassaSerializer(serializers.Serializer):
    """Entrada comum para ações que recebem polos por UUID."""

    polos = serializers.ListField(
        child=serializers.UUIDField(), allow_empty=False
    )

    def validate_polos(self, valores):
        """Impede a repetição do mesmo polo na seleção."""
        if len(valores) != len(set(valores)):
            raise serializers.ValidationError(
                "A lista de polos não pode conter UUIDs repetidos."
            )
        return valores


class VincularEmMassaSerializer(PolosEmMassaSerializer):
    """Entrada para vinculação em massa."""

    edicao = serializers.UUIDField()
    projecao_inscritos = serializers.IntegerField(min_value=0)


class AlterarTipoEmMassaItemSerializer(serializers.Serializer):
    """Entrada de uma alteração de tipo para um polo e edição."""

    polo_uuid = serializers.UUIDField()
    edicao = serializers.UUIDField(allow_null=True)
    tipo = serializers.ChoiceField(
        choices=DefinicaoPolo._meta.get_field("tipo").choices
    )


class AlterarTipoEmMassaSerializer(serializers.ListSerializer):
    """Lista de alterações de tipo a serem processadas em massa."""

    child = AlterarTipoEmMassaItemSerializer()

    def validate(self, valores):
        """Impede repetir o mesmo polo para a mesma edição."""
        if not valores:
            raise serializers.ValidationError(
                "A lista de operações não pode estar vazia."
            )
        chaves = [(item["polo_uuid"], item["edicao"]) for item in valores]
        if len(chaves) != len(set(chaves)):
            raise serializers.ValidationError(
                "A lista não pode repetir o mesmo polo para a mesma edição."
            )
        return valores


class AlterarEdicaoEmMassaSerializer(serializers.Serializer):
    """Entrada para movimentação de definições em massa."""

    definicoes = serializers.ListField(
        child=serializers.UUIDField(), allow_empty=False
    )
    edicao_destino = serializers.UUIDField()

    def validate_definicoes(self, valores):
        """Impede a repetição da mesma definição na seleção."""
        if len(valores) != len(set(valores)):
            raise serializers.ValidationError(
                "A lista de definições não pode conter UUIDs repetidos."
            )
        return valores


class AlterarTipoEmMassaAlteradoSerializer(serializers.Serializer):
    """Representa uma alteração de tipo concluída."""

    polo_uuid = serializers.UUIDField()
    edicao_uuid = serializers.UUIDField()
    tipo = serializers.ChoiceField(
        choices=DefinicaoPolo._meta.get_field("tipo").choices
    )


class AlterarTipoEmMassaIgnoradoSerializer(serializers.Serializer):
    """Representa um polo ignorado por não possuir edição."""

    polo_uuid = serializers.UUIDField()
    motivo = serializers.CharField()


class AlterarTipoEmMassaRespostaSerializer(serializers.Serializer):
    """Resposta da definição de tipos em massa."""

    mensagem = serializers.CharField()
    alterados = AlterarTipoEmMassaAlteradoSerializer(many=True)
    ignorados = AlterarTipoEmMassaIgnoradoSerializer(many=True)


class VincularEmMassaResponseSerializer(serializers.Serializer):
    """Resposta da vinculação em massa."""

    criadas = DefinicaoPoloSerializer(many=True, read_only=True)
    ignorados = serializers.ListField(
        child=serializers.UUIDField(), read_only=True
    )


__all__ = [
    "AlterarEdicaoEmMassaSerializer",
    "AlterarTipoEmMassaAlteradoSerializer",
    "AlterarTipoEmMassaIgnoradoSerializer",
    "AlterarTipoEmMassaItemSerializer",
    "AlterarTipoEmMassaRespostaSerializer",
    "AlterarTipoEmMassaSerializer",
    "PolosEmMassaSerializer",
    "VincularEmMassaSerializer",
    "VincularEmMassaResponseSerializer",
]
