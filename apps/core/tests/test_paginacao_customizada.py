"""Testes da paginação customizada compartilhada."""

import pytest
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory
from rest_framework.serializers import ValidationError

from apps.core.utils.paginacao_customizada import PaginacaoCustomizada


def _request(**query_params):
    """Cria uma requisição DRF com os parâmetros informados."""
    request = APIRequestFactory().get("/", query_params)
    return Request(request)


def test_paginacao_retorna_resposta_padrao_com_metadados() -> None:
    """A paginação habilitada retorna metadados e resultados."""
    paginacao = PaginacaoCustomizada(page_size=2)

    resultado = paginacao.paginate_queryset(
        ["primeiro", "segundo", "terceiro"],
        _request(page=2),
    )
    resposta = paginacao.get_paginated_response(resultado)

    assert resposta.data == {
        "count": 3,
        "next": None,
        "previous": "http://testserver/",
        "results": ["terceiro"],
    }


def test_paginacao_converte_pagina_invalida_em_erro_de_validacao() -> None:
    """Páginas inexistentes retornam ValidationError em vez de 404."""
    paginacao = PaginacaoCustomizada(page_size=1)
    dados = ["único"]
    requisicao = _request(page=2)

    with pytest.raises(ValidationError) as exc_info:
        paginacao.paginate_queryset(dados, requisicao)

    assert "page" in exc_info.value.detail


def test_paginacao_desabilitada_retorna_todos_os_dados() -> None:
    """A paginação desabilitada retorna todos os dados sem metadados."""
    paginacao = PaginacaoCustomizada(page_size=1)

    resultado = paginacao.paginate_queryset(
        ["primeiro", "segundo"],
        _request(desabilita_paginacao="true"),
    )
    resposta = paginacao.get_paginated_response(resultado)

    assert resultado == ["primeiro", "segundo"]
    assert resposta.data == ["primeiro", "segundo"]
