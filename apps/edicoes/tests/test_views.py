"""Testes dos endpoints HTTP de edições."""

from datetime import date

import pytest
from freezegun import freeze_time
from rest_framework import status

from apps.edicoes.constants import StatusEdicao

pytestmark = pytest.mark.django_db

URL = "/api/v1/edicoes/"


def _payload(nome: str = "Nova edição") -> dict[str, str]:
    """Monta um payload válido para a API."""
    return {
        "nome": nome,
        "data_inicio": "2099-01-01",
        "data_fim": "2099-01-31",
        "inscricoes_inicio": "2098-12-01",
        "inscricoes_fim": "2099-01-31",
    }


def test_lista_edicoes_exige_autenticacao(api_client) -> None:
    """A rota de domínio usa a permissão padrão de autenticado."""
    response = api_client.get(URL)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data == {
        "detalhe": "Credenciais de autenticacao nao foram informadas."
    }


def test_cria_edicao_pela_api(cliente_autenticado) -> None:
    """O POST cria uma edição e retorna seus dados públicos."""
    response = cliente_autenticado.post(URL, _payload(), format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["nome"] == "Nova edição"
    assert response.data["status"] == StatusEdicao.PLANEJADA
    assert response.data["quantidade_inscritos"] == 0


def test_retorna_primeiro_erro_de_regra_de_negocio(
    cliente_autenticado,
    edicao_factory,
) -> None:
    """Erros de domínio retornam detalhe como string única."""
    edicao_factory(
        data_inicio=date(2099, 1, 1),
        data_fim=date(2099, 1, 31),
        inscricoes_inicio=date(2098, 12, 1),
        inscricoes_fim=date(2099, 1, 31),
    )

    response = cliente_autenticado.post(
        URL,
        _payload(nome="Outra edição"),
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data == {
        "detalhe": "Erro: já existe edição no período cadastrado."
    }


def test_atualiza_edicao_pela_api(cliente_autenticado, edicao_factory) -> None:
    """O PATCH atualiza campos permitidos da edição."""
    edicao = edicao_factory(nome="Nome antigo")

    response = cliente_autenticado.patch(
        f"{URL}{edicao.uuid}/",
        {"nome": "Nome novo"},
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["nome"] == "Nome novo"


def test_nao_atualiza_edicao_encerrada_pela_api(
    cliente_autenticado,
    edicao_factory,
) -> None:
    """O PATCH de edição encerrada retorna erro de domínio."""
    with freeze_time("2099-02-01 12:00:00"):
        edicao = edicao_factory(
            data_inicio=date(2099, 1, 1),
            data_fim=date(2099, 1, 31),
            inscricoes_inicio=date(2098, 12, 1),
            inscricoes_fim=date(2099, 1, 31),
        )

        response = cliente_autenticado.patch(
            f"{URL}{edicao.uuid}/",
            {"nome": "Não pode alterar"},
            format="json",
        )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data == {
        "detalhe": "Erro: edição encerrada não pode ser alterada."
    }


def test_remove_edicao_planejada_pela_api(
    cliente_autenticado,
    edicao_factory,
) -> None:
    """O DELETE remove uma edição ainda planejada."""
    edicao = edicao_factory()

    response = cliente_autenticado.delete(f"{URL}{edicao.uuid}/")

    assert response.status_code == status.HTTP_204_NO_CONTENT
