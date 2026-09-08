"""Testes dos casos de uso do domínio de polos."""

import pytest
from freezegun import freeze_time

from apps.integracoes.eol.adapter import EolAdapter
from apps.integracoes.eol.port import (
    DreEol,
    TipoEscolaEol,
    UnidadeEol,
    UnidadeRecreioEol,
)
from apps.polos.constants import (
    MOTIVO_JA_EXECUTADA_HOJE,
    GestaoPolo,
    StatusPolo,
    TipoPolo,
)
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


def _unidade_eol(
    codigo: str,
    nome: str = "ESCOLA",
    *,
    sigla: str = "EMEF",
    dre: str = "DRE TESTE",
    codigo_dre: str = "108100",
) -> UnidadeEol:
    """Monta uma unidade do catálogo bruto para os testes."""
    return UnidadeEol(
        codigo_eol=codigo,
        nome_escola=nome,
        sigla_tipo_escola=sigla,
        nome_dre=dre,
        sigla_dre=dre,
        codigo_dre=codigo_dre,
    )


def _unidade_recreio(
    codigo: str,
    nome: str = "ESCOLA",
    **extras: str,
) -> UnidadeRecreioEol:
    """Monta uma unidade enriquecida pronta para persistência."""
    return UnidadeRecreioEol(
        codigo_eol=codigo,
        nome_escola=nome,
        sigla_tipo_escola=extras.get("sigla_tipo_escola", "EMEF"),
        nome_dre=extras.get("nome_dre", "DRE TESTE"),
        sigla_dre=extras.get("sigla_dre", "DRE TESTE"),
        codigo_dre=extras.get("codigo_dre", "108100"),
        email=extras.get("email", "escola@educacao.sp.gov.br"),
        telefone=extras.get("telefone", "1133334444"),
        cep=extras.get("cep", "01234-567"),
        tipo_logradouro=extras.get("tipo_logradouro", "Rua"),
        logradouro=extras.get("logradouro", "das Flores"),
        bairro=extras.get("bairro", "Centro"),
        numero=extras.get("numero", "10"),
        complemento=extras.get("complemento", ""),
        nome_diretor=extras.get("nome_diretor", "Diretor Teste"),
    )


class FakeEolPopular:
    """Porta EOL controlada para os testes de população."""

    def __init__(
        self,
        unidades: tuple[UnidadeEol, ...],
        enriquecidas: tuple[UnidadeRecreioEol, ...] | None = None,
    ) -> None:
        """Guarda o catálogo e o resultado do enriquecimento."""
        self.unidades = unidades
        self.enriquecidas = enriquecidas or ()
        self.enriquecer_chamadas: list[tuple[UnidadeEol, ...]] = []

    def listar_todas_unidades(self) -> tuple[UnidadeEol, ...]:
        """Devolve o catálogo configurado."""
        return self.unidades

    def filtrar_unidades_recreio(
        self,
        unidades: tuple[UnidadeEol, ...],
    ) -> tuple[UnidadeEol, ...]:
        """Repassa as unidades já elegíveis do teste."""
        return unidades

    def enriquecer_unidades(
        self,
        unidades,
    ) -> tuple[UnidadeRecreioEol, ...]:
        """Devolve o lote enriquecido correspondente aos códigos pedidos."""
        lote = tuple(unidades)
        self.enriquecer_chamadas.append(lote)
        por_eol = {item.codigo_eol: item for item in self.enriquecidas}
        return tuple(
            por_eol[unidade.codigo_eol]
            for unidade in lote
            if unidade.codigo_eol in por_eol
        )


def test_service_popula_polos_diretos_novos() -> None:
    """Unidades novas nascem com gestão direta e endereço separado."""
    unidades = (
        _unidade_eol("019241", "ESCOLA A"),
        _unidade_eol("019242", "ESCOLA B"),
    )
    enriquecidas = (
        _unidade_recreio("019241", "ESCOLA A", complemento="Bloco B"),
        _unidade_recreio("019242", "ESCOLA B"),
    )
    fake = FakeEolPopular(unidades, enriquecidas)

    resultado = PoloService(eol=fake).popular_unidades_diretas()

    assert resultado.executada is True
    assert resultado.total_consultados == 2
    assert resultado.total_novos == 2
    assert resultado.total_ja_existentes == 0
    polo = Polo.objects.get(codigo_eol="019241")
    assert polo.gestao == GestaoPolo.DIRETA
    assert polo.tipo == TipoPolo.PENDENTE
    assert polo.status == StatusPolo.ATIVO
    assert polo.nome_gestor == "Diretor Teste"
    assert polo.tipo_logradouro == "Rua"
    assert polo.logradouro == "das Flores"
    assert polo.bairro == "Centro"
    assert polo.numero == "10"
    assert polo.complemento == "Bloco B"
    assert polo.quantidade_maxima_alunos == 1
    assert len(fake.enriquecer_chamadas) == 1


def test_service_nao_duplica_polo_direto_existente(polo_factory) -> None:
    """O diff ignora códigos EOL já salvos como gestão direta."""
    polo_factory(
        gestao=GestaoPolo.DIRETA,
        codigo_eol="019241",
        nome_polo="ESCOLA A",
    )
    unidades = (
        _unidade_eol("019241", "ESCOLA A"),
        _unidade_eol("019242", "ESCOLA B"),
    )
    fake = FakeEolPopular(
        unidades,
        (_unidade_recreio("019242", "ESCOLA B"),),
    )

    resultado = PoloService(eol=fake).popular_unidades_diretas()

    assert resultado.total_consultados == 2
    assert resultado.total_novos == 1
    assert resultado.total_ja_existentes == 1
    assert Polo.objects.filter(gestao=GestaoPolo.DIRETA).count() == 2
    assert fake.enriquecer_chamadas[0][0].codigo_eol == "019242"


def test_service_nao_trata_polo_parceiro_como_existente(
    polo_factory,
) -> None:
    """O diff considera apenas polos de gestão direta."""
    polo_factory(gestao=GestaoPolo.PARCEIRA, nome_polo="ESCOLA PARCEIRA")
    fake = FakeEolPopular(
        (_unidade_eol("019241", "ESCOLA DIRETA A"),),
        (_unidade_recreio("019241", "ESCOLA DIRETA A"),),
    )

    resultado = PoloService(eol=fake).popular_unidades_diretas()

    assert resultado.total_novos == 1
    assert Polo.objects.filter(gestao=GestaoPolo.DIRETA).count() == 1
    assert Polo.objects.get(codigo_eol="019241").nome_polo == "ESCOLA DIRETA A"


def test_service_ignora_segunda_populacao_no_mesmo_dia() -> None:
    """A carga automática roda no máximo uma vez por dia."""
    fake = FakeEolPopular(
        (_unidade_eol("019241", "ESCOLA A"),),
        (_unidade_recreio("019241", "ESCOLA A"),),
    )
    service = PoloService(eol=fake)

    primeiro = service.popular_unidades_diretas()
    segundo = service.popular_unidades_diretas()

    assert primeiro.executada is True
    assert primeiro.total_novos == 1
    assert segundo.executada is False
    assert segundo.motivo_ignorada == MOTIVO_JA_EXECUTADA_HOJE
    assert segundo.total_consultados == 0


def test_service_permite_popular_no_dia_seguinte() -> None:
    """No dia seguinte a carga volta a consultar a EOL."""
    fake = FakeEolPopular(
        (_unidade_eol("019241", "ESCOLA A"),),
        (_unidade_recreio("019241", "ESCOLA A"),),
    )

    with freeze_time("2026-03-01 15:00:00+00:00"):
        PoloService(eol=fake).popular_unidades_diretas()
    with freeze_time("2026-03-02 15:00:00+00:00"):
        segundo = PoloService(eol=fake).popular_unidades_diretas()

    assert segundo.executada is True
    assert segundo.motivo_ignorada is None


def test_service_registra_populacao_sem_unidades_novas(polo_factory) -> None:
    """Mesmo sem criar polos, a execução do dia é registrada."""
    polo_factory(
        gestao=GestaoPolo.DIRETA,
        codigo_eol="019241",
        nome_polo="ESCOLA A",
    )
    fake = FakeEolPopular((_unidade_eol("019241", "ESCOLA A"),))

    resultado = PoloService(eol=fake).popular_unidades_diretas()

    assert resultado.executada is True
    assert resultado.total_novos == 0
    assert resultado.total_ja_existentes == 1
    assert fake.enriquecer_chamadas == []


def test_service_resolve_colisao_de_nome_do_polo(polo_factory) -> None:
    """Nomes repetidos recebem o código EOL como sufixo."""
    polo_factory(
        gestao=GestaoPolo.DIRETA,
        codigo_eol="019251",
        nome_polo="ESCOLA COLISAO",
    )
    fake = FakeEolPopular(
        (_unidade_eol("019252", "ESCOLA COLISAO"),),
        (_unidade_recreio("019252", "ESCOLA COLISAO"),),
    )

    PoloService(eol=fake).popular_unidades_diretas()

    assert Polo.objects.get(codigo_eol="019252").nome_polo == (
        "ESCOLA COLISAO (019252)"
    )


def test_service_ignora_unidade_com_dados_invalidos() -> None:
    """ValidationError pontual não interrompe o lote."""
    fake = FakeEolPopular(
        (
            _unidade_eol("019260", "ESCOLA OK"),
            _unidade_eol("019261", "ESCOLA ERRO"),
        ),
        (
            _unidade_recreio("019260", "ESCOLA OK"),
            _unidade_recreio(
                "019261",
                "ESCOLA ERRO",
                email="email-invalido",
            ),
        ),
    )

    resultado = PoloService(eol=fake).popular_unidades_diretas()

    assert resultado.total_novos == 1
    assert Polo.objects.filter(codigo_eol="019260").exists()
    assert not Polo.objects.filter(codigo_eol="019261").exists()


def test_service_popula_em_lotes(monkeypatch) -> None:
    """O enriquecimento é particionado quando há muitas unidades novas."""
    monkeypatch.setattr(
        "apps.polos.services.polo_service.TAMANHO_LOTE_POPULAR_UNIDADES_DIRETAS",
        2,
    )
    unidades = (
        _unidade_eol("019271", "ESCOLA 1"),
        _unidade_eol("019272", "ESCOLA 2"),
        _unidade_eol("019273", "ESCOLA 3"),
    )
    fake = FakeEolPopular(
        unidades,
        (
            _unidade_recreio("019271", "ESCOLA 1"),
            _unidade_recreio("019272", "ESCOLA 2"),
            _unidade_recreio("019273", "ESCOLA 3"),
        ),
    )

    resultado = PoloService(eol=fake).popular_unidades_diretas()

    assert resultado.total_novos == 3
    assert len(fake.enriquecer_chamadas) == 2


def test_service_usa_defaults_quando_dre_ou_tipo_vem_vazio() -> None:
    """DRE e tipo de UE vazios recebem o fallback do domínio."""
    fake = FakeEolPopular(
        (_unidade_eol("019270", "ESCOLA DEFAULTS"),),
        (
            _unidade_recreio(
                "019270",
                "ESCOLA DEFAULTS",
                sigla_tipo_escola="",
                nome_dre="",
                sigla_dre="",
                codigo_dre="",
                email="a@b.com",
                telefone="",
                cep="",
                tipo_logradouro="",
                logradouro="",
                bairro="",
                numero="",
                nome_diretor="",
            ),
        ),
    )

    resultado = PoloService(eol=fake).popular_unidades_diretas()

    polo = Polo.objects.get(codigo_eol="019270")
    assert resultado.total_novos == 1
    assert polo.dre_nome == "Não informado"
    assert polo.dre_codigo_eol == "Não informado"
    assert polo.tipo_ue == "Não informado"
