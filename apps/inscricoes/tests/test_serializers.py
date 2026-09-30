"""Testes dos serializers de inscrições."""

import pytest

from apps.inscricoes.api.serializers import (
    InscricaoDetalheSerializer,
    InscricaoInformacoesBasicasSerializer,
    InscricaoListagemSerializer,
    PoloElegivelSerializer,
)
from apps.inscricoes.constants import (
    GrupoInscricao,
    StatusInscricao,
    TipoEstudante,
)

pytestmark = pytest.mark.django_db


def test_serializer_basico_retorna_campos_e_choices(
    inscricao_factory,
) -> None:
    """O contrato básico expõe campos editáveis e status somente leitura."""
    inscricao = inscricao_factory()

    dados = InscricaoInformacoesBasicasSerializer(inscricao).data

    assert dados["uuid"] == str(inscricao.uuid)
    assert dados["tipo_logradouro"] == "Rua"
    assert dados["status"] == StatusInscricao.RASCUNHO


def test_serializer_basico_marca_status_e_metadados_como_somente_leitura(
    inscricao_factory,
) -> None:
    """Status não pode ser controlado pelo payload do cliente."""
    inscricao = inscricao_factory()
    serializer = InscricaoInformacoesBasicasSerializer(
        inscricao,
        data={
            "tipo_estudante": TipoEstudante.ESTUDANTE_EXTERNO,
            "grupo": GrupoInscricao.QUATRO_A_14_ANOS,
            "status": StatusInscricao.COMPLETA,
            "ativo": False,
        },
        partial=True,
    )

    assert serializer.is_valid(), serializer.errors
    assert "status" not in serializer.validated_data
    assert "ativo" not in serializer.validated_data


def test_serializer_detalhe_aninha_polo_e_edicao(
    inscricao_completa_factory,
) -> None:
    """O detalhe retorna UUID e nomes resumidos das relações."""
    inscricao = inscricao_completa_factory()

    dados = InscricaoDetalheSerializer(inscricao).data

    assert dados["polo"] == {
        "uuid": str(inscricao.polo.uuid),
        "nome_polo": inscricao.polo.nome_polo,
    }
    assert dados["edicao"] == {
        "uuid": str(inscricao.edicao.uuid),
        "nome": inscricao.edicao.nome,
    }


def test_serializer_listagem_expoe_nome_do_polo(
    inscricao_completa_factory,
) -> None:
    """A listagem oferece o identificador e o nome do polo."""
    inscricao = inscricao_completa_factory()

    dados = InscricaoListagemSerializer(inscricao).data

    assert str(dados["polo"]) == str(inscricao.polo.uuid)
    assert dados["polo_nome"] == inscricao.polo.nome_polo


def test_serializer_polo_elegivel_eh_somente_leitura(
    polo_factory,
) -> None:
    """O contrato de seleção retorna somente dados do polo."""
    polo = polo_factory()

    serializer = PoloElegivelSerializer(polo)

    assert serializer.data["nome_polo"] == polo.nome_polo
    assert set(serializer.fields) == {
        "uuid",
        "codigo_eol",
        "nome_polo",
        "dre_codigo_eol",
        "dre_nome",
    }
