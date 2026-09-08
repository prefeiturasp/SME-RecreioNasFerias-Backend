"""Testes dos serializers de definições de polos."""

import pytest

from apps.definicoes_polos.api.serializers import (
    AlterarEdicaoEmMassaSerializer,
    AlterarTipoEmMassaSerializer,
    DefinicaoPoloDetalhamentoSerializer,
    DefinicaoPoloHistoricoSerializer,
    DefinicaoPoloSerializer,
    VincularEmMassaResponseSerializer,
    VincularEmMassaSerializer,
)
from apps.definicoes_polos.constants import TipoPolo

pytestmark = pytest.mark.django_db


def test_serializer_retorna_participacao_com_uuids(
    definicao_polo_factory,
) -> None:
    """O contrato básico usa UUIDs para polo e edição."""
    definicao = definicao_polo_factory()

    dados = DefinicaoPoloSerializer(definicao).data

    assert dados["uuid"] == str(definicao.uuid)
    assert str(dados["polo"]) == str(definicao.polo.uuid)
    assert str(dados["edicao"]) == str(definicao.edicao.uuid)
    assert dados["total_inscritos"] == 325


def test_serializer_marca_total_e_metadados_como_somente_leitura(
    definicao_polo_factory,
) -> None:
    """Campos calculados e gerenciados não entram nos dados validados."""
    definicao = definicao_polo_factory()
    serializer = DefinicaoPoloSerializer(
        definicao,
        data={
            "polo": str(definicao.polo.uuid),
            "edicao": str(definicao.edicao.uuid),
            "tipo": TipoPolo.OFICIAL,
            "projecao_inscritos": 100,
            "total_inscritos": 999,
            "ativo": False,
        },
        partial=True,
    )

    assert serializer.is_valid(), serializer.errors
    assert "total_inscritos" not in serializer.validated_data
    assert "ativo" not in serializer.validated_data


def test_serializer_detalhamento_aninha_polo_e_edicao(
    definicao_polo_factory,
) -> None:
    """O detalhe contém o PoloSerializer e o resumo da edição."""
    definicao = definicao_polo_factory()

    dados = DefinicaoPoloDetalhamentoSerializer(definicao).data

    assert dados["polo"]["uuid"] == str(definicao.polo.uuid)
    assert dados["polo"]["codigo_eol"] == definicao.polo.codigo_eol
    assert dados["edicao"] == {
        "uuid": str(definicao.edicao.uuid),
        "nome": definicao.edicao.nome,
    }


def test_serializer_historico_retorna_edicao_com_nome(
    definicao_polo_factory,
) -> None:
    """O histórico identifica a edição por UUID e nome."""
    definicao = definicao_polo_factory()

    dados = DefinicaoPoloHistoricoSerializer(definicao).data

    assert dados["edicao"] == {
        "uuid": str(definicao.edicao.uuid),
        "nome": definicao.edicao.nome,
    }
    assert "polo" not in dados


def test_serializer_vinculacao_em_massa_exige_projecao() -> None:
    """A vinculação em massa exige a projeção."""
    serializer = VincularEmMassaSerializer(
        data={"polos": [], "edicao": "00000000-0000-0000-0000-000000000001"}
    )

    assert not serializer.is_valid()
    assert "projecao_inscritos" in serializer.errors


def test_serializer_vinculacao_em_massa_aceita_payload_valido(
    definicao_polo_factory,
) -> None:
    """O payload de vinculação em massa é validado."""
    definicao = definicao_polo_factory()
    serializer = VincularEmMassaSerializer(
        data={
            "polos": [str(definicao.polo.uuid)],
            "edicao": str(definicao.edicao.uuid),
            "projecao_inscritos": 200,
        }
    )

    assert serializer.is_valid(), serializer.errors


def test_serializer_vinculacao_em_massa_rejeita_polos_duplicados(
    definicao_polo_factory,
) -> None:
    """A vinculação em massa não aceita o mesmo polo duas vezes."""
    definicao = definicao_polo_factory()
    polo_uuid = str(definicao.polo.uuid)
    serializer = VincularEmMassaSerializer(
        data={
            "polos": [polo_uuid, polo_uuid],
            "edicao": str(definicao.edicao.uuid),
            "projecao_inscritos": 200,
        }
    )

    assert not serializer.is_valid()
    assert "não pode conter UUIDs repetidos" in str(serializer.errors)


def test_serializer_acoes_em_massa_rejeitam_uuids_duplicados(
    definicao_polo_factory,
) -> None:
    """As seleções em massa não aceitam repetição de identificadores."""
    definicao = definicao_polo_factory()
    polo_uuid = str(definicao.polo.uuid)
    edicao_uuid = str(definicao.edicao.uuid)

    tipo = AlterarTipoEmMassaSerializer(
        data=[
            {
                "polo_uuid": polo_uuid,
                "edicao": edicao_uuid,
                "tipo": TipoPolo.OFICIAL,
            },
            {
                "polo_uuid": polo_uuid,
                "edicao": edicao_uuid,
                "tipo": TipoPolo.OFICIAL,
            },
        ]
    )
    edicao = AlterarEdicaoEmMassaSerializer(
        data={
            "definicoes": [str(definicao.uuid), str(definicao.uuid)],
            "edicao_destino": edicao_uuid,
        }
    )

    assert not tipo.is_valid()
    assert not edicao.is_valid()


def test_serializer_alterar_tipo_em_massa_rejeita_lista_vazia() -> None:
    """A ação de tipo exige ao menos uma operação."""
    serializer = AlterarTipoEmMassaSerializer(data=[])

    assert not serializer.is_valid()
    assert "não pode estar vazia" in str(serializer.errors)


def test_serializer_resposta_vinculacao_em_massa(
    definicao_polo_factory,
) -> None:
    """A resposta em massa expõe criadas e ignorados."""
    definicao = definicao_polo_factory()
    dados = {
        "criadas": [DefinicaoPoloSerializer(definicao).data],
        "ignorados": [str(definicao.polo.uuid)],
    }

    serializer = VincularEmMassaResponseSerializer(data=dados)

    assert serializer.is_valid(), serializer.errors
