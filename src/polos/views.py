"""
Views HTTP para gestão de polos parceiros.

Expõe endpoints para criação, listagem, consulta, atualização e exclusão de
polos parceiros, com validações de negócio aplicadas no modelo.
"""

import json
from typing import Any
from uuid import UUID

from django.core.exceptions import ValidationError
from django.db import DatabaseError, transaction
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
    resposta_polo_nao_encontrado,
)
from infrastructure.services.escolas_integracao_service import (
    EscolasIntegracaoConfigError,
    EscolasIntegracaoIndisponivelError,
)
from polos.models import (
    GESTAO_PARCEIRA,
    NOME_EDICAO_SEM_VINCULO,
    Polo,
    STATUS_ATIVO,
    STATUS_INATIVO,
    TIPO_POLO_CHOICES,
    TIPO_POLO_OFICIAL,
    TIPO_POLO_PENDENTE,
    TIPO_POLO_RESERVA,
)
from polos.sincronizacao import sincronizar_unidades_diretas

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
    ("nomeEdicao", "nome_edicao"),
    ("tipo", "tipo"),
)

_TIPOS_POLO_VALIDOS = {TIPO_POLO_PENDENTE, TIPO_POLO_OFICIAL, TIPO_POLO_RESERVA}


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
    """Mapear campos do payload JSON para o modelo ``Polo``.

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


def _serializar_polo(polo: Polo) -> dict[str, Any]:
    """Converter um polo parceiro em dicionário serializável para JSON.

    Args:
        polo (Polo): Instância do modelo a ser serializada.

    Returns:
        dict[str, Any]: Representação JSON do polo parceiro.

    Raises:
        AttributeError: Se a instância não possuir os atributos esperados.
    """
    return {
        "id": str(polo.id),
        "tipo": polo.tipo,
        "gestao": polo.gestao,
        "codigoEol": polo.codigo_eol,
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
        "nomeEdicao": polo.nome_edicao,
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


def _obter_polo(polo_id: str) -> Polo | None:
    """Buscar polo parceiro pelo identificador UUID.

    Args:
        polo_id (str): UUID do polo informado na URL.

    Returns:
        Polo | None: Instância encontrada ou ``None`` se inexistente/inválido.
    """
    try:
        UUID(str(polo_id))
    except ValueError:
        return None
    try:
        return Polo.objects.get(pk=polo_id)
    except Polo.DoesNotExist:
        return None


def _aplicar_atualizacao(polo: Polo, corpo: dict[str, Any]) -> bool:
    """Aplicar campos opcionais do payload na instância de polo parceiro.

    Args:
        polo (Polo): Instância a ser atualizada.
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


def _filtrar_polos(
    request: HttpRequest,
    queryset: QuerySet[Polo],
) -> QuerySet[Polo]:
    """Aplicar filtros opcionais de listagem sobre o queryset de polos.

    Args:
        request (HttpRequest): Requisição GET com parâmetros de filtro opcionais.
        queryset (QuerySet[Polo]): Consulta base antes dos filtros.

    Returns:
        QuerySet[Polo]: Consulta filtrada conforme parâmetros informados.
    """
    dre = _valor_filtro_query(request, "dre")
    if dre is not None:
        queryset = queryset.filter(dre__iexact=dre)

    tipo_ue = _valor_filtro_query(request, "tipoUe")
    if tipo_ue is not None:
        queryset = queryset.filter(tipo_ue__iexact=tipo_ue)

    gestao = _valor_filtro_query(request, "gestao")
    if gestao is not None:
        queryset = queryset.filter(gestao__iexact=gestao)

    tipo_polo = _valor_filtro_query(request, "tipoPolo")
    if tipo_polo is not None:
        queryset = queryset.filter(tipo__iexact=tipo_polo)

    nome_edicao = _valor_filtro_query(request, "nomeEdicao")
    if nome_edicao is not None:
        queryset = queryset.filter(nome_edicao__iexact=nome_edicao)

    nome_polo_ou_osc = _valor_filtro_query(request, "nomePoloOuOsc")
    nome_ue_ou_codigo_eol = _valor_filtro_query(request, "nomeUeOuCodigoEol")
    termo_busca = nome_ue_ou_codigo_eol or nome_polo_ou_osc
    if termo_busca is not None:
        queryset = queryset.filter(
            Q(nome_polo__icontains=termo_busca)
            | Q(nome_osc__icontains=termo_busca)
            | Q(codigo_eol__icontains=termo_busca),
        )

    return queryset


def _parametros_listagem_polos_openapi() -> list[OpenApiParameter]:
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
            name="gestao",
            type=str,
            location=OpenApiParameter.QUERY,
            required=False,
            description="Filtra polos pela gestão (Parceira ou Direta).",
        ),
        OpenApiParameter(
            name="tipoPolo",
            type=str,
            location=OpenApiParameter.QUERY,
            required=False,
            description=(
                "Filtra polos pelo tipo (Pendente, Polo oficial ou Polo reserva)."
            ),
        ),
        OpenApiParameter(
            name="nomeEdicao",
            type=str,
            location=OpenApiParameter.QUERY,
            required=False,
            description="Filtra polos pelo nome da edição (correspondência exata).",
        ),
        OpenApiParameter(
            name="nomePoloOuOsc",
            type=str,
            location=OpenApiParameter.QUERY,
            required=False,
            description=(
                "Filtra polos pelo nome do polo, OSC ou código EOL (busca parcial)."
            ),
        ),
        OpenApiParameter(
            name="nomeUeOuCodigoEol",
            type=str,
            location=OpenApiParameter.QUERY,
            required=False,
            description=(
                "Filtra polos pelo nome da UE/polo, OSC ou código EOL "
                "(busca parcial)."
            ),
        ),
    ]


@csrf_exempt
@extend_schema(
    tags=["Polos Parceiros"],
    request=_schema_create_request("CreatePoloRequest"),
    responses={
        201: OpenApiResponse(description="Polo parceiro criado com sucesso"),
        400: OpenApiResponse(
            description="Payload inválido ou regra de negócio violada",
        ),
    },
)
def criar_polo(request: HttpRequest) -> JsonResponse:
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
        polo = Polo.objects.create(
            tipo=TIPO_POLO_PENDENTE,
            gestao=GESTAO_PARCEIRA,
            status=STATUS_ATIVO,
            **_extrair_campos_criacao(corpo),
        )
        return JsonResponse(
            _serializar_polo(polo),
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
    parameters=_parametros_listagem_polos_openapi(),
    responses={
        200: schema_resposta_lista_paginada("ListPolosResponse"),
        400: OpenApiResponse(description="Parâmetros de paginação inválidos"),
    },
)
def listar_polos(request: HttpRequest) -> JsonResponse:
    """Listar polos parceiros cadastrados com paginação e filtros opcionais.

    Args:
        request (HttpRequest): Requisição GET com parâmetros opcionais ``page``,
            ``pageSize``, ``dre``, ``tipoUe``, ``gestao``, ``tipoPolo``,
            ``nomeEdicao``, ``nomeUeOuCodigoEol`` e ``nomePoloOuOsc``.

    Returns:
        JsonResponse: Lista paginada de polos (200) ou erro de parâmetros (400).
    """
    queryset = _filtrar_polos(request, Polo.objects.all())
    payload = serializar_lista_paginada(
        request,
        queryset,
        _serializar_polo,
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
def buscar_polo(_: HttpRequest, polo_id: str) -> JsonResponse:
    """Buscar um polo parceiro pelo identificador UUID.

    Args:
        _ (HttpRequest): Requisição GET.
        polo_id (str): UUID do polo na URL.

    Returns:
        JsonResponse: Polo encontrado (200) ou não encontrado (404).

    Raises:
        Não propaga exceções: falhas são convertidas em resposta JSON.
    """
    polo = _obter_polo(polo_id)
    if polo is None:
        return resposta_polo_nao_encontrado()

    return JsonResponse(
        _serializar_polo(polo),
        status=200,
        json_dumps_params=JSON_DUMPS_PARAMS,
    )


@csrf_exempt
@extend_schema(
    tags=["Polos Parceiros"],
    request=_schema_update_request("UpdatePoloRequest"),
    responses={
        200: OpenApiResponse(description="Polo parceiro atualizado com sucesso"),
        400: OpenApiResponse(
            description="Payload inválido ou regra de negócio violada",
        ),
        404: OpenApiResponse(description="Polo parceiro não encontrado"),
    },
)
def atualizar_polo(request: HttpRequest, polo_id: str) -> JsonResponse:
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
    polo = _obter_polo(polo_id)
    if polo is None:
        return resposta_polo_nao_encontrado()

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
            _serializar_polo(polo),
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
    tags=["Polos"],
    request=inline_serializer(
        name="AtualizarPolosEmLoteRequest",
        fields={
            "ids": serializers.ListField(
                child=serializers.UUIDField(),
                allow_empty=False,
            ),
            "nomeEdicao": serializers.CharField(required=False, allow_blank=True),
            "tipo": serializers.ChoiceField(
                required=False,
                choices=[
                    TIPO_POLO_PENDENTE,
                    TIPO_POLO_OFICIAL,
                    TIPO_POLO_RESERVA,
                ],
            ),
        },
    ),
    responses={
        200: OpenApiResponse(description="Polos atualizados em lote"),
        400: OpenApiResponse(description="Payload inválido"),
    },
)
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def atualizar_polos_em_lote(request: HttpRequest) -> JsonResponse:
    """Atualizar ``nomeEdicao`` e/ou ``tipo`` de um ou mais polos.

    Args:
        request (HttpRequest): Requisição PATCH com ``ids`` e campos a alterar.

    Returns:
        JsonResponse: Quantidade atualizada e polos persistidos (200) ou erro (400/500).
    """
    try:
        corpo = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(
            {"error": "Payload JSON inválido"},
            status=400,
            json_dumps_params=JSON_DUMPS_PARAMS,
        )

    ids_brutos = corpo.get("ids")
    if not isinstance(ids_brutos, list) or not ids_brutos:
        return JsonResponse(
            {"error": "Informe ao menos um identificador de polo"},
            status=400,
            json_dumps_params=JSON_DUMPS_PARAMS,
        )

    ids_validos: list[UUID] = []
    for valor in ids_brutos:
        try:
            ids_validos.append(UUID(str(valor)))
        except (TypeError, ValueError):
            return JsonResponse(
                {"error": "Identificador de polo inválido"},
                status=400,
                json_dumps_params=JSON_DUMPS_PARAMS,
            )

    atualiza_nome_edicao = "nomeEdicao" in corpo
    atualiza_tipo = "tipo" in corpo
    if not atualiza_nome_edicao and not atualiza_tipo:
        return JsonResponse(
            {"error": "Informe nomeEdicao e/ou tipo para atualização"},
            status=400,
            json_dumps_params=JSON_DUMPS_PARAMS,
        )

    nome_edicao = None
    if atualiza_nome_edicao:
        nome_edicao = (
            str(corpo.get("nomeEdicao") or "").strip() or NOME_EDICAO_SEM_VINCULO
        )

    tipo = None
    if atualiza_tipo:
        tipo = str(corpo.get("tipo") or "").strip()
        if tipo not in _TIPOS_POLO_VALIDOS:
            return JsonResponse(
                {
                    "error": (
                        "Erro: o tipo deve ser Pendente, Polo oficial ou Polo reserva"
                    ),
                },
                status=400,
                json_dumps_params=JSON_DUMPS_PARAMS,
            )

    polos = list(Polo.objects.filter(id__in=ids_validos))
    if not polos:
        return JsonResponse(
            {"error": "Nenhum polo encontrado para os identificadores informados"},
            status=400,
            json_dumps_params=JSON_DUMPS_PARAMS,
        )

    try:
        with transaction.atomic():
            for polo in polos:
                if atualiza_nome_edicao:
                    polo.nome_edicao = nome_edicao
                if atualiza_tipo:
                    polo.tipo = tipo
                polo.save()
    except ValidationError as erro:
        return JsonResponse(
            {"error": _extrair_mensagem_erro(erro)},
            status=400,
            json_dumps_params=JSON_DUMPS_PARAMS,
        )
    except _ERROS_PERSISTENCIA as erro:
        return resposta_erro_interno(erro)

    return JsonResponse(
        {
            "totalAtualizados": len(polos),
            "results": [_serializar_polo(polo) for polo in polos],
        },
        status=200,
        json_dumps_params=JSON_DUMPS_PARAMS,
    )


@csrf_exempt
@extend_schema(
    tags=["Polos Parceiros"],
    responses={
        204: OpenApiResponse(description="Polo parceiro removido com sucesso"),
        404: OpenApiResponse(description="Polo parceiro não encontrado"),
    },
)
def deletar_polo(_: HttpRequest, polo_id: str) -> JsonResponse:
    """Remover um polo parceiro pelo identificador UUID.

    Args:
        _ (HttpRequest): Requisição DELETE.
        polo_id (str): UUID do polo na URL.

    Returns:
        JsonResponse: Corpo vazio (204) ou não encontrado (404).

    Raises:
        Não propaga exceções: falhas são convertidas em resposta JSON.
    """
    polo = _obter_polo(polo_id)
    if polo is None:
        return resposta_polo_nao_encontrado()

    polo.delete()
    return JsonResponse({}, status=204, json_dumps_params=JSON_DUMPS_PARAMS)


def _parse_limite_unidades_diretas(request: HttpRequest) -> int | None:
    """Interpretar query ``limite`` opcional para unidades diretas.

    Args:
        request: Requisição HTTP com query string.

    Returns:
        Limite positivo ou ``None`` quando ausente.

    Raises:
        ValueError: Quando ``limite`` não é um inteiro positivo.
    """
    bruto = request.GET.get("limite")
    if bruto is None or str(bruto).strip() == "":
        return None
    try:
        limite = int(str(bruto).strip())
    except (TypeError, ValueError) as exc:
        raise ValueError("Parâmetro limite inválido") from exc
    if limite < 1:
        raise ValueError("Parâmetro limite inválido")
    return limite


def _parse_forcar_unidades_diretas(request: HttpRequest) -> bool:
    """Interpretar query ``forcar`` para ignorar o limite de uma sync por dia."""
    bruto = str(request.GET.get("forcar") or "").strip().casefold()
    return bruto in {"1", "true", "sim", "yes"}


@csrf_exempt
@extend_schema(
    tags=["Polos"],
    responses={
        200: OpenApiResponse(
            description="Opções de filtro derivadas dos polos persistidos",
        ),
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def listar_opcoes_filtro_polos(_: HttpRequest) -> JsonResponse:
    """Listar valores distintos de filtros a partir dos polos persistidos.

    Returns:
        JsonResponse: ``{ dres, tiposUe, gestoes, nomesEdicao, tiposPolo }`` ordenados.
    """
    dres = sorted(
        {
            valor.strip()
            for valor in Polo.objects.exclude(dre="")
            .values_list("dre", flat=True)
            .distinct()
            if valor and str(valor).strip()
        },
        key=str.casefold,
    )
    tipos_ue = sorted(
        {
            valor.strip()
            for valor in Polo.objects.exclude(tipo_ue="")
            .values_list("tipo_ue", flat=True)
            .distinct()
            if valor and str(valor).strip()
        },
        key=str.casefold,
    )
    gestoes = sorted(
        {
            valor.strip()
            for valor in Polo.objects.exclude(gestao="")
            .values_list("gestao", flat=True)
            .distinct()
            if valor and str(valor).strip()
        },
        key=str.casefold,
    )
    nomes_edicao = sorted(
        {
            valor.strip()
            for valor in Polo.objects.exclude(nome_edicao="")
            .values_list("nome_edicao", flat=True)
            .distinct()
            if valor and str(valor).strip()
        },
        key=str.casefold,
    )
    tipos_polo = [valor for valor, _rotulo in TIPO_POLO_CHOICES]

    return JsonResponse(
        {
            "dres": dres,
            "tiposUe": tipos_ue,
            "gestoes": gestoes,
            "nomesEdicao": nomes_edicao,
            "tiposPolo": tipos_polo,
        },
        status=200,
        json_dumps_params=JSON_DUMPS_PARAMS,
    )


@csrf_exempt
@extend_schema(
    tags=["Polos"],
    parameters=[
        OpenApiParameter(
            name="limite",
            type=int,
            location=OpenApiParameter.QUERY,
            required=False,
            description=(
                "Limita a quantidade de unidades filtradas antes da "
                "sincronização (útil para testes; omitir para processar todas)."
            ),
        ),
        OpenApiParameter(
            name="forcar",
            type=bool,
            location=OpenApiParameter.QUERY,
            required=False,
            description=(
                "Quando true, ignora o limite de uma sincronização por dia."
            ),
        ),
    ],
    responses={
        200: OpenApiResponse(
            description=(
                "Sincronização de unidades diretas concluída "
                "(novas gravadas com gestão Direta) ou ignorada por frequência"
            ),
        ),
        400: OpenApiResponse(description="Parâmetro limite inválido"),
        503: OpenApiResponse(description="SME Integração API indisponível"),
        500: OpenApiResponse(description="Configuração ou erro interno"),
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def listar_unidades_diretas(request: HttpRequest) -> JsonResponse:
    """Sincronizar unidades diretas da SME Integração na tabela ``polos``.

    Busca unidades elegíveis, compara com polos de gestão Direta pelo código
    EOL e persiste apenas as unidades ainda inexistentes. Por padrão executa
    no máximo uma vez por dia (fuso America/Sao_Paulo).

    Args:
        request: Requisição ``GET`` autenticada, com ``limite``/``forcar`` opcionais.

    Returns:
        JsonResponse: Totais da sincronização e polos novos criados.
    """
    try:
        limite = _parse_limite_unidades_diretas(request)
    except ValueError:
        return JsonResponse(
            {"error": "Parâmetro limite inválido"},
            status=400,
            json_dumps_params=JSON_DUMPS_PARAMS,
        )

    forcar = _parse_forcar_unidades_diretas(request)

    try:
        resultado = sincronizar_unidades_diretas(limite=limite, forcar=forcar)
    except EscolasIntegracaoConfigError as erro:
        return JsonResponse(
            {"error": str(erro)},
            status=500,
            json_dumps_params=JSON_DUMPS_PARAMS,
        )
    except EscolasIntegracaoIndisponivelError as erro:
        return JsonResponse(
            {"error": str(erro)},
            status=503,
            json_dumps_params=JSON_DUMPS_PARAMS,
        )
    except Exception as erro:  # noqa: BLE001 - resposta HTTP padronizada
        return resposta_erro_interno(erro)

    return JsonResponse(
        {
            "totalConsultados": resultado.total_consultados,
            "totalNovos": resultado.total_novos,
            "totalJaExistentes": resultado.total_ja_existentes,
            "unidadesNovas": [
                _serializar_polo(polo) for polo in resultado.polos_criados
            ],
            "executada": resultado.executada,
            "motivoIgnorada": resultado.motivo_ignorada,
            "ultimaExecucaoEm": (
                resultado.ultima_execucao_em.isoformat()
                if resultado.ultima_execucao_em is not None
                else None
            ),
        },
        status=200,
        json_dumps_params=JSON_DUMPS_PARAMS,
    )


@csrf_exempt
@extend_schema_view(
    get=extend_schema(
        tags=["Polos Parceiros"],
        parameters=_parametros_listagem_polos_openapi(),
        responses={
            200: schema_resposta_lista_paginada("ListPolosResponseView"),
            400: OpenApiResponse(description="Parâmetros de paginação inválidos"),
        },
    ),
    post=extend_schema(
        tags=["Polos Parceiros"],
        request=_schema_create_request("CreatePoloRequestView"),
        responses={
            201: OpenApiResponse(description="Polo parceiro criado com sucesso"),
        },
    ),
)
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def polos(request: HttpRequest) -> JsonResponse:
    """Despachar listagem ou cadastro no endpoint ``/api/polos/``.

    Args:
        request (HttpRequest): Requisição HTTP ``GET`` ou ``POST``.

    Returns:
        JsonResponse: Resposta da operação de listagem ou cadastro.

    Raises:
        Não propaga exceções: handlers encapsulam erros em respostas HTTP.
    """
    if request.method == "GET":
        return listar_polos(request)
    return criar_polo(request)


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
        request=_schema_update_request("UpdatePoloRequestView"),
        responses={200: OpenApiResponse(description="Polo parceiro atualizado")},
    ),
    delete=extend_schema(
        tags=["Polos Parceiros"],
        responses={204: OpenApiResponse(description="Polo parceiro removido")},
    ),
)
@api_view(["GET", "PUT", "DELETE"])
@permission_classes([IsAuthenticated])
def polo_por_id(request: HttpRequest, polo_id: str) -> JsonResponse:
    """Despachar consulta, atualização ou exclusão em ``/api/polos/<uuid>/``.

    Args:
        request (HttpRequest): Requisição HTTP ``GET``, ``PUT`` ou ``DELETE``.
        polo_id (str): UUID do polo na URL.

    Returns:
        JsonResponse: Resposta da operação correspondente ou 405.

    Raises:
        Não propaga exceções: handlers encapsulam erros em respostas HTTP.
    """
    if request.method == "GET":
        return buscar_polo(request, str(polo_id))
    if request.method == "PUT":
        return atualizar_polo(request, str(polo_id))
    return deletar_polo(request, str(polo_id))
