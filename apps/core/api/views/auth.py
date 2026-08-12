"""Endpoints placeholder de autenticação.

Mantém o contrato HTTP do login institucional já alinhado ao payload legado,
mesmo antes da implementacao real da autenticacao institucional.
"""

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.api.serializers import (
    AuthMessageSerializer,
    LoginRequestSerializer,
    LoginResponseSerializer,
)
from apps.core.constants import MENSAGEM_AUTENTICACAO_INDISPONIVEL
from apps.core.services import AuthService

auth_service = AuthService()


@extend_schema(
    tags=["Autenticação"],
    summary="Login institucional",
    operation_id="auth_login",
    request=LoginRequestSerializer,
    responses={
        200: OpenApiResponse(
            response=LoginResponseSerializer,
            description="Contrato previsto para a autenticação institucional.",
        ),
        400: OpenApiResponse(
            description="Payload invalido ou dados invalidos."
        ),
        401: OpenApiResponse(description="Credenciais invalidas."),
        403: OpenApiResponse(
            description="Cargo nao autorizado para o sistema."
        ),
        501: OpenApiResponse(
            response=AuthMessageSerializer,
            description=(
                "Autenticacao institucional ainda nao esta disponivel."
            ),
        ),
        502: OpenApiResponse(description="Falha de integracao externa."),
    },
)
@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request: Request) -> Response:
    """Valida o payload legado de login e delega o fluxo ao serviço.

    Args:
        request: Requisição HTTP recebida no endpoint de login.

    Returns:
        Resposta `200` com o payload legado quando o serviço existir, ou
        `501` enquanto a autenticação institucional estiver pendente.

    Raises:
        ValidationError: Quando o payload não respeita o contrato esperado.
    """
    serializer = LoginRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    try:
        payload = auth_service.login(**serializer.validated_data)
    except NotImplementedError:
        return Response(
            {"detalhe": MENSAGEM_AUTENTICACAO_INDISPONIVEL},
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )

    return Response(payload, status=status.HTTP_200_OK)


@extend_schema(
    tags=["Autenticação"],
    summary="Logout institucional",
    operation_id="auth_logout",
    request=None,
    responses={
        204: OpenApiResponse(
            description="Contrato previsto para encerramento de sessão.",
        ),
        401: OpenApiResponse(description="Token invalido ou expirado."),
        501: OpenApiResponse(
            response=AuthMessageSerializer,
            description=(
                "Autenticacao institucional ainda nao esta disponivel."
            ),
        ),
    },
)
@api_view(["POST"])
@permission_classes([AllowAny])
def logout_view(request: Request) -> Response:
    """Mantém o contrato futuro de encerramento de sessão.

    Args:
        request: Requisição HTTP recebida no endpoint de logout.

    Returns:
        Resposta `204` quando o fluxo real existir, ou `501` enquanto o logout
        institucional ainda não tiver sido implementado.
    """
    try:
        auth_service.logout(request.headers.get("Authorization", ""))
    except NotImplementedError:
        return Response(
            {"detalhe": MENSAGEM_AUTENTICACAO_INDISPONIVEL},
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )

    return Response(status=status.HTTP_204_NO_CONTENT)
