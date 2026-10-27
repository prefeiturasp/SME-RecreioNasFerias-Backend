"""Testes das transições automáticas de status."""

from datetime import date

import pytest
from freezegun import freeze_time

from apps.edicoes.constants import StatusEdicao
from apps.edicoes.services.edicao_service import EdicaoService

pytestmark = pytest.mark.django_db


def test_edicao_futura_fica_planejada(edicao_factory) -> None:
    """Antes do início do período de inscrições, a edição permanece planejada."""
    with freeze_time("2098-12-31 12:00:00"):
        edicao = edicao_factory(
            inscricoes_inicio=date(2099, 1, 1),
            inscricoes_fim=date(2099, 1, 31),
        )

    assert edicao.status == StatusEdicao.PLANEJADA


def test_edicao_fica_ativa_no_primeiro_dia(edicao_factory) -> None:
    """O primeiro dia da edição já pertence ao período ativo."""
    with freeze_time("2099-01-01 12:00:00"):
        edicao = edicao_factory(
            data_inicio=date(2099, 1, 1),
            data_fim=date(2099, 1, 31),
        )

    assert edicao.status == StatusEdicao.ATIVA


def test_edicao_fica_ativa_no_ultimo_dia(edicao_factory) -> None:
    """O último dia da edição ainda pertence ao período ativo."""
    with freeze_time("2099-01-31 12:00:00"):
        edicao = edicao_factory(
            data_inicio=date(2099, 1, 1),
            data_fim=date(2099, 1, 31),
        )

    assert edicao.status == StatusEdicao.ATIVA


def test_edicao_fica_encerrada_no_dia_seguinte(edicao_factory) -> None:
    """No dia seguinte ao fim, a edição fica encerrada."""
    with freeze_time("2099-02-01 12:00:00"):
        edicao = edicao_factory(
            data_inicio=date(2099, 1, 1),
            data_fim=date(2099, 1, 31),
        )

    assert edicao.status == StatusEdicao.ENCERRADA


def test_consulta_sincroniza_status_sem_salvar_individualmente(
    edicao_factory,
) -> None:
    """A consulta atualiza status de registros antigos pela service."""
    with freeze_time("2098-12-31 12:00:00"):
        edicao = edicao_factory(
            data_inicio=date(2099, 1, 1),
            data_fim=date(2099, 1, 31),
        )

    with freeze_time("2099-01-01 12:00:00"):
        encontrada = EdicaoService().obter(edicao.uuid)

    assert encontrada.status == StatusEdicao.ATIVA


def test_edicao_vigente_permanece_ativa_apos_fim_das_inscricoes(
    edicao_factory,
) -> None:
    """O fim das inscrições não encerra a edição em andamento."""
    with freeze_time("2099-01-20 12:00:00"):
        edicao = edicao_factory(
            data_inicio=date(2099, 1, 1),
            data_fim=date(2099, 1, 31),
            inscricoes_inicio=date(2098, 12, 1),
            inscricoes_fim=date(2099, 1, 10),
        )

        EdicaoService.sincronizar_status()
        edicao.refresh_from_db()

    assert edicao.status == StatusEdicao.ATIVA


def test_edicao_fica_encerrada_no_dia_seguinte_ao_fim_da_edicao(
    edicao_factory,
) -> None:
    """Após data_fim, a edição fica encerrada."""
    with freeze_time("2099-02-01 12:00:00"):
        edicao = edicao_factory(
            data_inicio=date(2099, 1, 1),
            data_fim=date(2099, 1, 31),
            inscricoes_inicio=date(2098, 12, 1),
            inscricoes_fim=date(2099, 1, 10),
        )

    assert edicao.status == StatusEdicao.ENCERRADA
