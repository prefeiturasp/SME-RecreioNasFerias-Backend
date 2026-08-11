"""Endpoint público de healthcheck."""

from django.views.decorators.http import require_GET
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response


@extend_schema(
    tags=["Infraestrutura"],
    summary="Verifica a saúde da aplicação",
    operation_id="health_check",
    responses={200: OpenApiResponse(description="Aplicação saudável.")},
)
@api_view(["GET"])
@permission_classes([AllowAny])
@require_GET
def health_check(request: Request) -> Response:
    """Retorna o status mínimo esperado pelos orquestradores."""
    return Response({"status": "ok"})
