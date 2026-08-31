"""Testes dos casos de uso do domínio de edições."""

from datetime import date

import pytest
from django.core.exceptions import ValidationError
from freezegun import freeze_time

from apps.edicoes.constants import StatusEdicao
from apps.edicoes.models import Edicao
from apps.edicoes.services.edicao_service import EdicaoService
from apps.edicoes.validators import MENSAGEM_EDICAO_ENCERRADA

pytestmark = pytest.mark.django_db


def test_service_cria_edicao_sem_permitir_status_de_entrada() -> None:
    """A criação controla o status e não aceita status arbitrário."""
    edicao = EdicaoService().criar(
        nome="Edição planejada",
        data_inicio=date(2099, 1, 1),
        data_fim=date(2099, 1, 31),
        inscricoes_inicio=date(2098, 12, 1),
        inscricoes_fim=date(2099, 1, 31),
        status=StatusEdicao.ENCERRADA,
    )

    assert edicao.status == StatusEdicao.PLANEJADA


def test_service_atualiza_edicao(edicao_factory) -> None:
    """A atualização altera campos permitidos enquanto não encerrada."""
    edicao = edicao_factory(nome="Nome original")

    atualizada = EdicaoService().atualizar(
        edicao,
        nome="Nome atualizado",
    )

    assert atualizada.nome == "Nome atualizado"
    assert Edicao.objects.get(pk=edicao.pk).nome == "Nome atualizado"


def test_service_nao_atualiza_edicao_encerrada(edicao_factory) -> None:
    """A alteração de uma edição encerrada é rejeitada."""
    with freeze_time("2090-02-01 12:00:00"):
        edicao = edicao_factory(
            data_inicio=date(2090, 1, 1),
            data_fim=date(2090, 1, 31),
            inscricoes_inicio=date(2089, 12, 1),
            inscricoes_fim=date(2090, 1, 31),
        )
        Edicao.objects.filter(pk=edicao.pk).update(
            status=StatusEdicao.ENCERRADA
        )

        with pytest.raises(ValidationError) as contexto:
            EdicaoService().atualizar(edicao, nome="Tentativa")

    assert MENSAGEM_EDICAO_ENCERRADA in str(contexto.value)


def test_service_exclui_edicao_planejada(edicao_factory) -> None:
    """Uma edição planejada pode ser excluída."""
    edicao = edicao_factory()

    EdicaoService().excluir(edicao)

    assert not Edicao.objects.filter(pk=edicao.pk).exists()


def test_service_nao_exclui_edicao_encerrada(edicao_factory) -> None:
    """A exclusão também é bloqueada para edição encerrada."""
    with freeze_time("2090-02-01 12:00:00"):
        edicao = edicao_factory(
            data_inicio=date(2090, 1, 1),
            data_fim=date(2090, 1, 31),
            inscricoes_inicio=date(2089, 12, 1),
            inscricoes_fim=date(2090, 1, 31),
        )
        Edicao.objects.filter(pk=edicao.pk).update(
            status=StatusEdicao.ENCERRADA
        )

        with pytest.raises(ValidationError) as contexto:
            EdicaoService().excluir(edicao)

    assert MENSAGEM_EDICAO_ENCERRADA in str(contexto.value)
