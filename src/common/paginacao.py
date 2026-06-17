"""
Utilitários de paginação HTTP compartilhados entre views da API.

Centraliza leitura de parâmetros de query string e montagem de payloads
paginados para manter consistência entre endpoints de listagem.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import Any, TypeVar

from django.db.models import QuerySet
from django.http import HttpRequest
from drf_spectacular.utils import OpenApiParameter, inline_serializer
from rest_framework import serializers

PAGINA_PADRAO = 1
TAMANHO_PAGINA_PADRAO = 10
TAMANHO_PAGINA_MAXIMO = 100

TModelo = TypeVar("TModelo")


def extrair_parametro_inteiro(
    request: HttpRequest,
    nome: str,
    *,
    padrao: int,
    minimo: int = 1,
) -> int | None:
    """Ler parâmetro inteiro da query string com validação básica.

    Args:
        request (HttpRequest): Requisição HTTP com query string.
        nome (str): Nome do parâmetro a ser lido.
        padrao (int): Valor usado quando o parâmetro não é informado.
        minimo (int): Menor valor aceito para o parâmetro.

    Returns:
        int | None: Valor válido ou ``None`` quando o parâmetro é inválido.
    """
    valor_bruto = request.GET.get(nome)
    if valor_bruto in (None, ""):
        return padrao
    try:
        valor = int(valor_bruto)
    except (TypeError, ValueError):
        return None
    if valor < minimo:
        return None
    return valor


def serializar_lista_paginada(
    request: HttpRequest,
    queryset: QuerySet[TModelo],
    serializar_item: Callable[[TModelo], dict[str, Any]],
) -> dict[str, Any] | None:
    """Montar payload paginado para qualquer queryset ordenável.

    Args:
        request (HttpRequest): Requisição GET com parâmetros de paginação.
        queryset (QuerySet[TModelo]): Consulta base a ser paginada.
        serializar_item: Função que converte cada instância em dicionário JSON.

    Returns:
        dict[str, Any] | None: Payload paginado ou ``None`` se parâmetros
            forem inválidos.
    """
    pagina = extrair_parametro_inteiro(request, "page", padrao=PAGINA_PADRAO)
    tamanho_pagina = extrair_parametro_inteiro(
        request,
        "pageSize",
        padrao=TAMANHO_PAGINA_PADRAO,
    )
    if pagina is None or tamanho_pagina is None:
        return None
    if tamanho_pagina > TAMANHO_PAGINA_MAXIMO:
        tamanho_pagina = TAMANHO_PAGINA_MAXIMO

    total = queryset.count()
    total_paginas = math.ceil(total / tamanho_pagina) if total else 0
    inicio = (pagina - 1) * tamanho_pagina
    fim = inicio + tamanho_pagina

    return {
        "results": [serializar_item(item) for item in queryset[inicio:fim]],
        "page": pagina,
        "pageSize": tamanho_pagina,
        "total": total,
        "totalPages": total_paginas,
    }


def parametros_paginacao_openapi() -> list[OpenApiParameter]:
    """Montar parâmetros de paginação documentados no OpenAPI.

    Returns:
        list[OpenApiParameter]: Parâmetros ``page`` e ``pageSize`` para schema.
    """
    return [
        OpenApiParameter(
            name="page",
            type=int,
            location=OpenApiParameter.QUERY,
            description="Número da página (inicia em 1).",
        ),
        OpenApiParameter(
            name="pageSize",
            type=int,
            location=OpenApiParameter.QUERY,
            description=(
                f"Tamanho da página (padrão {TAMANHO_PAGINA_PADRAO}, "
                f"máximo {TAMANHO_PAGINA_MAXIMO})."
            ),
        ),
    ]


def schema_resposta_lista_paginada(nome: str) -> serializers.Serializer:
    """Montar schema OpenAPI da resposta paginada genérica.

    Args:
        nome (str): Nome único do schema no documento OpenAPI.

    Returns:
        serializers.Serializer: Schema inline com metadados de paginação.
    """
    return inline_serializer(
        name=nome,
        fields={
            "results": serializers.ListField(child=serializers.DictField()),
            "page": serializers.IntegerField(),
            "pageSize": serializers.IntegerField(),
            "total": serializers.IntegerField(),
            "totalPages": serializers.IntegerField(),
        },
    )
