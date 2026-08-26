"""Testes do modelo persistido de edições."""

from datetime import date

import pytest
from django.core.exceptions import ValidationError
from freezegun import freeze_time

from apps.edicoes.constants import StatusEdicao
from apps.edicoes.models import Edicao

pytestmark = pytest.mark.django_db


def test_modelo_tem_indicadores_com_zero_por_padrao(edicao_factory) -> None:
    """Indicadores começam zerados e não são editáveis pela API/Admin."""
    edicao = edicao_factory()

    assert edicao.quantidade_inscritos == 0
    assert edicao.quantidade_atendimento_efetivo == 0
    assert edicao.quantidade_passeios == 0
    assert edicao.quantidade_apresentacoes == 0
    assert Edicao._meta.get_field("quantidade_inscritos").editable is False


def test_modelo_define_status_como_text_choices(edicao_factory) -> None:
    """O campo utiliza os três status oficiais do domínio."""
    campo = Edicao._meta.get_field("status")
    edicao = edicao_factory()

    assert campo.choices == list(StatusEdicao.choices)
    assert edicao.status == StatusEdicao.PLANEJADA


def test_modelo_rejeita_fim_da_edicao_antes_do_inicio(edicao_factory) -> None:
    """O período da edição precisa estar em ordem cronológica."""
    edicao = edicao_factory.build(
        data_inicio=date(2099, 2, 1),
        data_fim=date(2099, 1, 31),
    )

    with pytest.raises(ValidationError):
        edicao.save()


def test_modelo_rejeita_fim_das_inscricoes_apos_fim_da_edicao(
    edicao_factory,
) -> None:
    """Inscrições não podem ultrapassar o último dia da edição."""
    edicao = edicao_factory.build(
        inscricoes_fim=date(2099, 2, 1),
    )

    with pytest.raises(ValidationError):
        edicao.save()


def test_modelo_tem_uuid_e_timestamps(edicao_factory) -> None:
    """A entidade herda os campos comuns do modelo base."""
    edicao = edicao_factory()

    assert edicao.uuid is not None
    assert edicao.criado_em is not None
    assert edicao.atualizado_em is not None


def test_modelo_str_retorna_nome_da_edicao(edicao_factory) -> None:
    """A representação textual da edição utiliza seu nome."""
    edicao = edicao_factory(nome="Edição representada")

    assert str(edicao) == "Edição representada"


def test_modelo_marca_edicao_atual_como_ativa(edicao_factory) -> None:
    """Uma edição cujo período contém hoje fica ativa ao salvar."""
    with freeze_time("2099-01-15 12:00:00"):
        edicao = edicao_factory(
            data_inicio=date(2099, 1, 1),
            data_fim=date(2099, 1, 31),
        )

    assert edicao.status == StatusEdicao.ATIVA


def test_modelo_marca_edicao_passada_como_encerrada(edicao_factory) -> None:
    """Uma edição cujo último dia já passou fica encerrada ao salvar."""
    with freeze_time("2099-02-01 12:00:00"):
        edicao = edicao_factory(
            data_inicio=date(2099, 1, 1),
            data_fim=date(2099, 1, 31),
        )

    assert edicao.status == StatusEdicao.ENCERRADA
