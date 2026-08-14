"""Endpoint público de healthcheck."""

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckView(APIView):
    """Retorna o status mínimo esperado pelos orquestradores."""

    authentication_classes: list[type] = []
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Infraestrutura"],
        summary="Verifica a saúde da aplicação",
        operation_id="health_check",
        auth=[],
        responses={200: OpenApiResponse(description="Aplicação saudável.")},
    )
    def get(self, request: Request) -> Response:
        """Responde ao healthcheck mínimo consumido pela infraestrutura."""
        return Response({"status": "ok"})
