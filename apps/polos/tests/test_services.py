"""Testes dos casos de uso do domínio de polos."""

import pytest

from apps.integracoes.eol.adapter import EolAdapter
from apps.integracoes.eol.port import DreEol, TipoEscolaEol
from apps.polos.constants import StatusPolo, TipoPolo
from apps.polos.models import Polo
from apps.polos.services.polo_service import PoloService

pytestmark = pytest.mark.django_db


def test_service_cria_polo_com_defaults_de_dominio(polo_factory) -> None:
    """A criação ignora tipo e status recebidos e aplica os defaults."""
    dados = {
        "codigo_eol": "019362",
        "nome_polo": "Polo criado pelo serviço",
        "nome_osc": "OSC do polo",
        "dre_nome": "DRE de teste",
        "dre_codigo_eol": "108202",
        "tipo": TipoPolo.OFICIAL,
        "status": StatusPolo.INATIVO,
        "tipo_ue": "EMEI",
        "quantidade_maxima_alunos": 150,
        "cep": "01001000",
        "tipo_logradouro": "Rua",
        "logradouro": "Principal",
        "bairro": "Centro",
        "numero": "10",
        "nome_gestor": "Gestor",
        "email": "servico@example.com",
        "telefone": "1130000000",
    }

    polo = PoloService().criar(**dados)

    assert polo.tipo == TipoPolo.PENDENTE
    assert polo.status == StatusPolo.ATIVO
    assert polo.gestao == "parceira"
    assert polo.complemento == ""
    assert Polo.objects.filter(pk=polo.pk).exists()


def test_service_lista_tipos_e_dres_pela_porta_eol() -> None:
    """O serviço delega os catálogos à porta EOL injetada."""
    tipos = (TipoEscolaEol(codigo=1, descricao_sigla="EMEF"),)
    dres = (
        DreEol(
            codigo_dre="108100",
            nome_dre="DRE Butantã",
            sigla_dre="DRE - BT",
        ),
    )

    class FakeEol:
        """Porta EOL mínima para o teste de delegação."""

        def listar_tipos_escola(self):
            return tipos

        def listar_dres(self):
            return dres

    service = PoloService(eol=FakeEol())

    assert service.listar_tipos_escola() == tipos
    assert service.listar_dres() == dres


def test_service_cria_adapter_eol_sob_demanda() -> None:
    """A integração padrão só é criada quando efetivamente utilizada."""
    service = PoloService()

    assert service._eol is None
    assert isinstance(service.eol, EolAdapter)
    assert service._eol is service.eol


def test_service_lista_e_obtem_polos(polo_factory) -> None:
    """O serviço lista e recupera polos pelo UUID público."""
    polo = polo_factory()

    assert polo in PoloService().listar()
    assert PoloService().obter(polo.uuid) == polo


def test_service_filtra_por_dre(polo_factory) -> None:
    """O filtro de DRE usa o código EOL com comparação exata."""
    primeiro = polo_factory(dre_codigo_eol="108100")
    polo_factory(dre_codigo_eol="108200")

    resultado = PoloService().listar(dre_codigo_eol=" 108100 ")

    assert list(resultado) == [primeiro]


def test_service_filtra_por_tipo_de_ue(polo_factory) -> None:
    """O filtro de tipo de UE usa a sigla com comparação exata."""
    primeiro = polo_factory(tipo_ue="EMEF")
    polo_factory(tipo_ue="EMEI")

    resultado = PoloService().listar(tipo_ue=" EMEF ")

    assert list(resultado) == [primeiro]


def test_service_busca_no_nome_do_polo_ou_da_osc(polo_factory) -> None:
    """A busca textual procura em nome do Polo ou nome da OSC."""
    polo_nome = polo_factory(nome_polo="Polo Mario")
    polo_osc = polo_factory(
        nome_polo="Polo Diferente",
        nome_osc="OSC Mario",
    )
    polo_factory(nome_polo="Polo Sem Correspondência")

    resultado = PoloService().listar(busca="  mario ")

    assert set(resultado) == {polo_nome, polo_osc}


def test_service_combina_filtros_e_ignora_filtros_vazios(
    polo_factory,
) -> None:
    """Filtros diferentes usam AND e parâmetros vazios são ignorados."""
    esperado = polo_factory(
        dre_codigo_eol="108100",
        tipo_ue="EMEF",
        nome_polo="Polo Mario",
    )
    polo_factory(
        dre_codigo_eol="108100",
        tipo_ue="EMEI",
        nome_polo="Polo Mario EMEI",
    )
    polo_factory(
        dre_codigo_eol="108200",
        tipo_ue="EMEF",
        nome_polo="Polo Mario Outra DRE",
    )

    resultado = PoloService().listar(
        dre_codigo_eol="108100",
        tipo_ue="EMEF",
        busca="Mario",
    )
    todos = PoloService().listar(
        dre_codigo_eol=" ",
        tipo_ue="",
        busca=" ",
    )

    assert list(resultado) == [esperado]
    assert todos.count() == 3


def test_service_atualiza_polo(polo_factory) -> None:
    """A atualização altera campos e reaplica as validações."""
    polo = polo_factory(nome_polo="Nome original")

    atualizada = PoloService().atualizar(
        polo,
        nome_polo="Nome atualizado",
        status=StatusPolo.INATIVO,
        ativo=False,
    )

    assert atualizada.nome_polo == "Nome atualizado"
    assert atualizada.status == StatusPolo.INATIVO
    assert atualizada.ativo is True
    assert Polo.objects.get(pk=polo.pk).nome_polo == "Nome atualizado"


def test_service_exclui_polo(polo_factory) -> None:
    """Polos podem ser excluídos pelo serviço."""
    polo = polo_factory()

    PoloService().excluir(polo)

    assert not Polo.objects.filter(pk=polo.pk).exists()
