"""ViewSet HTTP do domínio de inscrições."""

from __future__ import annotations

from django.http import Http404
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiTypes,
    extend_schema,
    extend_schema_view,
    inline_serializer,
)
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.utils.paginacao_customizada import PaginacaoCustomizada
from apps.inscricoes.api.serializers import (
    InscricaoDetalheSerializer,
    InscricaoInformacoesBasicasSerializer,
    InscricaoListagemSerializer,
    PoloElegivelSerializer,
)
from apps.inscricoes.models import Inscricao
from apps.inscricoes.services.inscricao_service import InscricaoService


@extend_schema_view(
    list=extend_schema(
        summary="Lista inscrições",
        tags=["Inscrições"],
        parameters=[
            OpenApiParameter(
                name="tipo_estudante",
                type=OpenApiTypes.STR,
                description="Filtra por tipo de estudante",
                required=False,
            ),
            OpenApiParameter(
                name="polo",
                type=OpenApiTypes.UUID,
                description="Filtra por polo",
                required=False,
            ),
            OpenApiParameter(
                name="codigo_eol",
                type=OpenApiTypes.STR,
                description="Filtra por código EOL",
                required=False,
            ),
            OpenApiParameter(
                name="cpf",
                type=OpenApiTypes.STR,
                description="Filtra por CPF",
                required=False,
            ),
            OpenApiParameter(
                name="nome_participante",
                type=OpenApiTypes.STR,
                description="Filtra por nome do participante",
                required=False,
            ),
            OpenApiParameter(
                name="grupo",
                type=OpenApiTypes.STR,
                description="Filtra por grupo",
                required=False,
            ),
            OpenApiParameter(
                name="status",
                type=OpenApiTypes.STR,
                description="Filtra por status",
                required=False,
            ),
        ],
        ),
    create=extend_schema(summary="Cria inscrição", tags=["Inscrições"]),
    retrieve=extend_schema(summary="Detalha inscrição", tags=["Inscrições"]),
    update=extend_schema(summary="Atualiza inscrição", tags=["Inscrições"]),
    partial_update=extend_schema(
        summary="Atualiza parcialmente inscrição", tags=["Inscrições"]
    ),
    destroy=extend_schema(summary="Exclui inscrição", tags=["Inscrições"]),
)
class InscricaoViewSet(viewsets.ModelViewSet):
    """Expõe cadastro, gestão e polos elegíveis das inscrições."""

    queryset = Inscricao.objects.select_related("polo", "edicao")
    serializer_class = InscricaoInformacoesBasicasSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "uuid"
    pagination_class = PaginacaoCustomizada
    service_class = InscricaoService

    def get_queryset(self):
        """Retorna consulta filtrada na lista e detalhada nas demais ações."""
        if self.action == "list":
            return self.service_class().listar(
                tipo_estudante=self.request.query_params.get("tipo_estudante"),
                polo=self.request.query_params.get("polo"),
                codigo_eol=self.request.query_params.get("codigo_eol"),
                cpf=self.request.query_params.get("cpf"),
                nome_participante=self.request.query_params.get(
                    "nome_participante"
                ),
                grupo=self.request.query_params.get("grupo"),
                status=self.request.query_params.get("status"),
            )
        return self.queryset

    def get_serializer_class(self):
        """Seleciona o serializer conforme a ação HTTP."""
        if self.action == "list":
            return InscricaoListagemSerializer
        if self.action == "retrieve":
            return InscricaoDetalheSerializer
        return InscricaoInformacoesBasicasSerializer

    def get_object(self):
        """Converte recurso inexistente em erro de validação da API."""
        try:
            return super().get_object()
        except Http404 as exc:
            raise serializers.ValidationError(
                {"uuid": "Inscrição não encontrada."}
            ) from exc

    def perform_create(self, serializer):
        """Cria a inscrição pelo serviço de domínio."""
        serializer.instance = self.service_class().criar(
            **serializer.validated_data
        )

    def perform_update(self, serializer):
        """Atualiza a inscrição pelo serviço de domínio."""
        serializer.instance = self.service_class().atualizar(
            serializer.instance, **serializer.validated_data
        )

    def perform_destroy(self, instance):
        """Remove a inscrição."""
        instance.delete()

    @extend_schema(
        summary="Cancela inscrição",
        request=None,
        responses=InscricaoDetalheSerializer,
        tags=["Inscrições"],
    )
    @action(detail=True, methods=["post"])
    def cancelar(self, request, *args, **kwargs):
        """Executa o cancelamento manual da inscrição."""
        inscricao = self.get_object()
        inscricao = self.service_class().cancelar(inscricao)
        return Response(InscricaoDetalheSerializer(inscricao).data)

    @extend_schema(
        summary="Reativa inscrição",
        request=None,
        responses=InscricaoDetalheSerializer,
        tags=["Inscrições"],
    )
    @action(detail=True, methods=["post"])
    def reativar(self, request, *args, **kwargs):
        """Executa a reativação manual e recalcula o status."""
        inscricao = self.get_object()
        inscricao = self.service_class().reativar(inscricao)
        return Response(InscricaoDetalheSerializer(inscricao).data)

    @extend_schema(
        summary="Lista polos elegíveis para inscrição",
        parameters=[
            OpenApiParameter(
                name="dre_codigo_eol",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
            )
        ],
        responses=PoloElegivelSerializer(many=True),
        tags=["Inscrições"],
    )
    @action(detail=False, methods=["get"], url_path="polos-elegiveis")
    def polos_elegiveis(self, request, *args, **kwargs):
        """Lista polos ativos oficialmente definidos em alguma edição."""
        polos = self.service_class().listar_polos_elegiveis(
            request.query_params.get("dre_codigo_eol")
        )
        page = self.paginate_queryset(polos)
        if page is not None:
            return self.get_paginated_response(
                PoloElegivelSerializer(page, many=True).data
            )
        return Response(
            PoloElegivelSerializer(polos, many=True).data,
            status=status.HTTP_200_OK,
        )


    @extend_schema(
        summary="Valores de choices do domínio de inscrições",
        request=None,
        responses=inline_serializer(
            "ValoresChoicesResponse",
            fields={
                "grupo_inscricao": serializers.ListField(
                    child=serializers.DictField()
                ),
                "tipo_estudante": serializers.ListField(
                    child=serializers.DictField()
                ),
                "status_inscricao": serializers.ListField(
                    child=serializers.DictField()
                ),
            }
        ),
        tags=["Inscrições"],
    )
    @action(detail=False, methods=["get"], url_path="valores-choices")
    def valores_choices(self, request, *args, **kwargs):
        """Retorna os valores de todas os choices do domínio de inscrições."""
        from apps.core.utils.valores_choices import ValoresChoices

        return Response(ValoresChoices().get_values_inscricoes_choices())
