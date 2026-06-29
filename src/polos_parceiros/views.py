"""
Views HTTP para gestão de polos parceiros.

Expõe endpoints para criação, listagem, consulta, atualização e exclusão de
polos parceiros, com validações de negócio aplicadas no modelo.
"""

import json
from typing import Any
from uuid import UUID

from django.core.exceptions import ValidationError
from django.db import DatabaseError
from django.db.models import Q, QuerySet
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

from common.paginacao import (
    parametros_paginacao_openapi,
    schema_resposta_lista_paginada,
    serializar_lista_paginada,
)
from common.respostas_http import (
    JSON_DUMPS_PARAMS,
    resposta_erro_interno,
    resposta_paginacao_invalida,
    resposta_polo_parceiro_nao_encontrado,
)
from polos_parceiros.models import (
    PoloParceiro,
    STATUS_ATIVO,
    STATUS_INATIVO,
    TIPO_POLO_PARCEIRO,
)

_ERROS_PERSISTENCIA = (DatabaseError, TypeError, ValueError)

_CAMPOS_CRIACAO = (
    ("nomeOsc", "nome_osc"),
    ("nomePolo", "nome_polo"),
    ("dre", "dre"),
    ("tipoUe", "tipo_ue"),
    ("quantidadeMaximaAlunos", "quantidade_maxima_alunos"),
    ("cep", "cep"),
    ("endereco", "endereco"),
    ("nomeGestor", "nome_gestor"),
    ("emailPolo", "email_polo"),
    ("telefonePolo", "telefone_polo"),
)

_CAMPOS_ATUALIZACAO = _CAMPOS_CRIACAO + (
    ("observacoesGerais", "observacoes_gerais"),
    ("status", "status"),
)


def _schema_campos_polo(*, obrigatorio: bool) -> dict[str, serializers.Field]:
    """Montar campos OpenAPI comuns de polo parceiro."""
    return {
        "nomeOsc": serializers.CharField(required=obrigatorio),
        "nomePolo": serializers.CharField(required=obrigatorio),
        "dre": serializers.CharField(required=obrigatorio),
        "tipoUe": serializers.CharField(required=obrigatorio),
        "quantidadeMaximaAlunos": serializers.IntegerField(
            required=obrigatorio,
            min_value=1,
        ),
        "cep": serializers.CharField(required=obrigatorio),
        "endereco": serializers.CharField(required=obrigatorio),
        "nomeGestor": serializers.CharField(required=obrigatorio),
        "emailPolo": serializers.EmailField(required=obrigatorio),
        "telefonePolo": serializers.CharField(required=obrigatorio),
    }


def _schema_create_request(nome: str) -> serializers.Serializer:
    """Montar schema OpenAPI do payload de criação de polo parceiro."""
    return inline_serializer(
        name=nome,
        fields={
            **_schema_campos_polo(obrigatorio=True),
            "observacoesGerais": serializers.CharField(
                required=False,
                allow_blank=True,
            ),
        },
    )


def _schema_update_request(nome: str) -> serializers.Serializer:
    """Montar schema OpenAPI do payload de atualização de polo parceiro."""
    campos = _schema_campos_polo(obrigatorio=False)
    campos["observacoesGerais"] = serializers.CharField(
        required=False,
        allow_blank=True,
    )
    campos["status"] = serializers.ChoiceField(
        required=False,
        choices=[STATUS_ATIVO, STATUS_INATIVO],
    )
    return inline_serializer(name=nome, fields=campos)


def _extrair_campos_criacao(corpo: dict[str, Any]) -> dict[str, Any]:
    """Mapear campos do payload JSON para o modelo ``PoloParceiro``.

    Args:
        corpo (dict[str, Any]): Payload JSON da requisição de criação.

    Returns:
        dict[str, Any]: Campos do modelo prontos para ``objects.create``.
    """
    dados = {
        campo_modelo: corpo.get(campo_json)
        for campo_json, campo_modelo in _CAMPOS_CRIACAO
    }
    dados["observacoes_gerais"] = corpo.get("observacoesGerais", "")
    return dados


def _serializar_polo_parceiro(polo: PoloParceiro) -> dict[str, Any]:
    """Converter um polo parceiro em dicionário serializável para JSON.

    Args:
        polo (PoloParceiro): Instância do modelo a ser serializada.

    Returns:
        dict[str, Any]: Representação JSON do polo parceiro.

    Raises:
        AttributeError: Se a instância não possuir os atributos esperados.
    """
    return {
        "id": str(polo.id),
        "tipo": polo.tipo,
        "nomeOsc": polo.nome_osc,
        "nomePolo": polo.nome_polo,
        "dre": polo.dre,
        "tipoUe": polo.tipo_ue,
        "quantidadeMaximaAlunos": polo.quantidade_maxima_alunos,
        "cep": polo.cep,
        "endereco": polo.endereco,
        "nomeGestor": polo.nome_gestor,
        "emailPolo": polo.email_polo,
        "telefonePolo": polo.telefone_polo,
        "status": polo.status,
        "observacoesGerais": polo.observacoes_gerais,
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


def _obter_polo_parceiro(polo_id: str) -> PoloParceiro | None:
    """Buscar polo parceiro pelo identificador UUID.

    Args:
        polo_id (str): UUID do polo informado na URL.

    Returns:
        PoloParceiro | None: Instância encontrada ou ``None`` se inexistente/inválido.
    """
    try:
        UUID(str(polo_id))
    except ValueError:
        return None
    try:
        return PoloParceiro.objects.get(pk=polo_id)
    except PoloParceiro.DoesNotExist:
        return None


def _aplicar_atualizacao(polo: PoloParceiro, corpo: dict[str, Any]) -> bool:
    """Aplicar campos opcionais do payload na instância de polo parceiro.

    Args:
        polo (PoloParceiro): Instância a ser atualizada.
        corpo (dict[str, Any]): Payload JSON da requisição.

    Returns:
        bool: ``True`` se ao menos um campo foi alterado.
    """
    alterou = False

    for campo_json, campo_modelo in _CAMPOS_ATUALIZACAO:
        if campo_json in corpo:
            setattr(polo, campo_modelo, corpo[campo_json])
            alterou = True

    return alterou


def _valor_filtro_query(request: HttpRequest, nome: str) -> str | None:
    """Ler parâmetro textual da query string ignorando valores vazios.

    Args:
        request (HttpRequest): Requisição HTTP com query string.
        nome (str): Nome do parâmetro a ser lido.

    Returns:
        str | None: Valor normalizado ou ``None`` quando ausente ou vazio.
    """
    valor_bruto = request.GET.get(nome)
    if valor_bruto in (None, ""):
        return None
    valor_normalizado = str(valor_bruto).strip()
    return valor_normalizado if valor_normalizado else None


def _filtrar_polos_parceiros(
    request: HttpRequest,
    queryset: QuerySet[PoloParceiro],
) -> QuerySet[PoloParceiro]:
    """Aplicar filtros opcionais de listagem sobre o queryset de polos parceiros.

    Args:
        request (HttpRequest): Requisição GET com parâmetros de filtro opcionais.
        queryset (QuerySet[PoloParceiro]): Consulta base antes dos filtros.

    Returns:
        QuerySet[PoloParceiro]: Consulta filtrada conforme parâmetros informados.
    """
    dre = _valor_filtro_query(request, "dre")
    if dre is not None:
        queryset = queryset.filter(dre__iexact=dre)

    tipo_ue = _valor_filtro_query(request, "tipoUe")
    if tipo_ue is not None:
        queryset = queryset.filter(tipo_ue__iexact=tipo_ue)

    nome_polo_ou_osc = _valor_filtro_query(request, "nomePoloOuOsc")
    if nome_polo_ou_osc is not None:
        queryset = queryset.filter(
            Q(nome_polo__icontains=nome_polo_ou_osc)
            | Q(nome_osc__icontains=nome_polo_ou_osc),
        )

    return queryset


def _parametros_listagem_polos_parceiros_openapi() -> list[OpenApiParameter]:
    """Montar parâmetros de paginação e filtros documentados no OpenAPI.

    Returns:
        list[OpenApiParameter]: Parâmetros de listagem para schema da API.
    """
    return [
        *parametros_paginacao_openapi(),
        OpenApiParameter(
            name="dre",
            type=str,
            location=OpenApiParameter.QUERY,
            required=False,
            description="Filtra polos pela DRE (correspondência exata).",
        ),
        OpenApiParameter(
            name="tipoUe",
            type=str,
            location=OpenApiParameter.QUERY,
            required=False,
            description="Filtra polos pelo tipo de UE (correspondência exata).",
        ),
        OpenApiParameter(
            name="nomePoloOuOsc",
            type=str,
            location=OpenApiParameter.QUERY,
            required=False,
            description=(
                "Filtra polos pelo nome do polo ou da OSC (busca parcial)."
            ),
        ),
    ]


@csrf_exempt
@extend_schema(
    tags=["Polos Parceiros"],
    request=_schema_create_request("CreatePoloParceiroRequest"),
    responses={
        201: OpenApiResponse(description="Polo parceiro criado com sucesso"),
        400: OpenApiResponse(
            description="Payload inválido ou regra de negócio violada",
        ),
    },
)
def criar_polo_parceiro(request: HttpRequest) -> JsonResponse:
    """Criar um polo parceiro a partir do payload JSON.

    Args:
        request (HttpRequest): Requisição POST com dados obrigatórios do polo.

    Returns:
        JsonResponse: Polo criado (201), erro de validação (400) ou
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
            json_dumps_params=JSON_DUMPS_PARAMS,
        )

    try:
        polo = PoloParceiro.objects.create(
            tipo=TIPO_POLO_PARCEIRO,
            status=STATUS_ATIVO,
            **_extrair_campos_criacao(corpo),
        )
        return JsonResponse(
            _serializar_polo_parceiro(polo),
            status=201,
            json_dumps_params=JSON_DUMPS_PARAMS,
        )
    except ValidationError as erro:
        return JsonResponse(
            {"error": _extrair_mensagem_erro(erro)},
            status=400,
            json_dumps_params=JSON_DUMPS_PARAMS,
        )
    except _ERROS_PERSISTENCIA as erro:
        return resposta_erro_interno(erro)


@extend_schema(
    tags=["Polos Parceiros"],
    parameters=_parametros_listagem_polos_parceiros_openapi(),
    responses={
        200: schema_resposta_lista_paginada("ListPolosParceirosResponse"),
        400: OpenApiResponse(description="Parâmetros de paginação inválidos"),
    },
)
def listar_polos_parceiros(request: HttpRequest) -> JsonResponse:
    """Listar polos parceiros cadastrados com paginação e filtros opcionais.

    Args:
        request (HttpRequest): Requisição GET com parâmetros opcionais ``page``,
            ``pageSize``, ``dre``, ``tipoUe`` e ``nomePoloOuOsc``.

    Returns:
        JsonResponse: Lista paginada de polos (200) ou erro de parâmetros (400).

    Raises:
        Exception: Se ocorrer falha inesperada durante a consulta ao banco.
    """
    queryset = _filtrar_polos_parceiros(request, PoloParceiro.objects.all())
    payload = serializar_lista_paginada(
        request,
        queryset,
        _serializar_polo_parceiro,
    )
    if payload is None:
        return resposta_paginacao_invalida()
    return JsonResponse(payload, status=200, json_dumps_params=JSON_DUMPS_PARAMS)


@extend_schema(
    tags=["Polos Parceiros"],
    responses={
        200: OpenApiResponse(description="Polo parceiro encontrado"),
        404: OpenApiResponse(description="Polo parceiro não encontrado"),
    },
)
def buscar_polo_parceiro(_: HttpRequest, polo_id: str) -> JsonResponse:
    """Buscar um polo parceiro pelo identificador UUID.

    Args:
        _ (HttpRequest): Requisição GET.
        polo_id (str): UUID do polo na URL.

    Returns:
        JsonResponse: Polo encontrado (200) ou não encontrado (404).

    Raises:
        Não propaga exceções: falhas são convertidas em resposta JSON.
    """
    polo = _obter_polo_parceiro(polo_id)
    if polo is None:
        return resposta_polo_parceiro_nao_encontrado()

    return JsonResponse(
        _serializar_polo_parceiro(polo),
        status=200,
        json_dumps_params=JSON_DUMPS_PARAMS,
    )


@csrf_exempt
@extend_schema(
    tags=["Polos Parceiros"],
    request=_schema_update_request("UpdatePoloParceiroRequest"),
    responses={
        200: OpenApiResponse(description="Polo parceiro atualizado com sucesso"),
        400: OpenApiResponse(
            description="Payload inválido ou regra de negócio violada",
        ),
        404: OpenApiResponse(description="Polo parceiro não encontrado"),
    },
)
def atualizar_polo_parceiro(request: HttpRequest, polo_id: str) -> JsonResponse:
    """Atualizar parcialmente um polo parceiro existente.

    Args:
        request (HttpRequest): Requisição PUT com campos opcionais no JSON.
        polo_id (str): UUID do polo na URL.

    Returns:
        JsonResponse: Polo atualizado (200), erro de validação (400),
            não encontrado (404) ou erro interno (500).

    Raises:
        Não propaga exceções: falhas são convertidas em resposta JSON.
    """
    polo = _obter_polo_parceiro(polo_id)
    if polo is None:
        return resposta_polo_parceiro_nao_encontrado()

    try:
        corpo = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(
            {"error": "Payload JSON inválido"},
            status=400,
            json_dumps_params=JSON_DUMPS_PARAMS,
        )

    if not _aplicar_atualizacao(polo, corpo):
        return JsonResponse(
            {"error": "Informe ao menos um campo para atualização"},
            status=400,
            json_dumps_params=JSON_DUMPS_PARAMS,
        )

    try:
        polo.save()
        return JsonResponse(
            _serializar_polo_parceiro(polo),
            status=200,
            json_dumps_params=JSON_DUMPS_PARAMS,
        )
    except ValidationError as erro:
        return JsonResponse(
            {"error": _extrair_mensagem_erro(erro)},
            status=400,
            json_dumps_params=JSON_DUMPS_PARAMS,
        )
    except _ERROS_PERSISTENCIA as erro:
        return resposta_erro_interno(erro)


@csrf_exempt
@extend_schema(
    tags=["Polos Parceiros"],
    responses={
        204: OpenApiResponse(description="Polo parceiro removido com sucesso"),
        404: OpenApiResponse(description="Polo parceiro não encontrado"),
    },
)
def deletar_polo_parceiro(_: HttpRequest, polo_id: str) -> JsonResponse:
    """Remover um polo parceiro pelo identificador UUID.

    Args:
        _ (HttpRequest): Requisição DELETE.
        polo_id (str): UUID do polo na URL.

    Returns:
        JsonResponse: Corpo vazio (204) ou não encontrado (404).

    Raises:
        Não propaga exceções: falhas são convertidas em resposta JSON.
    """
    polo = _obter_polo_parceiro(polo_id)
    if polo is None:
        return resposta_polo_parceiro_nao_encontrado()

    polo.delete()
    return JsonResponse({}, status=204, json_dumps_params=JSON_DUMPS_PARAMS)


@csrf_exempt
@extend_schema_view(
    get=extend_schema(
        tags=["Polos Parceiros"],
        parameters=_parametros_listagem_polos_parceiros_openapi(),
        responses={
            200: schema_resposta_lista_paginada("ListPolosParceirosResponseView"),
            400: OpenApiResponse(description="Parâmetros de paginação inválidos"),
        },
    ),
    post=extend_schema(
        tags=["Polos Parceiros"],
        request=_schema_create_request("CreatePoloParceiroRequestView"),
        responses={
            201: OpenApiResponse(description="Polo parceiro criado com sucesso"),
        },
    ),
)
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def polos_parceiros(request: HttpRequest) -> JsonResponse:
    """Despachar listagem ou cadastro no endpoint ``/api/polos-parceiros/``.

    Args:
        request (HttpRequest): Requisição HTTP ``GET`` ou ``POST``.

    Returns:
        JsonResponse: Resposta da operação de listagem ou cadastro.

    Raises:
        Não propaga exceções: handlers encapsulam erros em respostas HTTP.
    """
    if request.method == "GET":
        return listar_polos_parceiros(request)
    return criar_polo_parceiro(request)


@csrf_exempt
@extend_schema_view(
    get=extend_schema(
        tags=["Polos Parceiros"],
        responses={
            200: OpenApiResponse(description="Polo parceiro encontrado"),
            404: OpenApiResponse(description="Polo parceiro não encontrado"),
        },
    ),
    put=extend_schema(
        tags=["Polos Parceiros"],
        request=_schema_update_request("UpdatePoloParceiroRequestView"),
        responses={200: OpenApiResponse(description="Polo parceiro atualizado")},
    ),
    delete=extend_schema(
        tags=["Polos Parceiros"],
        responses={204: OpenApiResponse(description="Polo parceiro removido")},
    ),
)
@api_view(["GET", "PUT", "DELETE"])
@permission_classes([IsAuthenticated])
def polo_parceiro_por_id(request: HttpRequest, polo_id: str) -> JsonResponse:
    """Despachar consulta, atualização ou exclusão em ``/api/polos-parceiros/<uuid>/``.

    Args:
        request (HttpRequest): Requisição HTTP ``GET``, ``PUT`` ou ``DELETE``.
        polo_id (str): UUID do polo na URL.

    Returns:
        JsonResponse: Resposta da operação correspondente ou 405.

    Raises:
        Não propaga exceções: handlers encapsulam erros em respostas HTTP.
    """
    if request.method == "GET":
        return buscar_polo_parceiro(request, str(polo_id))
    if request.method == "PUT":
        return atualizar_polo_parceiro(request, str(polo_id))
    return deletar_polo_parceiro(request, str(polo_id))
