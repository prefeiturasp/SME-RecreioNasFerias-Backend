"""Testes do serializer de edições."""

import pytest

from apps.edicoes.api.serializers import EdicaoSerializer
from apps.edicoes.constants import StatusEdicao

pytestmark = pytest.mark.django_db


def test_serializer_retorna_campos_da_edicao(edicao_factory) -> None:
    """A resposta contém os campos públicos definidos no contrato."""
    edicao = edicao_factory()

    dados = EdicaoSerializer(edicao).data

    assert dados["uuid"] == str(edicao.uuid)
    assert dados["nome"] == edicao.nome
    assert dados["status"] == StatusEdicao.PLANEJADA
    assert dados["quantidade_inscritos"] == 0


def test_serializer_marca_status_e_indicadores_como_somente_leitura() -> None:
    """Status e consolidações não podem vir do payload da API."""
    serializer = EdicaoSerializer(
        data={
            "nome": "Nova edição",
            "data_inicio": "2099-01-01",
            "data_fim": "2099-01-31",
            "inscricoes_inicio": "2098-12-01",
            "inscricoes_fim": "2099-01-31",
            "status": StatusEdicao.ENCERRADA,
            "quantidade_inscritos": 999,
        }
    )

    assert serializer.is_valid(), serializer.errors
    assert "status" not in serializer.validated_data
    assert "quantidade_inscritos" not in serializer.validated_data


def test_serializer_exige_periodos_obrigatorios() -> None:
    """O contrato rejeita payload sem campos obrigatórios."""
    serializer = EdicaoSerializer(data={"nome": "Incompleta"})

    assert not serializer.is_valid()
    assert "data_inicio" in serializer.errors
    assert "data_fim" in serializer.errors
    assert "inscricoes_inicio" in serializer.errors
    assert "inscricoes_fim" in serializer.errors
