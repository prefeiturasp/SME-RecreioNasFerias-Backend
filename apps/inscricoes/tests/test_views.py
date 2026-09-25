"""Testes dos endpoints HTTP de inscrições."""

from types import SimpleNamespace

import pytest
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

from apps.inscricoes.services.inscricao_service import InscricaoService

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
