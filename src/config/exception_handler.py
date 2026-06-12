"""Tratamento centralizado de exceções da API em português.

Converte mensagens padrão do Django REST Framework para textos em português
nos cenários mais comuns de autenticação, autorização e validação de request.
"""

from typing import Any

from rest_framework import status
from rest_framework.exceptions import (
    AuthenticationFailed,
    MethodNotAllowed,
    NotAuthenticated,
    ParseError,
    PermissionDenied,
)
from rest_framework.views import exception_handler as drf_exception_handler


def _normalizar_detalhe_portugues(exc: Exception, detail: Any) -> Any:
    """Normaliza mensagens automáticas do DRF para português.

    Args:
        exc (Exception): Exceção original levantada durante a request.
        detail (Any): Conteúdo atual de ``response.data["detail"]``.

    Returns:
        Any: Detalhe traduzido para português quando aplicável.
    """
    if isinstance(exc, NotAuthenticated):
        return "Credenciais de autenticação não foram informadas."
    if isinstance(exc, AuthenticationFailed):
        return str(detail) if detail else "Falha na autenticação."
    if isinstance(exc, PermissionDenied):
        return "Você não tem permissão para executar esta ação."
    if isinstance(exc, MethodNotAllowed):
        return "Método não permitido."
    if isinstance(exc, ParseError):
        return "Payload JSON inválido."
    return detail


def custom_exception_handler(exc: Exception, context: dict[str, Any]):
    """Aplica tradução de mensagens de erro padrão do DRF.

    Args:
        exc (Exception): Exceção capturada pelo pipeline do DRF.
        context (dict[str, Any]): Contexto da request em processamento.

    Returns:
        Response | None: Resposta padronizada quando a exceção é conhecida,
            ou ``None`` para delegar tratamento padrão do Django.
    """
    response = drf_exception_handler(exc, context)
    if response is None:
        return None

    detail = response.data.get("detail")
    if detail is not None:
        response.data["detail"] = _normalizar_detalhe_portugues(exc, detail)

    if response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR:
        response.data = {"detail": "Erro interno da aplicação."}

    return response

