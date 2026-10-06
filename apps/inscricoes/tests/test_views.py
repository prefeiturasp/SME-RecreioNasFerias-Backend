"""Testes dos endpoints HTTP de inscrições."""

from types import SimpleNamespace

import pytest
from django.core.exceptions import ValidationError
from freezegun import freeze_time
from rest_framework import status
from rest_framework.response import Response

from apps.inscricoes.api.serializers import (
    InscricaoDetalheSerializer,
    InscricaoInformacoesBasicasSerializer,
    InscricaoListagemSerializer,
)
from apps.inscricoes.api.views.inscricao_viewset import InscricaoViewSet
from apps.inscricoes.constants import (
    GrupoInscricao,
    StatusInscricao,
    TipoEstudante,
)
from apps.inscricoes.models import Inscricao
from apps.inscricoes.services.inscricao_service import InscricaoService
from apps.inscricoes.validators import MENSAGEM_EOL_NAO_ENCONTRADO
from apps.integracoes.eol.exceptions import (
    EolConfigError,
    EolContratoError,
    EolIndisponivelError,
)
from apps.integracoes.eol.port import ParticipanteRedeEol

pytestmark = pytest.mark.django_db

URL = "/api/v1/inscricoes/"


def _payload(polo, *, tipo=TipoEstudante.ESTUDANTE_EXTERNO) -> dict[str, str]:
    """Monta um payload completo de inscrição externa."""
    return {
        "polo": str(polo.uuid),
        "tipo_estudante": tipo,
        "grupo": GrupoInscricao.QUATRO_A_14_ANOS,
        "cpf": "12312312312",
        "nome_participante": "Participante da API",
        "data_nascimento": "2015-05-19",
        "responsavel_nome": "Responsável da API",
        "cep": "01001000",
        "tipo_logradouro": "Rua",
        "logradouro": "Principal",
        "numero": "10",
        "bairro": "Centro",
        "cidade": "São Paulo",
        "telefone_contato_1": "11911111111",
        "email": "responsavel@api.example",
        "dre_codigo_eol": polo.dre_codigo_eol,
        "dre_nome": polo.dre_nome,
    }


def test_rotas_exigem_autenticacao(api_client) -> None:
    """As rotas de inscrições exigem autenticação."""
    response = api_client.get(URL)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_cria_e_recupera_inscricao_com_detalhes(
    cliente_autenticado,
    polo_factory,
    definicao_polo_factory,
    edicao_factory,
) -> None:
    """POST cria e GET retorna os resumos de polo e edição."""
    polo = polo_factory()
    edicao = edicao_factory()
    definicao_polo_factory(polo=polo, edicao=edicao, tipo="oficial")
    payload = _payload(polo)
    payload["edicao"] = str(edicao.uuid)

    criado = cliente_autenticado.post(URL, payload, format="json")
    recuperado = cliente_autenticado.get(f"{URL}{criado.data['uuid']}/")

    assert criado.status_code == status.HTTP_201_CREATED
    assert criado.data["status"] == StatusInscricao.COMPLETA
    assert recuperado.status_code == status.HTTP_200_OK
    assert recuperado.data["polo"] == {
        "uuid": str(polo.uuid),
        "nome_polo": polo.nome_polo,
    }
    assert recuperado.data["edicao"] == {
        "uuid": str(edicao.uuid),
        "nome": edicao.nome,
    }


def test_lista_aplica_filtros_e_retorna_polo_nome(
    cliente_autenticado,
    inscricao_completa_factory,
) -> None:
    """GET lista usa os filtros funcionais da tela."""
    inscricao = inscricao_completa_factory(nome_participante="Filtrável")
    inscricao_completa_factory(nome_participante="Não retornar")

    response = cliente_autenticado.get(
        URL,
        {
            "tipo_estudante": inscricao.tipo_estudante,
            "polo": str(inscricao.polo.uuid),
            "codigo_eol": inscricao.codigo_eol,
            "cpf": inscricao.cpf,
            "nome_participante": "filtrável",
            "grupo": inscricao.grupo,
            "status": inscricao.status,
            "desabilita_paginacao": "true",
        },
    )

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    assert response.data[0]["polo_nome"] == inscricao.polo.nome_polo


def test_cria_rascunho_atualiza_e_remove(
    cliente_autenticado,
    polo_factory,
) -> None:
    """A API permite criar rascunho, atualizar e remover."""
    criado = cliente_autenticado.post(
        URL,
        {
            "tipo_estudante": TipoEstudante.ESTUDANTE_EXTERNO,
            "grupo": GrupoInscricao.QUATRO_A_14_ANOS,
        },
        format="json",
    )
    atualizado = cliente_autenticado.patch(
        f"{URL}{criado.data['uuid']}/",
        {"nome_participante": "Rascunho atualizado"},
        format="json",
    )
    removido = cliente_autenticado.delete(f"{URL}{criado.data['uuid']}/")

    assert criado.status_code == status.HTTP_201_CREATED
    assert atualizado.status_code == status.HTTP_200_OK
    assert removido.status_code == status.HTTP_204_NO_CONTENT


def test_cancela_e_reativa_inscricao(
    cliente_autenticado,
    inscricao_completa_factory,
) -> None:
    """As ações manuais alteram o ciclo de vida da inscrição."""
    inscricao = inscricao_completa_factory()

    cancelada = cliente_autenticado.post(
        f"{URL}{inscricao.uuid}/cancelar/", {}, format="json"
    )
    reativada = cliente_autenticado.post(
        f"{URL}{inscricao.uuid}/reativar/", {}, format="json"
    )

    assert cancelada.status_code == status.HTTP_200_OK
    assert cancelada.data["status"] == StatusInscricao.CANCELADA
    assert reativada.status_code == status.HTTP_200_OK
    assert reativada.data["status"] == StatusInscricao.COMPLETA


def test_lista_polos_elegiveis_com_e_sem_paginacao(
    cliente_autenticado,
    inscricao_completa_factory,
) -> None:
    """A ação retorna polos oficiais com os dois formatos de paginação."""
    polo = inscricao_completa_factory().polo

    with freeze_time("2099-01-01 12:00:00"):
        paginado = cliente_autenticado.get(
            f"{URL}polos-elegiveis/",
            {"dre_codigo_eol": polo.dre_codigo_eol},
        )
        sem_paginacao = cliente_autenticado.get(
            f"{URL}polos-elegiveis/",
            {
                "dre_codigo_eol": polo.dre_codigo_eol,
                "desabilita_paginacao": "true",
            },
        )

    assert paginado.status_code == status.HTTP_200_OK
    assert "results" in paginado.data
    assert sem_paginacao.status_code == status.HTTP_200_OK
    assert sem_paginacao.data[0]["nome_polo"] == polo.nome_polo


def test_uuid_inexistente_retorna_400(cliente_autenticado) -> None:
    """UUID inexistente é convertido em erro de validação."""
    response = cliente_autenticado.get(
        f"{URL}baa03608-83dc-4c6d-9b5a-8dd36b429044/"
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_view_seleciona_serializers_por_acao() -> None:
    """O ViewSet seleciona o contrato correto para cada ação."""
    view = InscricaoViewSet()

    view.action = "list"
    assert view.get_serializer_class() is InscricaoListagemSerializer
    view.action = "retrieve"
    assert view.get_serializer_class() is InscricaoDetalheSerializer
    view.action = "create"
    assert view.get_serializer_class() is InscricaoInformacoesBasicasSerializer


def test_service_lista_polos_elegiveis_sem_filtro() -> None:
    """A consulta de polos também funciona sem filtro de DRE."""
    resultado = InscricaoService().listar_polos_elegiveis()

    assert resultado.count() == 0


def test_view_polos_elegiveis_sem_paginacao_do_queryset(
    inscricao_completa_factory,
    monkeypatch,
) -> None:
    """A action suporta o ramo em que a paginação não retorna página."""
    polo = inscricao_completa_factory().polo
    view = InscricaoViewSet()
    request = SimpleNamespace(
        query_params={"dre_codigo_eol": polo.dre_codigo_eol}
    )
    monkeypatch.setattr(view, "paginate_queryset", lambda queryset: None)

    with freeze_time("2099-01-01 12:00:00"):
        response = view.polos_elegiveis(request)

    assert isinstance(response, Response)
    assert response.status_code == 200
    assert response.data[0]["nome_polo"] == polo.nome_polo


def test_view_retorna_valores_dos_choices(cliente_autenticado) -> None:
    """A action de catálogos retorna value e label dos choices."""
    response = cliente_autenticado.get("/api/v1/inscricoes/valores-choices/")

    assert response.status_code == 200
    assert response.data["grupo_inscricao"][0] == {
        "value": "BERCARIO_I",
        "label": "Berçário I",
    }


def _participante() -> ParticipanteRedeEol:
    """Monta um participante mínimo para o contrato HTTP."""
    return ParticipanteRedeEol(
        codigo_aluno=6034178,
        tipo_turno=0,
        ano_letivo=2026,
        nome_aluno="ANNA JULIA ARAUJO SA",
        nome_social_aluno="",
        codigo_situacao_matricula=3,
        situacao_matricula="Transferido",
        data_situacao="2026-05-15T17:25:21.483",
        data_nascimento="2013-10-16",
        numero_aluno_chamada="001",
        codigo_turma=3026798,
        nome_responsavel="SAMARA LIMA ARAUJO",
        tipo_responsavel="1",
        celular_responsavel="",
        data_atualizacao_contato="2024-02-09T11:18:16.11",
        codigo_tipo_turma=1,
        turma_nome="",
        etapa_ensino="",
        ciclo_ensino="",
        desc_etapa_ensino="",
        desc_ciclo_ensino="",
        data_atualizacao_tabela="2026-05-15T17:25:21.483",
        nome_mae="SAMARA LIMA ARAUJO",
        sexo="F",
        grupo_etnico="RECUSOU INFORMAR",
        nacionalidade="B",
        eh_imigrante=False,
        nis="23703487417",
        cns="",
        numero="72",
        complemento="",
        bairro="VILA SANTA CRUZ ZONA LESTE",
        cep="08411-010",
        cidade="SAO PAULO",
        uf="SP",
        tipo_logradouro="Rua",
        logradouro="DA PASSAGEM FUNDA",
    )


def test_participante_eol_exige_autenticacao(api_client) -> None:
    """A consulta de participante exige autenticação."""
    response = api_client.get(f"{URL}participante-eol/")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_participante_eol_devolve_nome(
    cliente_autenticado,
    monkeypatch,
) -> None:
    """O GET devolve só os campos que preenchem o formulário."""
    participante = _participante()

    def _consultar(
        _self: InscricaoService,
        codigo_eol: str | None,
    ) -> ParticipanteRedeEol:
        assert codigo_eol == "6034178"
        return participante

    monkeypatch.setattr(
        InscricaoService,
        "consultar_participante_por_eol",
        _consultar,
    )

    response = cliente_autenticado.get(
        f"{URL}participante-eol/",
        {"codigo_eol": "6034178"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert set(response.data) == {
        "codigo_eol",
        "nome_participante",
        "data_nascimento",
        "responsavel_nome",
        "responsavel_nome_social",
        "cep",
        "logradouro",
        "numero",
        "complemento",
        "bairro",
        "cidade",
        "telefone_contato_1",
        "telefone_contato_2",
        "email",
    }
    assert response.data["codigo_eol"] == "6034178"
    assert response.data["nome_participante"] == "ANNA JULIA ARAUJO SA"
    assert response.data["responsavel_nome"] == "SAMARA LIMA ARAUJO"
    assert response.data["data_nascimento"] == "2013-10-16"
    assert response.data["cep"] == "08411-010"
    assert response.data["logradouro"] == "DA PASSAGEM FUNDA"
    assert response.data["numero"] == "72"
    assert response.data["bairro"] == "VILA SANTA CRUZ ZONA LESTE"
    assert response.data["cidade"] == "SAO PAULO"
    assert response.data["telefone_contato_1"] == ""
    assert response.data["email"] == ""
    assert response.data["telefone_contato_2"] == ""
    assert response.data["responsavel_nome_social"] == ""
    assert response.data["complemento"] == ""


def test_participante_eol_nao_encontrado_nao_grava(
    cliente_autenticado,
    monkeypatch,
) -> None:
    """Código ausente na SME responde 400 e não cria inscrição."""

    def _consultar(
        _self: InscricaoService,
        codigo_eol: str | None,
    ) -> ParticipanteRedeEol:
        raise ValidationError({"codigo_eol": MENSAGEM_EOL_NAO_ENCONTRADO})

    monkeypatch.setattr(
        InscricaoService,
        "consultar_participante_por_eol",
        _consultar,
    )

    response = cliente_autenticado.get(
        f"{URL}participante-eol/",
        {"codigo_eol": "000"},
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data == {"detalhe": MENSAGEM_EOL_NAO_ENCONTRADO}
    assert Inscricao.objects.count() == 0


def test_participante_eol_retorna_erro_de_configuracao(
    cliente_autenticado,
    monkeypatch,
) -> None:
    """Falha de configuração da EOL retorna HTTP 500."""

    def _consultar(
        _self: InscricaoService,
        codigo_eol: str | None,
    ) -> ParticipanteRedeEol:
        raise EolConfigError("config")

    monkeypatch.setattr(
        InscricaoService,
        "consultar_participante_por_eol",
        _consultar,
    )

    response = cliente_autenticado.get(f"{URL}participante-eol/")

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.data == {"detalhe": "config"}


@pytest.mark.parametrize(
    "erro",
    [EolIndisponivelError("indisponivel"), EolContratoError("contrato")],
)
def test_participante_eol_retorna_erro_de_integracao(
    cliente_autenticado,
    monkeypatch,
    erro: Exception,
) -> None:
    """Falhas externas da EOL retornam HTTP 502."""

    def _consultar(
        _self: InscricaoService,
        codigo_eol: str | None,
    ) -> ParticipanteRedeEol:
        raise erro

    monkeypatch.setattr(
        InscricaoService,
        "consultar_participante_por_eol",
        _consultar,
    )

    response = cliente_autenticado.get(f"{URL}participante-eol/")

    assert response.status_code == status.HTTP_502_BAD_GATEWAY
    assert response.data == {"detalhe": str(erro)}
