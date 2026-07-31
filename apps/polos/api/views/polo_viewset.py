"""ViewSet placeholder do domínio de polos."""

from drf_spectacular.utils import (
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from rest_framework import status, viewsets
from rest_framework.request import Request
from rest_framework.response import Response


@extend_schema_view(
    list=extend_schema(
        summary="Lista polos",
        responses={
            501: OpenApiResponse(
                description="Dominio ainda nao esta disponivel.",
            ),
        },
    )
)
class PoloViewSet(viewsets.ViewSet):
    """Expõe o endpoint placeholder dos polos."""

    def list(self, request: Request) -> Response:
        """Retorna a resposta temporária do domínio em construção."""
        return Response(
            {"detalhe": "Recurso ainda nao esta disponivel."},
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )
