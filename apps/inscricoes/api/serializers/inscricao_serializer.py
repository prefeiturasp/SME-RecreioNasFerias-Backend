"""Contratos HTTP de cadastro e consulta de inscrições."""

from rest_framework import serializers

from apps.edicoes.api.serializers.edicao_serializer import (
    EdicaoResumoSerializer,
)
from apps.edicoes.models import Edicao
from apps.inscricoes.models import Inscricao
from apps.polos.api.serializers.polo_serializer import PoloResumoSerializer
from apps.polos.models import Polo


class InscricaoInformacoesBasicasSerializer(serializers.ModelSerializer):
    """Contrato de entrada e saída da primeira etapa do formulário."""

    polo = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=Polo.objects.all(),
        allow_null=True,
        required=False,
    )
    edicao = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=Edicao.objects.all(),
        allow_null=True,
        required=False,
    )

    grupo_label = serializers.CharField(
        source="get_grupo_display", read_only=True, allow_null=True
    )
    
    tipo_estudante_label = serializers.CharField(
        source="get_tipo_estudante_display", read_only=True, allow_null=True
    )
    
    status_label = serializers.CharField(
        source="get_status_display", read_only=True, allow_null=True
    )
    
    class Meta:
        """Configuração do contrato da primeira etapa."""

        model = Inscricao
        fields = (
            "uuid",
            "edicao",
            "polo",
            "tipo_estudante",
            "tipo_estudante_label",
            "grupo",
            "grupo_label",
            "codigo_eol",
            "cpf",
            "nome_participante",
            "data_nascimento",
            "responsavel_nome",
            "responsavel_nome_social",
            "cep",
            "tipo_logradouro",
            "logradouro",
            "numero",
            "complemento",
            "bairro",
            "cidade",
            "telefone_contato_1",
            "telefone_contato_2",
            "email",
            "dre_codigo_eol",
            "dre_nome",
            "status",
            "status_label",
            "ativo",
        )
        read_only_fields = ("uuid", "status", "ativo")


class InscricaoListagemSerializer(serializers.ModelSerializer):
    """Contrato enxuto da listagem de participantes."""

    polo = serializers.SlugRelatedField(
        slug_field="uuid", read_only=True, allow_null=True
    )
    polo_nome = serializers.CharField(
        source="polo.nome_polo", read_only=True, allow_null=True
    )
    
    grupo_label = serializers.CharField(
        source="get_grupo_display", read_only=True, allow_null=True
    )
    
    tipo_estudante_label = serializers.CharField(
        source="get_tipo_estudante_display", read_only=True, allow_null=True
    )
    
    status_label = serializers.CharField(
        source="get_status_display", read_only=True, allow_null=True
    )

    class Meta:
        """Configuração do contrato de listagem."""

        model = Inscricao
        fields = (
            "uuid",
            "tipo_estudante",
            "tipo_estudante_label",
            "polo",
            "polo_nome",
            "codigo_eol",
            "cpf",
            "nome_participante",
            "grupo",
            "grupo_label",
            "status",
            "status_label",
        )
        read_only_fields = fields


class InscricaoDetalheSerializer(InscricaoInformacoesBasicasSerializer):
    """Contrato de detalhamento da inscrição."""

    polo = PoloResumoSerializer(read_only=True, allow_null=True)
    edicao = EdicaoResumoSerializer(read_only=True, allow_null=True)
    grupo_label = serializers.CharField(
        source="get_grupo_display", read_only=True, allow_null=True
    )
    
    tipo_estudante_label = serializers.CharField(
        source="get_tipo_estudante_display", read_only=True, allow_null=True
    )
    
    status_label = serializers.CharField(
        source="get_status_display", read_only=True, allow_null=True
    )

    class Meta(InscricaoInformacoesBasicasSerializer.Meta):
        """Configuração do contrato somente leitura de detalhe."""

        read_only_fields = InscricaoInformacoesBasicasSerializer.Meta.fields


class PoloElegivelSerializer(serializers.ModelSerializer):
    """Polo disponível para seleção no cadastro da inscrição."""

    class Meta:
        """Configuração do contrato de polo elegível."""

        model = Polo
        fields = (
            "uuid",
            "codigo_eol",
            "nome_polo",
            "dre_codigo_eol",
            "dre_nome",
        )
        read_only_fields = fields
