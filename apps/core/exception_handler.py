"""Tratamento centralizado de exceções REST em pt-BR.

Converte mensagens padrão do Django REST Framework para textos em português
nos cenários mais comuns de autenticação, autorização e validação de request.
"""

from __future__ import annotations

from typing import Any

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
        }
        return {
            chaves.get(chave, chave): _traduzir_payload(valor)
            for chave, valor in payload.items()
        }

    if isinstance(payload, list):
        return [_traduzir_payload(item) for item in payload]

    return payload


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
    resposta = drf_exception_handler(exc, context)
    if resposta is None:
        return None

    resposta.data = _traduzir_payload(resposta.data)
    if isinstance(resposta.data, dict) and "detalhe" in resposta.data:
        resposta.data["detalhe"] = _normalizar_detalhe_portugues(
            exc,
            resposta.data["detalhe"],
        )

    return resposta
