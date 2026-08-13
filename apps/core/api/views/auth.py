"""Endpoints de autenticação institucional do app `core`."""

from __future__ import annotations

from contextlib import suppress
from typing import Any, Literal, cast

from django.conf import settings
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.exceptions import NotAuthenticated
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.serializers import (
    TokenRefreshSerializer,
    TokenVerifySerializer,
)
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.api.serializers import (
    LoginRequestSerializer,
    LoginResponseSerializer,
    MeResponseSerializer,
    RefreshResponseSerializer,
    TokenVerifyRequestSerializer,
)
from apps.core.services import (
    AuthAuditService,
    AuthService,
    CargoNaoAutorizadoError,
)
from apps.integracoes.coresso.exceptions import (
    CoressoAutenticacaoError,
    CoressoConfigError,
    CoressoContratoError,
    CoressoIndisponivelError,
)

auth_service = AuthService()
auth_audit_service = AuthAuditService()


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    """Define o refresh token em cookie HttpOnly."""
    same_site: Literal["Lax", "Strict", "None", False] = cast(
        Literal["Lax", "Strict", "None", False],
        settings.AUTH_REFRESH_COOKIE_SAMESITE,
    )
    response.set_cookie(
        key=settings.AUTH_REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=settings.AUTH_REFRESH_COOKIE_SECURE,
        samesite=same_site,
        path=settings.AUTH_REFRESH_COOKIE_PATH,
        max_age=int(settings.AUTH_JWT_REFRESH_TOKEN_LIFETIME.total_seconds()),
    )


def _clear_refresh_cookie(response: Response) -> None:
    """Remove o refresh token do cookie da aplicação."""
    response.delete_cookie(
        settings.AUTH_REFRESH_COOKIE_NAME,
        path=settings.AUTH_REFRESH_COOKIE_PATH,
    )


def _error_response(detalhe: str, status_code: int) -> Response:
    """Monta uma resposta de erro simples do fluxo de autenticação."""
    return Response({"detalhe": detalhe}, status=status_code)


class LoginView(APIView):
    """Autentica no CoreSSO, cria sessão local JWT e devolve o access token."""

    authentication_classes: list[type] = []
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Autenticação"],
        summary="Login institucional",
        operation_id="auth_login",
        request=LoginRequestSerializer,
        auth=[],
        responses={
            200: OpenApiResponse(
                response=LoginResponseSerializer,
                description="Login realizado com sucesso.",
            ),
            400: OpenApiResponse(
                description="Payload invalido ou dados invalidos."
            ),
            401: OpenApiResponse(description="Credenciais invalidas."),
            403: OpenApiResponse(
                description="Cargo nao autorizado para o sistema."
            ),
            502: OpenApiResponse(description="Falha de integracao externa."),
            500: OpenApiResponse(description="Falha interna da aplicacao."),
        },
    )
    def post(self, request: Request) -> Response:
        """Processa o login institucional e inicia a sessão JWT local."""
        request_serializer = LoginRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)

        login = request_serializer.validated_data["login"]
        senha = request_serializer.validated_data["senha"]

        try:
            session_data = auth_service.login(login=login, senha=senha)
        except CoressoAutenticacaoError as exc:
            auth_audit_service.registrar_tentativa_login(
                request,
                sucesso=False,
                login_tentativa=login,
                codigo_http=status.HTTP_401_UNAUTHORIZED,
                mensagem=str(exc),
            )
            return _error_response(
                str(exc),
                status.HTTP_401_UNAUTHORIZED,
            )
        except CargoNaoAutorizadoError as exc:
            auth_audit_service.registrar_tentativa_login(
                request,
                sucesso=False,
                login_tentativa=login,
                codigo_http=status.HTTP_403_FORBIDDEN,
                mensagem=str(exc),
            )
            return _error_response(
                str(exc),
                status.HTTP_403_FORBIDDEN,
            )
        except (CoressoIndisponivelError, CoressoContratoError) as exc:
            auth_audit_service.registrar_tentativa_login(
                request,
                sucesso=False,
                login_tentativa=login,
                codigo_http=status.HTTP_502_BAD_GATEWAY,
                mensagem=str(exc),
            )
            return _error_response(
                str(exc),
                status.HTTP_502_BAD_GATEWAY,
            )
        except CoressoConfigError as exc:
            auth_audit_service.registrar_tentativa_login(
                request,
                sucesso=False,
                login_tentativa=login,
                codigo_http=status.HTTP_500_INTERNAL_SERVER_ERROR,
                mensagem=str(exc),
            )
            return _error_response(
                str(exc),
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        refresh = RefreshToken.for_user(session_data.usuario)
        response_serializer = LoginResponseSerializer.from_session_data(
            session_data,
            token=str(refresh.access_token),
        )
        response = Response(
            response_serializer.data, status=status.HTTP_200_OK
        )
        _set_refresh_cookie(response, str(refresh))
        auth_audit_service.registrar_tentativa_login(
            request,
            sucesso=True,
            login_tentativa=session_data.rf,
            codigo_http=status.HTTP_200_OK,
            mensagem="Login realizado com sucesso.",
            cargo=session_data.cargo,
        )
        return response


class RefreshView(APIView):
    """Renova o access token usando o refresh token do cookie."""

    authentication_classes: list[type] = []
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Autenticação"],
        summary="Renovar token de acesso",
        operation_id="auth_refresh",
        request=None,
        auth=[],
        responses={
            200: OpenApiResponse(
                response=RefreshResponseSerializer,
                description="Token renovado com sucesso.",
            ),
            401: OpenApiResponse(
                description="Refresh token invalido ou expirado."
            ),
        },
    )
    def post(self, request: Request) -> Response:
        """Renova o token de acesso usando o refresh token disponível."""
        data = request.data.copy()
        if (
            "refresh" not in data
            and settings.AUTH_REFRESH_COOKIE_NAME in request.COOKIES
        ):
            data["refresh"] = request.COOKIES[
                settings.AUTH_REFRESH_COOKIE_NAME
            ]

        serializer = TokenRefreshSerializer(data=data)

        try:
            serializer.is_valid(raise_exception=True)
        except (InvalidToken, TokenError):
            response = _error_response(
                "Token invalido ou expirado.",
                status.HTTP_401_UNAUTHORIZED,
            )
            _clear_refresh_cookie(response)
            return response

        response = Response(
            {"token": serializer.validated_data["access"]},
            status=status.HTTP_200_OK,
        )
        if "refresh" in serializer.validated_data:
            _set_refresh_cookie(response, serializer.validated_data["refresh"])
        return response


class LogoutView(APIView):
    """Encerra a sessão local removendo e invalidando o refresh token."""

    authentication_classes: list[type] = []
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Autenticação"],
        summary="Logout institucional",
        operation_id="auth_logout",
        request=None,
        auth=[],
        responses={
            204: OpenApiResponse(
                description="Logout realizado com sucesso.",
            ),
            401: OpenApiResponse(description="Token invalido ou expirado."),
        },
    )
    def post(self, request: Request) -> Response:
        """Encerra a sessão local e remove o cookie de refresh."""
        refresh_token = request.COOKIES.get(settings.AUTH_REFRESH_COOKIE_NAME)
        if refresh_token:
            with suppress(Exception):
                RefreshToken(cast(Any, refresh_token)).blacklist()

        response = Response(status=status.HTTP_204_NO_CONTENT)
        _clear_refresh_cookie(response)
        return response


class MeView(APIView):
    """Retorna o perfil local do usuário autenticado."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Autenticação"],
        summary="Perfil do usuário autenticado",
        operation_id="auth_me",
        responses={
            200: OpenApiResponse(
                response=MeResponseSerializer,
                description="Perfil do usuário autenticado.",
            ),
            401: OpenApiResponse(description="Nao autenticado."),
        },
    )
    def get(self, request: Request) -> Response:
        """Retorna o perfil do usuário autenticado na aplicação."""
        if not request.user or not request.user.is_authenticated:
            raise NotAuthenticated()

        serializer = MeResponseSerializer.from_user(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class VerifyView(APIView):
    """Valida um access token JWT já emitido pela aplicação."""

    authentication_classes: list[type] = []
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Autenticação"],
        summary="Verificar token",
        operation_id="auth_verify",
        request=TokenVerifyRequestSerializer,
        auth=[],
        responses={
            200: OpenApiResponse(description="Token valido."),
            401: OpenApiResponse(description="Token invalido ou expirado."),
        },
    )
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Verifica a validade de um access token emitido pela API."""
        serializer = TokenVerifySerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except (InvalidToken, TokenError):
            return _error_response(
                "Token invalido ou expirado.",
                status.HTTP_401_UNAUTHORIZED,
            )
        return Response(serializer.validated_data, status=status.HTTP_200_OK)
