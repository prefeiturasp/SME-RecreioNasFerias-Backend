"""Testes dos casos de uso de inscrições."""

import pytest

from apps.inscricoes.constants import (
    GrupoInscricao,
    StatusInscricao,
    TipoEstudante,
)
from apps.inscricoes.models import Inscricao
from apps.inscricoes.services.inscricao_service import InscricaoService
from apps.polos.constants import StatusPolo

pytestmark = pytest.mark.django_db


def test_service_lista_obtem_e_filtra_inscricoes(
    inscricao_completa_factory,
) -> None:
    """O serviço lista, obtém e combina filtros da tela."""
    esperado = inscricao_completa_factory(
        nome_participante="Alice Teste",
        codigo_eol="1234567",
        cpf="11111111111",
    )
    inscricao_completa_factory(
        edicao=esperado.edicao,
        nome_participante="Outro participante",
        codigo_eol="7654321",
        cpf="22222222222",
    )
    service = InscricaoService()

    assert list(service.listar()) == [
        Inscricao.objects.get(nome_participante="Outro participante"),
        esperado,
    ]
    assert list(
        service.listar(
            tipo_estudante=TipoEstudante.ESTUDANTE_EXTERNO,
            polo=esperado.polo.uuid,
            codigo_eol=" 1234567 ",
            cpf="111111",
            nome_participante="alice",
            grupo=GrupoInscricao.QUATRO_A_14_ANOS,
            status=StatusInscricao.COMPLETA,
        )
    ) == [esperado]
    assert service.obter(esperado.uuid) == esperado


def test_service_cria_inscricao_com_status_rascunho(inscricao_factory) -> None:
    """A criação delega ao modelo e permite rascunhos."""
    inscricao = InscricaoService().criar(
        tipo_estudante=TipoEstudante.ESTUDANTE_EXTERNO,
        grupo=GrupoInscricao.QUATRO_A_14_ANOS,
    )

    assert inscricao.pk is not None
    assert inscricao.status == StatusInscricao.RASCUNHO
    assert Inscricao.objects.filter(pk=inscricao.pk).exists()


def test_service_atualiza_e_ignora_campos_protegidos(
    inscricao_factory,
) -> None:
    """A atualização ignora UUID, status e ativo enviados pelo cliente."""
    inscricao = inscricao_factory(nome_participante="Antes")
    uuid_original = inscricao.uuid

    atualizada = InscricaoService().atualizar(
        inscricao,
        nome_participante="Depois",
        uuid="00000000-0000-0000-0000-000000000000",
        status=StatusInscricao.COMPLETA,
        ativo=False,
    )

    assert atualizada.uuid == uuid_original
    assert atualizada.nome_participante == "Depois"
    assert atualizada.status == StatusInscricao.RASCUNHO
    assert atualizada.ativo is True


def test_service_cancela_e_reativa_recalculando_status(
    inscricao_completa_factory,
) -> None:
    """Cancelamento é manual e reativação recalcula a completude."""
    inscricao = inscricao_completa_factory()
    service = InscricaoService()

    cancelada = service.cancelar(inscricao)
    assert cancelada.status == StatusInscricao.CANCELADA

    cancelada.tipo_logradouro = ""
    cancelada.save()
    assert cancelada.status == StatusInscricao.CANCELADA

    reativada = service.reativar(cancelada)
    assert reativada.status == StatusInscricao.RASCUNHO


def test_service_exclui_inscricao(inscricao_factory) -> None:
    """O serviço pode excluir uma inscrição."""
    inscricao = inscricao_factory()

    inscricao.delete()

    assert not Inscricao.objects.filter(pk=inscricao.pk).exists()


def test_service_lista_polos_elegiveis_filtra_dre(
    inscricao_completa_factory,
    polo_factory,
    definicao_polo_factory,
    edicao_factory,
) -> None:
    """A consulta traz polos ativos oficiais e filtra por DRE."""
    inscricao = inscricao_completa_factory()
    esperado = inscricao.polo
    outro = polo_factory(dre_codigo_eol="999999")
    definicao_polo_factory(
        polo=outro,
        edicao=inscricao.edicao,
        tipo="oficial",
    )
    inativo = polo_factory(status=StatusPolo.INATIVO)
    definicao_polo_factory(
        polo=inativo,
        edicao=inscricao.edicao,
        tipo="oficial",
    )

    resultado = InscricaoService().listar_polos_elegiveis(
        esperado.dre_codigo_eol
    )

    assert list(resultado) == [esperado]
