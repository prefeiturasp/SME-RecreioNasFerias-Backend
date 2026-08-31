"""ViewSet HTTP do domínio de polos."""

from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    OpenApiTypes,
    extend_schema,
    extend_schema_view,
)
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.integracoes.eol.exceptions import (
    EolConfigError,
    EolContratoError,
    EolIndisponivelError,
)
from apps.polos.api.serializers import (
    DreSerializer,
    PoloSerializer,
    TipoEscolaSerializer,
)
from apps.polos.models import Polo
from apps.polos.services.polo_service import PoloService


@extend_schema_view(
    list=extend_schema(
        summary="Lista polos",
        tags=["Polos"],
        parameters=[
            OpenApiParameter(
                name="dre_codigo_eol",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filtra pelo código EOL da DRE.",
            ),
            OpenApiParameter(
                name="tipo_ue",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filtra pela sigla do tipo de UE.",
            ),
            OpenApiParameter(
                name="busca",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description=(
                    "Busca o termo no nome do Polo ou no nome da OSC."
                ),
            ),
        ],
    ),
    create=extend_schema(summary="Cria polo", tags=["Polos"]),
    retrieve=extend_schema(summary="Recupera polo", tags=["Polos"]),
    update=extend_schema(summary="Atualiza polo", tags=["Polos"]),
    partial_update=extend_schema(
        summary="Atualiza parcialmente polo", tags=["Polos"]
    ),
    destroy=extend_schema(summary="Exclui polo", tags=["Polos"]),
)
class PoloViewSet(viewsets.ModelViewSet):
    """Expõe os casos de uso HTTP dos polos."""

    queryset = Polo.objects.all()
    serializer_class = PoloSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "uuid"
    service_class = PoloService

    def get_queryset(self):
        """Retorna os polos pelo serviço de domínio."""
        if self.action != "list":
            return self.service_class().listar()
        return self.service_class().listar(
            dre_codigo_eol=self.request.query_params.get("dre_codigo_eol"),
            tipo_ue=self.request.query_params.get("tipo_ue"),
            busca=self.request.query_params.get("busca"),
        )

    @extend_schema(
        summary="Lista tipos de escola",
        description=(
            "Lista os tipos de escola disponíveis na EOL."
        ),
        tags=["Polos"],
        responses={
            200: TipoEscolaSerializer(many=True),
            502: OpenApiResponse(
                description="Falha na integração com a EOL."
            ),
        },
    )
    @action(
        detail=False,
        methods=["get"],
        url_path="tipos-escola",
        url_name="tipos-escola",
    )
    def tipos_escola(self, request) -> Response:
        """Retorna os tipos de escola normalizados pela integração EOL."""
        try:
            tipos_escola = self.service_class().listar_tipos_escola()
        except EolConfigError as exc:
            return Response(
                {"detalhe": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except (EolIndisponivelError, EolContratoError) as exc:
            return Response(
                {"detalhe": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        return Response(TipoEscolaSerializer(tipos_escola, many=True).data)

    @extend_schema(
        summary="Lista DREs",
        description=(
            "Lista as Diretorias Regionais de Educação disponíveis na EOL."
        ),
        tags=["Polos"],
        responses={
            200: DreSerializer(many=True),
            502: OpenApiResponse(
                description="Falha na integração com a EOL."
            ),
        },
    )
    @action(detail=False, methods=["get"], url_path="dres", url_name="dres")
    def dres(self, request) -> Response:
        """Retorna as DREs normalizadas pela integração EOL."""
        try:
            dres = self.service_class().listar_dres()
        except EolConfigError as exc:
            return Response(
                {"detalhe": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except (EolIndisponivelError, EolContratoError) as exc:
            return Response(
                {"detalhe": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        return Response(DreSerializer(dres, many=True).data)

    def perform_create(self, serializer: PoloSerializer) -> None:
        """Cria o polo por meio do serviço de domínio."""
        serializer.instance = self.service_class().criar(
            **serializer.validated_data
        )

    def perform_update(self, serializer: PoloSerializer) -> None:
        """Atualiza o polo por meio do serviço de domínio."""
        serializer.instance = self.service_class().atualizar(
            serializer.instance, **serializer.validated_data
        )

    def perform_destroy(self, instance: Polo) -> None:
        """Recusa a exclusão pelo serviço de domínio."""
        self.service_class().excluir(instance)
