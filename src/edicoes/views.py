"""
Views HTTP para gestão de edições.

Expõe endpoints para criação, listagem, atualização e exclusão de edições,
com validações de negócio aplicadas no modelo.
"""

import json
import math
from typing import Any
from uuid import UUID

from django.core.exceptions import ValidationError
from django.db import DatabaseError
from django.db.models import QuerySet
from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
    inline_serializer,
)
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from edicoes.models import Edicao

_JSON = {"ensure_ascii": False, "indent": 2}
_PAGINA_PADRAO = 1
_TAMANHO_PAGINA_PADRAO = 10
_TAMANHO_PAGINA_MAXIMO = 100
_ERROS_PERSISTENCIA = (DatabaseError, TypeError, ValueError)


def _campos_quantidade_request() -> dict[str, serializers.Field]:
    """Montar campos opcionais de quantidade para schemas OpenAPI de criação."""
    return {
        "quantidadeInscritos": serializers.IntegerField(
            required=False, allow_null=True, min_value=0
        ),
        "quantidadeAtendimentoEfetivo": serializers.IntegerField(
            required=False, allow_null=True, min_value=0
        ),
        "quantidadePasseios": serializers.IntegerField(
            required=False, allow_null=True, min_value=0
        ),
        "quantidadeApresentacoes": serializers.IntegerField(
            required=False, allow_null=True, min_value=0
        ),
    }


def _schema_periodo(nome: str, *, obrigatorio: bool) -> serializers.Serializer:
    """Montar schema OpenAPI de período com datas de início e fim."""
    return inline_serializer(
        name=nome,
        fields={
            "de": serializers.DateField(required=obrigatorio),
            "ate": serializers.DateField(required=obrigatorio),
        },
    )


def _parametros_paginacao_openapi() -> list[OpenApiParameter]:
    """Montar parâmetros de paginação documentados no OpenAPI."""
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
                f"Tamanho da página (padrão {_TAMANHO_PAGINA_PADRAO}, "
                f"máximo {_TAMANHO_PAGINA_MAXIMO})."
            ),
        ),
    ]


def _schema_resposta_lista_paginada(nome: str) -> serializers.Serializer:
    """Montar schema OpenAPI da resposta paginada de edições."""
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


def _schema_create_request(nome: str) -> serializers.Serializer:
    """Montar schema OpenAPI do payload de criação de edição."""
    return inline_serializer(
        name=nome,
        fields={
            "nome": serializers.CharField(),
            "periodoEdicao": _schema_periodo(f"{nome}PeriodoEdicao", obrigatorio=True),
            "periodoInscricoes": _schema_periodo(
                f"{nome}PeriodoInscricoes",
                obrigatorio=True,
            ),
            **_campos_quantidade_request(),
        },
    )


def _schema_update_request(nome: str) -> serializers.Serializer:
    """Montar schema OpenAPI do payload de atualização de edição."""
    return inline_serializer(
        name=nome,
        fields={
            "nome": serializers.CharField(required=False),
            "periodoEdicao": _schema_periodo(
                f"{nome}PeriodoEdicao",
                obrigatorio=False,
            ),
            "periodoInscricoes": _schema_periodo(
                f"{nome}PeriodoInscricoes",
                obrigatorio=False,
            ),
        },
    )


def _resposta_erro_interno(erro: Exception) -> JsonResponse:
    """Converter falha inesperada de persistência em resposta HTTP 500."""
    return JsonResponse(
        {"error": str(erro)},
        status=500,
        json_dumps_params=_JSON,
    )


def _extrair_parametro_inteiro(
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


def _serializar_lista_paginada(
    request: HttpRequest,
    queryset: QuerySet[Edicao],
) -> dict[str, Any] | None:
    """Montar payload paginado da listagem de edições.

    Args:
        request (HttpRequest): Requisição GET com parâmetros de paginação.
        queryset (QuerySet[Edicao]): Consulta base ordenada por criação.

    Returns:
        dict[str, Any] | None: Payload paginado ou ``None`` se parâmetros
            forem inválidos.
    """
    pagina = _extrair_parametro_inteiro(request, "page", padrao=_PAGINA_PADRAO)
    tamanho_pagina = _extrair_parametro_inteiro(
        request,
        "pageSize",
        padrao=_TAMANHO_PAGINA_PADRAO,
    )
    if pagina is None or tamanho_pagina is None:
        return None
    if tamanho_pagina > _TAMANHO_PAGINA_MAXIMO:
        tamanho_pagina = _TAMANHO_PAGINA_MAXIMO

    total = queryset.count()
    total_paginas = math.ceil(total / tamanho_pagina) if total else 0
    inicio = (pagina - 1) * tamanho_pagina
    fim = inicio + tamanho_pagina

    return {
        "results": [_serializar_edicao(edicao) for edicao in queryset[inicio:fim]],
        "page": pagina,
        "pageSize": tamanho_pagina,
        "total": total,
        "totalPages": total_paginas,
    }


_CAMPOS_QUANTIDADE_CRIACAO = (
    ("quantidadeInscritos", "quantidade_inscritos"),
    ("quantidadeAtendimentoEfetivo", "quantidade_atendimento_efetivo"),
    ("quantidadePasseios", "quantidade_passeios"),
    ("quantidadeApresentacoes", "quantidade_apresentacoes"),
)


def _normalizar_quantidade_opcional(valor: Any) -> int | None:
    """Converter quantidade informada no payload para persistência opcional.

    Valores ausentes, nulos ou zero são armazenados como ``None`` no banco.

    Args:
        valor (Any): Valor recebido no JSON da requisição.

    Returns:
        int | None: Quantidade positiva ou ``None`` quando não informada/zerada.
    """
    if valor is None or valor == 0:
        return None
    return valor


def _extrair_quantidades_criacao(corpo: dict[str, Any]) -> dict[str, int | None]:
    """Mapear campos de quantidade do payload JSON para o modelo ``Edicao``.

    Args:
        corpo (dict[str, Any]): Payload JSON da requisição de criação.

    Returns:
        dict[str, int | None]: Campos do modelo prontos para ``objects.create``.
    """
    return {
        campo_modelo: _normalizar_quantidade_opcional(corpo.get(campo_json))
        for campo_json, campo_modelo in _CAMPOS_QUANTIDADE_CRIACAO
    }


def _serializar_edicao(edicao: Edicao) -> dict[str, Any]:
    """Converter uma edição em dicionário serializável para JSON.

    Args:
        edicao (Edicao): Instância do modelo a ser serializada.

    Returns:
        dict[str, Any]: Representação JSON da edição.

    Raises:
        AttributeError: Se a instância não possuir os atributos esperados.
    """
    return {
        "id": str(edicao.id),
        "nome": edicao.nome,
        "periodoEdicao": {
            "de": edicao.periodo_edicao_inicio.isoformat(),
            "ate": edicao.periodo_edicao_fim.isoformat(),
        },
        "periodoInscricoes": {
            "de": edicao.periodo_inscricoes_inicio.isoformat(),
            "ate": edicao.periodo_inscricoes_fim.isoformat(),
        },
        "quantidadeInscritos": edicao.quantidade_inscritos,
        "quantidadeAtendimentoEfetivo": edicao.quantidade_atendimento_efetivo,
        "quantidadePasseios": edicao.quantidade_passeios,
        "quantidadeApresentacoes": edicao.quantidade_apresentacoes,
    }


def _extrair_mensagem_erro(erro: ValidationError) -> str:
    """Extrair a primeira mensagem legível de um ``ValidationError``.

    Args:
        erro (ValidationError): Exceção de validação do Django.

    Returns:
        str: Mensagem de erro para resposta HTTP.
    """
    if hasattr(erro, "message_dict") and erro.message_dict:
        primeiro_valor = next(iter(erro.message_dict.values()))
        if isinstance(primeiro_valor, list) and primeiro_valor:
            return str(primeiro_valor[0])
        return str(primeiro_valor)
    if erro.messages:
        return str(erro.messages[0])
    return "Dados inválidos"


def _obter_edicao(edicao_id: str) -> Edicao | None:
    """Buscar edição pelo identificador UUID.

    Args:
        edicao_id (str): UUID da edição informado na URL.

    Returns:
        Edicao | None: Instância encontrada ou ``None`` se inexistente/inválido.
    """
    try:
        UUID(str(edicao_id))
    except ValueError:
        return None
    try:
        return Edicao.objects.get(pk=edicao_id)
    except Edicao.DoesNotExist:
        return None


def _aplicar_atualizacao(edicao: Edicao, corpo: dict[str, Any]) -> bool:
    """Aplicar campos opcionais do payload na instância de edição.

    Args:
        edicao (Edicao): Instância a ser atualizada.
        corpo (dict[str, Any]): Payload JSON da requisição.

    Returns:
        bool: ``True`` se ao menos um campo foi alterado.
    """
    alterou = False

    if "nome" in corpo:
        edicao.nome = corpo["nome"]
        alterou = True

    if "periodoEdicao" in corpo:
        periodo_edicao = corpo["periodoEdicao"] or {}
        if "de" in periodo_edicao:
            edicao.periodo_edicao_inicio = periodo_edicao["de"]
            alterou = True
        if "ate" in periodo_edicao:
            edicao.periodo_edicao_fim = periodo_edicao["ate"]
            alterou = True

    if "periodoInscricoes" in corpo:
        periodo_inscricoes = corpo["periodoInscricoes"] or {}
        if "de" in periodo_inscricoes:
            edicao.periodo_inscricoes_inicio = periodo_inscricoes["de"]
            alterou = True
        if "ate" in periodo_inscricoes:
            edicao.periodo_inscricoes_fim = periodo_inscricoes["ate"]
            alterou = True

    return alterou


@csrf_exempt
@extend_schema(
    tags=["Edições"],
    request=_schema_create_request("CreateEdicaoRequest"),
    responses={
        201: OpenApiResponse(description="Edição criada com sucesso"),
        400: OpenApiResponse(
            description="Payload inválido ou regra de negócio violada",
        ),
    },
)
def criar_edicao(request: HttpRequest) -> JsonResponse:
    """Criar uma edição a partir do payload JSON.

    Args:
        request (HttpRequest): Requisição POST com nome e períodos obrigatórios.

    Returns:
        JsonResponse: Edição criada (201), erro de validação (400) ou
            erro interno (500).

    Raises:
        Não propaga exceções: falhas são convertidas em resposta JSON.
    """
    try:
        corpo = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(
            {"error": "Payload JSON inválido"},
            status=400,
            json_dumps_params=_JSON,
        )

    try:
        periodo_edicao = corpo.get("periodoEdicao") or {}
        periodo_inscricoes = corpo.get("periodoInscricoes") or {}
        edicao = Edicao.objects.create(
            nome=corpo.get("nome"),
            periodo_edicao_inicio=periodo_edicao.get("de"),
            periodo_edicao_fim=periodo_edicao.get("ate"),
            periodo_inscricoes_inicio=periodo_inscricoes.get("de"),
            periodo_inscricoes_fim=periodo_inscricoes.get("ate"),
            **_extrair_quantidades_criacao(corpo),
        )
        return JsonResponse(
            _serializar_edicao(edicao),
            status=201,
            json_dumps_params=_JSON,
        )
    except ValidationError as erro:
        return JsonResponse(
            {"error": _extrair_mensagem_erro(erro)},
            status=400,
            json_dumps_params=_JSON,
        )
    except _ERROS_PERSISTENCIA as erro:
        return _resposta_erro_interno(erro)


@extend_schema(
    tags=["Edições"],
    parameters=_parametros_paginacao_openapi(),
    responses={
        200: _schema_resposta_lista_paginada("ListEdicoesResponse"),
        400: OpenApiResponse(description="Parâmetros de paginação inválidos"),
    },
)
def listar_edicoes(request: HttpRequest) -> JsonResponse:
    """Listar edições cadastradas com paginação, da mais recente para a mais antiga.

    Args:
        request (HttpRequest): Requisição GET com parâmetros opcionais ``page`` e
            ``pageSize``.

    Returns:
        JsonResponse: Lista paginada de edições (200) ou erro de parâmetros (400).

    Raises:
        Exception: Se ocorrer falha inesperada durante a consulta ao banco.
    """
    payload = _serializar_lista_paginada(request, Edicao.objects.all())
    if payload is None:
        return JsonResponse(
            {"error": "Parâmetros de paginação inválidos"},
            status=400,
            json_dumps_params=_JSON,
        )
    return JsonResponse(payload, status=200, json_dumps_params=_JSON)


@csrf_exempt
@extend_schema(
    tags=["Edições"],
    request=_schema_update_request("UpdateEdicaoRequest"),
    responses={
        200: OpenApiResponse(description="Edição atualizada com sucesso"),
        400: OpenApiResponse(
            description="Payload inválido ou regra de negócio violada",
        ),
        404: OpenApiResponse(description="Edição não encontrada"),
    },
)
def atualizar_edicao(request: HttpRequest, edicao_id: str) -> JsonResponse:
    """Atualizar parcialmente uma edição existente.

    Args:
        request (HttpRequest): Requisição PUT com campos opcionais no JSON.
        edicao_id (str): UUID da edição na URL.

    Returns:
        JsonResponse: Edição atualizada (200), erro de validação (400),
            não encontrada (404) ou erro interno (500).

    Raises:
        Não propaga exceções: falhas são convertidas em resposta JSON.
    """
    edicao = _obter_edicao(edicao_id)
    if edicao is None:
        return JsonResponse(
            {"error": "Edição não encontrada"},
            status=404,
            json_dumps_params=_JSON,
        )

    try:
        corpo = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(
            {"error": "Payload JSON inválido"},
            status=400,
            json_dumps_params=_JSON,
        )

    if not _aplicar_atualizacao(edicao, corpo):
        return JsonResponse(
            {"error": "Informe ao menos um campo para atualização"},
            status=400,
            json_dumps_params=_JSON,
        )

    try:
        edicao.save()
        return JsonResponse(
            _serializar_edicao(edicao),
            status=200,
            json_dumps_params=_JSON,
        )
    except ValidationError as erro:
        return JsonResponse(
            {"error": _extrair_mensagem_erro(erro)},
            status=400,
            json_dumps_params=_JSON,
        )
    except _ERROS_PERSISTENCIA as erro:
        return _resposta_erro_interno(erro)


@csrf_exempt
@extend_schema(
    tags=["Edições"],
    responses={
        204: OpenApiResponse(description="Edição removida com sucesso"),
        404: OpenApiResponse(description="Edição não encontrada"),
    },
)
def deletar_edicao(_: HttpRequest, edicao_id: str) -> JsonResponse:
    """Remover uma edição pelo identificador UUID.

    Args:
        _ (HttpRequest): Requisição DELETE.
        edicao_id (str): UUID da edição na URL.

    Returns:
        JsonResponse: Corpo vazio (204) ou não encontrada (404).

    Raises:
        Não propaga exceções: falhas são convertidas em resposta JSON.
    """
    edicao = _obter_edicao(edicao_id)
    if edicao is None:
        return JsonResponse(
            {"error": "Edição não encontrada"},
            status=404,
            json_dumps_params=_JSON,
        )

    edicao.delete()
    return JsonResponse({}, status=204, json_dumps_params=_JSON)


@csrf_exempt
@extend_schema_view(
    get=extend_schema(
        tags=["Edições"],
        parameters=_parametros_paginacao_openapi(),
        responses={
            200: _schema_resposta_lista_paginada("ListEdicoesResponseView"),
            400: OpenApiResponse(description="Parâmetros de paginação inválidos"),
        },
    ),
    post=extend_schema(
        tags=["Edições"],
        request=_schema_create_request("CreateEdicaoRequestView"),
        responses={201: OpenApiResponse(description="Edição criada com sucesso")},
    ),
)
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def edicoes(request: HttpRequest) -> JsonResponse:
    """Despachar listagem ou cadastro no endpoint ``/api/edicoes/``.

    Args:
        request (HttpRequest): Requisição HTTP ``GET`` ou ``POST``.

    Returns:
        JsonResponse: Resposta da operação de listagem ou cadastro.

    Raises:
        Não propaga exceções: handlers encapsulam erros em respostas HTTP.
    """
    if request.method == "GET":
        return listar_edicoes(request)
    return criar_edicao(request)


@csrf_exempt
@extend_schema_view(
    put=extend_schema(
        tags=["Edições"],
        request=_schema_update_request("UpdateEdicaoRequestView"),
        responses={200: OpenApiResponse(description="Edição atualizada")},
    ),
    delete=extend_schema(
        tags=["Edições"],
        responses={204: OpenApiResponse(description="Edição removida")},
    ),
)
@api_view(["PUT", "DELETE"])
@permission_classes([IsAuthenticated])
def edicao_por_id(request: HttpRequest, edicao_id: str) -> JsonResponse:
    """Despachar atualização ou exclusão em ``/api/edicoes/<uuid>/``.

    Args:
        request (HttpRequest): Requisição HTTP ``PUT`` ou ``DELETE``.
        edicao_id (str): UUID da edição na URL.

    Returns:
        JsonResponse: Resposta da operação correspondente ou 405.

    Raises:
        Não propaga exceções: handlers encapsulam erros em respostas HTTP.
    """
    if request.method == "PUT":
        return atualizar_edicao(request, str(edicao_id))
    return deletar_edicao(request, str(edicao_id))
