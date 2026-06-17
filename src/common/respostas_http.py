"""
Respostas JSON padronizadas para endpoints HTTP da API.

Define parâmetros de serialização e helpers de erro reutilizados pelas views.
"""

from __future__ import annotations

from django.http import JsonResponse

JSON_DUMPS_PARAMS = {"ensure_ascii": False, "indent": 2}


def resposta_erro_interno(erro: Exception) -> JsonResponse:
    """Converter falha inesperada de persistência em resposta HTTP 500.

    Args:
        erro (Exception): Exceção capturada durante operação de banco ou validação.

    Returns:
        JsonResponse: Corpo com campo ``error`` e status 500.
    """
    return JsonResponse(
        {"error": str(erro)},
        status=500,
        json_dumps_params=JSON_DUMPS_PARAMS,
    )


def resposta_paginacao_invalida() -> JsonResponse:
    """Retornar erro padronizado para parâmetros de paginação inválidos.

    Returns:
        JsonResponse: Corpo com mensagem de erro e status 400.
    """
    return JsonResponse(
        {"error": "Parâmetros de paginação inválidos"},
        status=400,
        json_dumps_params=JSON_DUMPS_PARAMS,
    )
