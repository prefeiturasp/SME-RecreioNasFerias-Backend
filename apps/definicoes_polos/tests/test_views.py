"""Testes dos endpoints HTTP de definições de polos."""

from datetime import date, timedelta

import pytest
from rest_framework import status

from apps.definicoes_polos.api.serializers import (
    DefinicaoPoloHistoricoSerializer,
)
from apps.definicoes_polos.api.views.definicao_polo_viewset import (
    DefinicaoPoloViewSet,
)
from apps.definicoes_polos.constants import TipoPolo

pytestmark = pytest.mark.django_db

URL = "/api/v1/definicoes-polos/"


def _criar_edicao(edicao_factory, numero: int):
    """Cria uma edição com período isolado."""
    inicio = date(2099, 1, 1) + timedelta(days=numero * 40)
    return edicao_factory(
        nome=f"Edição de View {numero}",
        data_inicio=inicio,
        data_fim=inicio + timedelta(days=20),
        inscricoes_inicio=inicio - timedelta(days=10),
        inscricoes_fim=inicio + timedelta(days=20),
    )


def _payload(polo, edicao, projecao=200):
    """Monta payload válido de participação."""
    return {
        "polo": str(polo.uuid),
        "edicao": str(edicao.uuid),
        "tipo": TipoPolo.OFICIAL,
        "projecao_inscritos": projecao,
        "ponto_focal_nome": "Ponto Focal",
        "ponto_focal_telefone": "11999999999",
        "ponto_focal_email": "focal@example.com",
    }


def test_rotas_exigem_autenticacao(api_client) -> None:
    """As rotas do domínio exigem autenticação."""
    response = api_client.get(URL)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_cria_e_recupera_detalhamento_pela_api(
    cliente_autenticado,
    polo_factory,
    edicao_factory,
) -> None:
    """POST cria e GET retorna polo completo e edição resumida."""
    polo = polo_factory()
    edicao = _criar_edicao(edicao_factory, 1)

    criado = cliente_autenticado.post(
        URL, _payload(polo, edicao), format="json"
    )
    recuperado = cliente_autenticado.get(f"{URL}{criado.data['uuid']}/")

    assert criado.status_code == status.HTTP_201_CREATED
    assert recuperado.status_code == status.HTTP_200_OK
    assert recuperado.data["polo"]["codigo_eol"] == polo.codigo_eol
    assert recuperado.data["edicao"] == {
        "uuid": str(edicao.uuid),
        "nome": edicao.nome,
    }


def test_lista_retorna_todos_os_polos_e_filtros(
    cliente_autenticado,
    polo_factory,
    edicao_factory,
    definicao_polo_factory,
) -> None:
    """A listagem consolida polos e aplica filtros da tela."""
    edicao = _criar_edicao(edicao_factory, 2)
    esperado = polo_factory(
        nome_polo="Polo filtrado",
        codigo_eol="019888",
        dre_codigo_eol="108100",
        tipo_ue="EMEF",
        gestao="direta",
    )
    definicao_polo_factory(polo=esperado, edicao=edicao, tipo=TipoPolo.RESERVA)
    sem_definicao = polo_factory(nome_polo="Polo sem definição")

    response = cliente_autenticado.get(
        URL,
        {
            "dre_codigos_eol": ["108100"],
            "tipo_ue": "EMEF",
            "busca": "019888",
            "gestao": "direta",
            "tipo_polo": TipoPolo.RESERVA,
        },
    )

    assert response.status_code == status.HTTP_200_OK
    assert [item["polo_uuid"] for item in response.data] == [
        str(esperado.uuid)
    ]
    assert sem_definicao.uuid not in [
        item["polo_uuid"] for item in response.data
    ]


def test_lista_filtra_por_edicao_com_inner_join(
    cliente_autenticado,
    polo_factory,
    edicao_factory,
    definicao_polo_factory,
) -> None:
    """Com edição, polos sem vínculo não aparecem."""
    edicao = _criar_edicao(edicao_factory, 3)
    esperado = polo_factory()
    definicao_polo_factory(polo=esperado, edicao=edicao)
    polo_factory()

    response = cliente_autenticado.get(URL, {"edicao": str(edicao.uuid)})

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    assert response.data[0]["polo_uuid"] == str(esperado.uuid)
    assert response.data[0]["edicao_uuid"] == str(edicao.uuid)


def test_atualiza_e_remove_participacao_pela_api(
    cliente_autenticado,
    definicao_polo_factory,
) -> None:
    """PATCH atualiza campos e DELETE remove a participação."""
    definicao = definicao_polo_factory()

    atualizada = cliente_autenticado.patch(
        f"{URL}{definicao.uuid}/",
        {"projecao_inscritos": 175},
        format="json",
    )
    removida = cliente_autenticado.delete(f"{URL}{definicao.uuid}/")

    assert atualizada.status_code == status.HTTP_200_OK
    assert atualizada.data["total_inscritos"] == 227
    assert removida.status_code == status.HTTP_204_NO_CONTENT


def test_uuid_inexistente_retorna_400(cliente_autenticado) -> None:
    """UUID de definição inexistente é convertido em validação HTTP 400."""
    response = cliente_autenticado.get(
        f"{URL}baa03608-83dc-4c6d-9b5a-8dd36b429044/"
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data == {"detalhe": "Definição de Polo não encontrada."}


def test_view_seleciona_serializer_de_historico() -> None:
    """O ViewSet usa o serializer próprio para a ação de histórico."""
    view = DefinicaoPoloViewSet()
    view.action = "historico"

    assert view.get_serializer_class() is DefinicaoPoloHistoricoSerializer


def test_historico_exige_polo_e_retorna_edicao(
    cliente_autenticado,
    definicao_polo_factory,
) -> None:
    """Histórico exige polo e retorna UUID e nome da edição."""
    definicao = definicao_polo_factory()

    sem_polo = cliente_autenticado.get(f"{URL}historico/")
    response = cliente_autenticado.get(
        f"{URL}historico/", {"polo": str(definicao.polo.uuid)}
    )

    assert sem_polo.status_code == status.HTTP_400_BAD_REQUEST
    assert response.status_code == status.HTTP_200_OK
    assert response.data[0]["edicao"] == {
        "uuid": str(definicao.edicao.uuid),
        "nome": definicao.edicao.nome,
    }


def test_historico_polo_inexistente_retorna_400(cliente_autenticado) -> None:
    """Polo inexistente no histórico retorna validação HTTP 400."""
    response = cliente_autenticado.get(
        f"{URL}historico/",
        {"polo": "baa03608-83dc-4c6d-9b5a-8dd36b429044"},
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_vincula_em_massa_pela_api(
    cliente_autenticado,
    polo_factory,
    edicao_factory,
) -> None:
    """A ação de vinculação em massa cria participações."""
    polos = [polo_factory(), polo_factory()]
    edicao = _criar_edicao(edicao_factory, 4)

    response = cliente_autenticado.post(
        f"{URL}vincular-em-massa/",
        {
            "polos": [str(polo.uuid) for polo in polos],
            "edicao": str(edicao.uuid),
            "projecao_inscritos": 175,
        },
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert len(response.data["criadas"]) == 2
    assert response.data["ignorados"] == []


def test_vincular_em_massa_rejeita_uuid_inexistente(
    cliente_autenticado,
    edicao_factory,
) -> None:
    """A ação não ignora polo inexistente."""
    edicao = _criar_edicao(edicao_factory, 5)
    response = cliente_autenticado.post(
        f"{URL}vincular-em-massa/",
        {
            "polos": ["baa03608-83dc-4c6d-9b5a-8dd36b429044"],
            "edicao": str(edicao.uuid),
            "projecao_inscritos": 100,
        },
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_altera_tipo_em_massa_pela_api(
    cliente_autenticado,
    definicao_polo_factory,
) -> None:
    """A ação altera o tipo da participação."""
    definicao = definicao_polo_factory()
    response = cliente_autenticado.post(
        f"{URL}alterar-tipo-em-massa/",
        [
            {
                "polo_uuid": str(definicao.polo.uuid),
                "edicao": str(definicao.edicao.uuid),
                "tipo": TipoPolo.OFICIAL,
            }
        ],
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["alterados"][0]["tipo"] == TipoPolo.OFICIAL


def test_altera_edicao_em_massa_pela_api(
    cliente_autenticado,
    definicao_polo_factory,
    edicao_factory,
) -> None:
    """A ação move definições para a edição destino."""
    definicao = definicao_polo_factory()
    destino = _criar_edicao(edicao_factory, 6)

    response = cliente_autenticado.post(
        f"{URL}alterar-edicao-em-massa/",
        {
            "definicoes": [str(definicao.uuid)],
            "edicao_destino": str(destino.uuid),
        },
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert str(response.data[0]["edicao"]) == str(destino.uuid)


def test_acoes_em_massa_rejeitam_uuid_inexistente(
    cliente_autenticado,
    definicao_polo_factory,
) -> None:
    """Ações não aceitam identificadores inexistentes."""
    definicao = definicao_polo_factory()
    response = cliente_autenticado.post(
        f"{URL}alterar-edicao-em-massa/",
        {
            "definicoes": ["baa03608-83dc-4c6d-9b5a-8dd36b429044"],
            "edicao_destino": str(definicao.edicao.uuid),
        },
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
