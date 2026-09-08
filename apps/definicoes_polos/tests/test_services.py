"""Testes dos casos de uso de definições de polos."""

from datetime import date, timedelta

import pytest
from django.core.exceptions import ValidationError

from apps.definicoes_polos.constants import TipoPolo
from apps.definicoes_polos.models import DefinicaoPolo
from apps.definicoes_polos.services.definicao_polo_service import (
    DefinicaoPoloService,
)

pytestmark = pytest.mark.django_db


def _criar_edicao(edicao_factory, numero: int):
    """Cria uma edição com período isolado das demais."""
    inicio = date(2099, 1, 1) + timedelta(days=numero * 40)
    return edicao_factory(
        nome=f"Edição de Serviço {numero}",
        data_inicio=inicio,
        data_fim=inicio + timedelta(days=20),
        inscricoes_inicio=inicio - timedelta(days=10),
        inscricoes_fim=inicio + timedelta(days=20),
    )


def test_service_lista_e_obtem_participacoes(definicao_polo_factory) -> None:
    """O service lista e obtém participações com relações carregadas."""
    definicao = definicao_polo_factory()
    service = DefinicaoPoloService()

    assert list(service.listar_participacoes()) == [definicao]
    assert list(service.listar_participacoes(polo=definicao.polo)) == [
        definicao
    ]
    assert list(service.listar_participacoes(edicao=definicao.edicao)) == [
        definicao
    ]
    assert service.obter_participacao(definicao.uuid) == definicao


def test_service_vincula_participacao_com_defaults(
    polo_factory,
    edicao_factory,
) -> None:
    """A vinculação nasce pendente e calcula o total."""
    polo = polo_factory()
    edicao = _criar_edicao(edicao_factory, 1)

    definicao = DefinicaoPoloService().vincular(
        polo,
        edicao,
        175,
        ponto_focal_nome="Ollyver",
        ponto_focal_telefone="11999999999",
        ponto_focal_email="ollyver@example.com",
    )

    assert definicao.tipo == TipoPolo.PENDENTE
    assert definicao.total_inscritos == 227
    assert definicao.ponto_focal_nome == "Ollyver"


def test_service_atualiza_participacao_e_ignora_campos_protegidos(
    definicao_polo_factory,
) -> None:
    """A atualização recalcula total e ignora total, ativo e UUID."""
    definicao = definicao_polo_factory()
    uuid_original = definicao.uuid

    atualizada = DefinicaoPoloService().atualizar(
        definicao,
        projecao_inscritos=100,
        ponto_focal_nome="Novo ponto focal",
        total_inscritos=999,
        ativo=False,
        uuid="outro",
    )

    assert atualizada.uuid == uuid_original
    assert atualizada.total_inscritos == 130
    assert atualizada.ponto_focal_nome == "Novo ponto focal"
    assert atualizada.ativo is True


def test_service_atualiza_capacidade_e_ponto_focal(
    definicao_polo_factory,
) -> None:
    """O caso de uso específico atualiza apenas seus campos permitidos."""
    definicao = definicao_polo_factory()

    atualizada = DefinicaoPoloService().atualizar_capacidade_e_ponto_focal(
        definicao,
        projecao_inscritos=175,
        ponto_focal_nome="Ponto atualizado",
        ponto_focal_telefone="11111111111",
        ponto_focal_email="atualizado@example.com",
        tipo=TipoPolo.OFICIAL,
    )

    assert atualizada.projecao_inscritos == 175
    assert atualizada.total_inscritos == 227
    assert atualizada.ponto_focal_nome == "Ponto atualizado"
    assert atualizada.tipo != TipoPolo.OFICIAL


def test_service_altera_tipo_e_exclui(definicao_polo_factory) -> None:
    """O service altera tipo e remove a participação."""
    definicao = definicao_polo_factory()
    service = DefinicaoPoloService()

    atualizada = service.alterar_tipo(definicao, TipoPolo.RESERVA)
    assert atualizada.tipo == TipoPolo.RESERVA

    service.excluir(atualizada)
    assert not DefinicaoPolo.objects.filter(pk=definicao.pk).exists()


def test_service_vincula_em_massa_cria_e_ignora_repetidos(
    polo_factory,
    edicao_factory,
    definicao_polo_factory,
) -> None:
    """A vinculação em massa separa criados e já vinculados."""
    primeiro = polo_factory()
    segundo = polo_factory()
    edicao = _criar_edicao(edicao_factory, 2)
    existente = definicao_polo_factory(polo=primeiro, edicao=edicao)

    resultado = DefinicaoPoloService().vincular_em_massa(
        [primeiro, segundo], edicao, 200
    )

    assert resultado["ignorados"] == [primeiro]
    assert [item.polo for item in resultado["criadas"]] == [segundo]
    assert existente.pk is not None


def test_service_define_tipo_em_massa_por_polo_e_edicao(
    definicao_polo_factory,
    polo_factory,
    edicao_factory,
) -> None:
    """A alteração em massa atualiza todas as participações encontradas."""
    edicao = _criar_edicao(edicao_factory, 3)
    primeiro = definicao_polo_factory(edicao=edicao)
    segundo = definicao_polo_factory(edicao=edicao, polo=polo_factory())

    resultado = DefinicaoPoloService().alterar_tipo_em_massa(
        [
            {
                "polo": primeiro.polo,
                "edicao": primeiro.edicao,
                "tipo": TipoPolo.OFICIAL,
            },
            {
                "polo": segundo.polo,
                "edicao": segundo.edicao,
                "tipo": TipoPolo.OFICIAL,
            },
        ]
    )

    assert len(resultado["alterados"]) == 2
    assert all(
        item.tipo == TipoPolo.OFICIAL for item in resultado["alterados"]
    )


def test_service_define_tipo_em_massa_ignora_polo_sem_edicao(
    definicao_polo_factory,
    polo_factory,
) -> None:
    """A definição em massa ignora operações sem edição."""
    definicao = definicao_polo_factory()
    ausente = polo_factory()

    resultado = DefinicaoPoloService().alterar_tipo_em_massa(
        [
            {
                "polo": definicao.polo,
                "edicao": definicao.edicao,
                "tipo": TipoPolo.RESERVA,
            },
            {"polo": ausente, "edicao": None, "tipo": TipoPolo.RESERVA},
        ]
    )

    assert resultado["alterados"] == [definicao]
    assert resultado["ignorados"] == [
        {
            "polo_uuid": ausente.uuid,
            "motivo": "Polo sem vínculo com edição.",
        }
    ]
    assert (
        "Houve polos que não tiveram o tipo alterado"
        in resultado["mensagem"]
    )


def test_service_alterar_tipo_em_massa_cria_vinculo_ausente(
    polo_factory,
    edicao_factory,
) -> None:
    """A ação cria a participação ausente antes de definir seu tipo."""
    polo = polo_factory()
    edicao = _criar_edicao(edicao_factory, 31)

    resultado = DefinicaoPoloService().alterar_tipo_em_massa(
        [{"polo": polo, "edicao": edicao, "tipo": TipoPolo.RESERVA}]
    )

    definicao = resultado["alterados"][0]
    assert definicao.polo == polo
    assert definicao.edicao == edicao
    assert definicao.tipo == TipoPolo.RESERVA
    assert definicao.projecao_inscritos == 0
    assert definicao.total_inscritos == 0


def test_service_alterar_edicao_em_massa(
    definicao_polo_factory,
    edicao_factory,
) -> None:
    """A edição de destino é aplicada às definições selecionadas."""
    definicao = definicao_polo_factory()
    destino = _criar_edicao(edicao_factory, 4)

    resultado = DefinicaoPoloService().alterar_edicao_em_massa(
        [definicao], destino
    )

    assert resultado[0].edicao == destino
    assert DefinicaoPolo.objects.get(pk=definicao.pk).edicao == destino


def test_service_alterar_edicao_em_massa_rejeita_conflito(
    definicao_polo_factory,
    edicao_factory,
) -> None:
    """O destino não pode já conter o mesmo polo."""
    destino = _criar_edicao(edicao_factory, 5)
    origem = definicao_polo_factory()
    definicao_polo_factory(polo=origem.polo, edicao=destino)

    def _executar() -> None:
        DefinicaoPoloService().alterar_edicao_em_massa([origem], destino)

    with pytest.raises(ValidationError):
        _executar()


def test_service_alterar_edicao_em_massa_rejeita_mesmo_polo_duplicado(
    definicao_polo_factory,
    edicao_factory,
) -> None:
    """Não move duas participações do mesmo polo para um único destino."""
    origem_um = definicao_polo_factory()
    origem_dois = definicao_polo_factory(
        polo=origem_um.polo,
        edicao=_criar_edicao(edicao_factory, 51),
    )
    destino = _criar_edicao(edicao_factory, 52)

    def _executar() -> None:
        DefinicaoPoloService().alterar_edicao_em_massa(
            [origem_um, origem_dois], destino
        )

    with pytest.raises(ValidationError) as contexto:
        _executar()

    assert "mais de uma definição do mesmo polo" in str(contexto.value)


def test_service_lista_polos_sem_edicao_com_ultima_participacao(
    polo_factory,
    edicao_factory,
    definicao_polo_factory,
) -> None:
    """Sem filtro, retorna todos e anota a participação mais recente."""
    polo = polo_factory(nome_polo="Polo com histórico")
    antigo = _criar_edicao(edicao_factory, 6)
    recente = _criar_edicao(edicao_factory, 7)
    definicao_polo_factory(polo=polo, edicao=antigo, tipo=TipoPolo.RESERVA)
    atual = definicao_polo_factory(
        polo=polo,
        edicao=recente,
        tipo=TipoPolo.OFICIAL,
        projecao_inscritos=175,
    )
    sem_vinculo = polo_factory(nome_polo="Polo sem vínculo")
    sem_vinculo.tipo = TipoPolo.RESERVA
    sem_vinculo.save()

    resultado = list(DefinicaoPoloService().listar_polos_com_definicao())
    por_nome = {item.nome_polo: item for item in resultado}

    assert por_nome[polo.nome_polo].definicao_uuid == atual.uuid
    assert por_nome[polo.nome_polo].edicao_uuid == recente.uuid
    assert por_nome[polo.nome_polo].tipo_polo_edicao == TipoPolo.OFICIAL
    assert por_nome[polo.nome_polo].total_inscritos_edicao == 227
    assert por_nome[sem_vinculo.nome_polo].definicao_uuid is None
    assert por_nome[sem_vinculo.nome_polo].tipo_polo_edicao == TipoPolo.RESERVA


def test_service_lista_polos_filtrada_por_edicao_e_demais_filtros(
    polo_factory,
    edicao_factory,
    definicao_polo_factory,
) -> None:
    """Com edição, aplica INNER JOIN e filtros do cadastro do polo."""
    edicao = _criar_edicao(edicao_factory, 8)
    esperado = polo_factory(
        nome_polo="Polo buscado",
        codigo_eol="019999",
        dre_codigo_eol="108100",
        tipo_ue="EMEF",
        gestao="direta",
    )
    definicao_polo_factory(
        polo=esperado,
        edicao=edicao,
        tipo=TipoPolo.OFICIAL,
        projecao_inscritos=175,
    )
    polo_factory(nome_polo="Sem participação")

    resultado = list(
        DefinicaoPoloService().listar_polos_com_definicao(
            dre_codigos_eol=[" 108100 "],
            tipo_ue=" EMEF ",
            busca=" buscado ",
            gestao=" direta ",
            edicao=edicao,
            tipo_polo=TipoPolo.OFICIAL,
        )
    )

    assert [item.nome_polo for item in resultado] == [esperado.nome_polo]
    assert resultado[0].projecao_inscritos_edicao == 175
    assert resultado[0].edicao_uuid == edicao.uuid


def test_service_lista_polos_ignora_filtros_vazios(polo_factory) -> None:
    """Filtros vazios não restringem a listagem."""
    primeiro = polo_factory()
    segundo = polo_factory()

    resultado = DefinicaoPoloService().listar_polos_com_definicao(
        dre_codigos_eol=[" ", ""], tipo_ue=" ", busca=" ", gestao=" "
    )

    assert set(resultado) == {primeiro, segundo}
