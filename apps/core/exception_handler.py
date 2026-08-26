"""Tratamento centralizado de exceções REST em pt-BR.

Converte mensagens padrão do Django REST Framework para textos em português
nos cenários mais comuns de autenticação, autorização e validação de request.
"""

from __future__ import annotations

from typing import Any

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import (
    AuthenticationFailed,
    MethodNotAllowed,
    NotAuthenticated,
    ParseError,
    PermissionDenied,
)
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler


def _traduzir_payload(payload: Any) -> Any:
    """Traduz chaves padrão do DRF para o português.

    Args:
        payload: Estrutura de dados retornada pelo DRF.

    Returns:
        Estrutura equivalente com chaves padrão convertidas para pt-BR.
    """
    if isinstance(payload, dict):
        chaves = {
            "detail": "detalhe",
            "non_field_errors": "erros_gerais",
            "__all__": "detalhe",
        }
        return {
            chaves.get(chave, chave): _traduzir_payload(valor)
            for chave, valor in payload.items()
        }

    if isinstance(payload, list):
        return [_traduzir_payload(item) for item in payload]

    return payload


def _resposta_validation_error_django(
    exc: DjangoValidationError,
) -> Response:
    """Converte uma validação do Django em resposta HTTP 400."""
    if hasattr(exc, "message_dict"):
        payload: Any = exc.message_dict
    else:
        payload = {"__all__": exc.messages}

    return Response(
        {"detalhe": _primeira_mensagem(_traduzir_payload(payload))},
        status=400,
    )


def _primeira_mensagem(payload: Any) -> str:
    """Extrai a primeira mensagem textual de um payload de erro."""
    if isinstance(payload, str):
        return payload

    if isinstance(payload, dict):
        for valor in payload.values():
            mensagem = _primeira_mensagem(valor)
            if mensagem:
                return mensagem

    if isinstance(payload, list):
        for valor in payload:
            mensagem = _primeira_mensagem(valor)
            if mensagem:
                return mensagem

    return "Erro ao processar a requisição."


def _normalizar_detalhe_portugues(exc: Exception, detalhe: Any) -> Any:
    """Traduz mensagens padrão do DRF para português quando necessário.

    Args:
        exc: Exceção original capturada pelo pipeline do DRF.
        detalhe: Conteúdo atual do campo `detail` da resposta.

    Returns:
        Mensagem traduzida quando houver regra conhecida, ou o detalhe
        original.
    """
    if isinstance(exc, NotAuthenticated):
        return "Credenciais de autenticacao nao foram informadas."

    if isinstance(exc, AuthenticationFailed):
        return str(detalhe) if detalhe else "Falha na autenticacao."

    if isinstance(exc, PermissionDenied):
        return "Voce nao tem permissao para executar esta acao."

    if isinstance(exc, MethodNotAllowed):
        return "Metodo nao permitido."

    if isinstance(exc, ParseError):
        return "Payload JSON invalido."

    return detalhe


def tratar_excecoes_drf(
    exc: Exception,
    context: dict[str, Any],
) -> Response | None:
    """Aplica tradução e padronização às respostas de erro do DRF.

    Args:
        exc: Exceção capturada pelo pipeline do Django REST Framework.
        context: Contexto da request em processamento.

    Returns:
        Resposta tratada quando a exceção for conhecida pelo DRF, ou `None`
        para delegar o tratamento padrão do Django.
    """
    if isinstance(exc, DjangoValidationError):
        return _resposta_validation_error_django(exc)

    resposta = drf_exception_handler(exc, context)
    if resposta is None:
        return None

    payload = _traduzir_payload(resposta.data)
    if isinstance(payload, dict) and "detalhe" in payload:
        payload["detalhe"] = _normalizar_detalhe_portugues(
            exc,
            payload["detalhe"],
        )

    resposta.data = {"detalhe": _primeira_mensagem(payload)}

    return resposta
