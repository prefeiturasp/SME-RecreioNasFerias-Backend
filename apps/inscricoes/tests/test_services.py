"""Testes dos casos de uso de inscrições."""

from datetime import date
from typing import cast

import pytest
from django.core.exceptions import ValidationError
from freezegun import freeze_time

from apps.inscricoes.constants import (
    GrupoInscricao,
    StatusInscricao,
    TipoEstudante,
)
from apps.inscricoes.models import Inscricao
from apps.inscricoes.services.inscricao_service import InscricaoService
from apps.inscricoes.validators import (
    MENSAGEM_CODIGO_EOL_OBRIGATORIO,
    MENSAGEM_EOL_NAO_ENCONTRADO,
)
from apps.integracoes.eol.adapter import EolAdapter
from apps.integracoes.eol.port import EolPort
from apps.polos.constants import GestaoPolo, StatusPolo, TipoPolo

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
) -> None:
    """Traz polos ativos oficiais da edição vigente e filtra por DRE."""
    inscricao = inscricao_completa_factory()
    esperado = inscricao.polo
    outro = polo_factory(dre_codigo_eol="999999")
    definicao_polo_factory(
        polo=outro,
        edicao=inscricao.edicao,
        tipo=TipoPolo.OFICIAL,
    )
    inativo = polo_factory(dre_codigo_eol=esperado.dre_codigo_eol)
    inativo.status = StatusPolo.INATIVO
    inativo.save()
    definicao_polo_factory(
        polo=inativo,
        edicao=inscricao.edicao,
        tipo=TipoPolo.OFICIAL,
    )

    with freeze_time("2099-01-01 12:00:00"):
        resultado = InscricaoService().listar_polos_elegiveis(
            esperado.dre_codigo_eol
        )

    assert list(resultado) == [esperado]


def test_service_lista_somente_oficial_da_edicao_com_inscricoes_abertas(
    polo_factory,
    definicao_polo_factory,
    edicao_factory,
) -> None:
    """Reserva e oficial de outra edição ficam de fora da edição vigente."""
    vigente = edicao_factory(
        nome="Edição com inscrições abertas",
        data_inicio=date(2099, 6, 1),
        data_fim=date(2099, 6, 30),
        inscricoes_inicio=date(2099, 5, 1),
        inscricoes_fim=date(2099, 6, 15),
    )
    anterior = edicao_factory(
        nome="Edição anterior",
        data_inicio=date(2099, 1, 1),
        data_fim=date(2099, 1, 31),
        inscricoes_inicio=date(2098, 12, 1),
        inscricoes_fim=date(2099, 1, 31),
    )
    dre = "108200"
    oficial = polo_factory(dre_codigo_eol=dre, nome_polo="Polo Oficial")
    antigo = polo_factory(dre_codigo_eol=dre, nome_polo="Polo Antigo")
    reserva = polo_factory(dre_codigo_eol=dre, nome_polo="Polo Reserva")
    definicao_polo_factory(polo=oficial, edicao=vigente, tipo=TipoPolo.OFICIAL)
    definicao_polo_factory(polo=antigo, edicao=anterior, tipo=TipoPolo.OFICIAL)
    definicao_polo_factory(polo=reserva, edicao=vigente, tipo=TipoPolo.RESERVA)

    with freeze_time("2099-06-10 12:00:00"):
        resultado = InscricaoService().listar_polos_elegiveis(dre)

    assert list(resultado) == [oficial]


def test_service_lista_polos_oficiais_de_gestao_direta_e_parceira(
    polo_factory,
    definicao_polo_factory,
    edicao_factory,
) -> None:
    """Direta e parceira entram se o polo é oficial na edição vigente."""
    edicao = edicao_factory()
    dre = "108100"
    direta = polo_factory(
        gestao=GestaoPolo.DIRETA,
        dre_codigo_eol=dre,
        nome_polo="Polo Direta",
    )
    parceira = polo_factory(
        gestao=GestaoPolo.PARCEIRA,
        dre_codigo_eol=dre,
        nome_polo="Polo Parceira",
    )
    definicao_polo_factory(polo=direta, edicao=edicao, tipo=TipoPolo.OFICIAL)
    definicao_polo_factory(polo=parceira, edicao=edicao, tipo=TipoPolo.OFICIAL)

    with freeze_time("2099-01-15 12:00:00"):
        resultado = InscricaoService().listar_polos_elegiveis(dre)

    assert list(resultado) == [direta, parceira]


def test_service_lista_polos_oficiais_sem_periodo_nem_dre(
    polo_factory,
    definicao_polo_factory,
    edicao_factory,
) -> None:
    """Oficial entra com inscrições fechadas ou polo inativo; os demais não."""
    encerrada = edicao_factory(
        nome="Edição encerrada",
        data_inicio=date(2090, 1, 1),
        data_fim=date(2090, 1, 31),
        inscricoes_inicio=date(2089, 12, 1),
        inscricoes_fim=date(2090, 1, 31),
    )
    outra = edicao_factory(
        nome="Outra edição encerrada",
        data_inicio=date(2091, 3, 1),
        data_fim=date(2091, 3, 31),
        inscricoes_inicio=date(2091, 2, 1),
        inscricoes_fim=date(2091, 3, 31),
    )
    oficial = polo_factory(nome_polo="Polo Oficial Fechado")
    inativo = polo_factory(nome_polo="Polo Oficial Inativo")
    inativo.status = StatusPolo.INATIVO
    inativo.save()
    reserva = polo_factory(nome_polo="Polo Reserva")
    pendente = polo_factory(nome_polo="Polo Pendente")
    repetido = polo_factory(nome_polo="Polo Oficial Repetido")
    definicao_polo_factory(
        polo=oficial, edicao=encerrada, tipo=TipoPolo.OFICIAL
    )
    definicao_polo_factory(
        polo=inativo, edicao=encerrada, tipo=TipoPolo.OFICIAL
    )
    definicao_polo_factory(
        polo=reserva, edicao=encerrada, tipo=TipoPolo.RESERVA
    )
    definicao_polo_factory(
        polo=pendente, edicao=encerrada, tipo=TipoPolo.PENDENTE
    )
    definicao_polo_factory(
        polo=repetido, edicao=encerrada, tipo=TipoPolo.OFICIAL
    )
    definicao_polo_factory(polo=repetido, edicao=outra, tipo=TipoPolo.OFICIAL)

    with freeze_time("2099-06-10 12:00:00"):
        resultado = list(InscricaoService().listar_polos_oficiais())

    assert resultado == [oficial, inativo, repetido]


def test_service_respeita_os_limites_do_periodo_de_inscricoes(
    polo_factory,
    definicao_polo_factory,
    edicao_factory,
) -> None:
    """Limites das inscrições entram; o dia seguinte fica de fora."""
    edicao = edicao_factory(
        data_inicio=date(2099, 1, 1),
        data_fim=date(2099, 2, 28),
        inscricoes_inicio=date(2099, 1, 1),
        inscricoes_fim=date(2099, 1, 31),
    )
    polo = polo_factory()
    definicao_polo_factory(polo=polo, edicao=edicao, tipo=TipoPolo.OFICIAL)
    service = InscricaoService()
    dre = polo.dre_codigo_eol

    with freeze_time("2099-01-01 12:00:00"):
        assert list(service.listar_polos_elegiveis(dre)) == [polo]
    with freeze_time("2099-01-31 12:00:00"):
        assert list(service.listar_polos_elegiveis(dre)) == [polo]
    with freeze_time("2099-02-01 12:00:00"):
        assert list(service.listar_polos_elegiveis(dre)) == []


class _PortaParticipante:
    """Porta falsa que registra a consulta e devolve um resultado fixo."""

    def __init__(self, resultado: object) -> None:
        """Guarda o valor que ``consultar_participante`` vai devolver."""
        self.resultado = resultado
        self.chamadas: list[str] = []

    def consultar_participante(self, codigo_eol: str) -> object:
        """Registra o código e devolve o resultado configurado."""
        self.chamadas.append(codigo_eol)
        return self.resultado


def test_service_cria_adaptador_eol_quando_nao_injetado() -> None:
    """A integração concreta nasce só quando a porta não foi injetada."""
    service = InscricaoService()

    assert service._eol is None
    assert isinstance(service.eol, EolAdapter)
    assert service._eol is service.eol


def test_service_consulta_participante_encontrado() -> None:
    """Porta com participante devolve o mesmo objeto."""
    marca = object()
    porta = _PortaParticipante(marca)
    service = InscricaoService(eol=cast(EolPort, porta))

    obtido = service.consultar_participante_por_eol("6034178")

    assert obtido is marca
    assert porta.chamadas == ["6034178"]


def test_service_recusa_codigo_eol_em_branco() -> None:
    """Código vazio ou só com espaços não chama a porta."""
    porta = _PortaParticipante(object())
    service = InscricaoService(eol=cast(EolPort, porta))

    with pytest.raises(ValidationError) as vazio:
        service.consultar_participante_por_eol("   ")
    with pytest.raises(ValidationError) as ausente:
        service.consultar_participante_por_eol(None)

    assert vazio.value.message_dict["codigo_eol"] == [
        MENSAGEM_CODIGO_EOL_OBRIGATORIO
    ]
    assert ausente.value.message_dict["codigo_eol"] == [
        MENSAGEM_CODIGO_EOL_OBRIGATORIO
    ]
    assert porta.chamadas == []


def test_service_recusa_eol_nao_encontrado() -> None:
    """Lista vazia da porta vira a mensagem da história."""
    porta = _PortaParticipante(None)
    service = InscricaoService(eol=cast(EolPort, porta))

    with pytest.raises(ValidationError) as contexto:
        service.consultar_participante_por_eol("000")

    assert contexto.value.message_dict["codigo_eol"] == [
        MENSAGEM_EOL_NAO_ENCONTRADO
    ]
    assert porta.chamadas == ["000"]
