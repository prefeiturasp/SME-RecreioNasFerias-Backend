"""Testes dos endpoints HTTP de polos."""

from datetime import UTC, datetime

import pytest
from rest_framework import status

from apps.integracoes.eol.exceptions import (
    EolConfigError,
    EolContratoError,
    EolIndisponivelError,
)
from apps.integracoes.eol.port import DreEol, TipoEscolaEol
from apps.polos.constants import (
    MOTIVO_JA_EXECUTADA_HOJE,
    StatusPolo,
    TipoPolo,
)
from apps.polos.services.polo_service import (
    PoloService,
    ResultadoPopularUnidadesDiretas,
)

pytestmark = pytest.mark.django_db

URL = "/api/v1/polos/"


def _payload(nome: str = "Polo novo") -> dict[str, object]:
    """Monta um payload válido para a API."""
    return {
        "codigo_eol": "019370",
        "nome_polo": nome,
        "nome_osc": f"OSC {nome}",
        "dre_nome": "DRE de teste",
        "dre_codigo_eol": "108210",
        "tipo": TipoPolo.OFICIAL,
        "status": StatusPolo.INATIVO,
        "tipo_ue": "CEU EMEF",
        "quantidade_maxima_alunos": 250,
        "cep": "01001000",
        "tipo_logradouro": "Rua",
        "logradouro": "Principal",
        "bairro": "Centro",
        "numero": "10",
        "nome_gestor": "Gestor do Polo",
        "email": "polo@example.com",
        "telefone": "1130000000",
    }


def test_lista_polos_exige_autenticacao(api_client) -> None:
    """A rota exige autenticação."""
    response = api_client.get(URL)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data == {
        "detalhe": "Credenciais de autenticacao nao foram informadas."
    }


def test_lista_polos_aplica_filtros_pela_api(
    cliente_autenticado,
    polo_factory,
) -> None:
    """A listagem encaminha os filtros para o serviço de polos."""
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

    response = cliente_autenticado.get(
        URL,
        {
            "dre_codigo_eol": "108100",
            "tipo_ue": "EMEF",
            "busca": "Mario",
            "desabilita_paginacao": "true",
        },
    )

    assert response.status_code == status.HTTP_200_OK
    assert [item["uuid"] for item in response.data] == [str(esperado.uuid)]


def test_cria_polo_pela_api(cliente_autenticado) -> None:
    """O POST cria polo e aplica defaults de tipo, status e gestão."""
    response = cliente_autenticado.post(URL, _payload(), format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["nome_polo"] == "Polo novo"
    assert response.data["tipo"] == TipoPolo.PENDENTE
    assert response.data["status"] == StatusPolo.ATIVO
    assert response.data["gestao"] == "parceira"
    assert response.data["complemento"] == ""


def test_retorna_polo_pela_api(cliente_autenticado, polo_factory) -> None:
    """O GET recupera um polo pelo UUID."""
    polo = polo_factory()

    response = cliente_autenticado.get(f"{URL}{polo.uuid}/")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["uuid"] == str(polo.uuid)


def test_atualiza_polo_com_put_pela_api(
    cliente_autenticado,
    polo_factory,
) -> None:
    """O PUT atualiza o polo sem exigir timestamps gerenciados."""
    polo = polo_factory()
    payload = _payload(nome="Polo atualizado")
    payload.update(
        codigo_eol=polo.codigo_eol,
        nome_osc="OSC atualizada",
        dre_nome=polo.dre_nome,
        dre_codigo_eol=polo.dre_codigo_eol,
        tipo=TipoPolo.OFICIAL,
        status=StatusPolo.INATIVO,
        gestao="direta",
    )

    response = cliente_autenticado.put(
        f"{URL}{polo.uuid}/", payload, format="json"
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["nome_polo"] == "Polo atualizado"
    assert response.data["gestao"] == "direta"
    assert "atualizado_em" in response.data


def test_atualiza_parcialmente_polo_pela_api(
    cliente_autenticado, polo_factory
) -> None:
    """O PATCH atualiza somente os campos enviados."""
    polo = polo_factory()

    response = cliente_autenticado.patch(
        f"{URL}{polo.uuid}/",
        {"status": StatusPolo.INATIVO},
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["status"] == StatusPolo.INATIVO


def test_remove_polo_pela_api(cliente_autenticado, polo_factory) -> None:
    """O DELETE remove um polo cadastrado."""
    polo = polo_factory()

    response = cliente_autenticado.delete(f"{URL}{polo.uuid}/")

    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_lista_tipos_escola_pela_api(cliente_autenticado, monkeypatch) -> None:
    """A API retorna tipos normalizados pela integração EOL."""
    monkeypatch.setattr(
        PoloService,
        "listar_tipos_escola",
        lambda self: (TipoEscolaEol(codigo=1, descricao_sigla="EMEF"),),
    )

    response = cliente_autenticado.get(f"{URL}tipos-escola/")

    assert response.status_code == status.HTTP_200_OK
    assert response.data == [{"codigo": 1, "descricao_sigla": "EMEF"}]


def test_lista_dres_pela_api(cliente_autenticado, monkeypatch) -> None:
    """A API retorna DREs normalizadas pela integração EOL."""
    monkeypatch.setattr(
        PoloService,
        "listar_dres",
        lambda self: (
            DreEol(
                codigo_dre="108100",
                nome_dre="DRE Butantã",
                sigla_dre="DRE - BT",
            ),
        ),
    )

    response = cliente_autenticado.get(f"{URL}dres/")

    assert response.status_code == status.HTTP_200_OK
    assert response.data == [
        {
            "codigo_dre": "108100",
            "nome_dre": "DRE Butantã",
            "sigla_dre": "DRE - BT",
        }
    ]


@pytest.mark.parametrize(
    ("url_suffix", "metodo", "erro"),
    [
        ("tipos-escola/", "listar_tipos_escola", EolConfigError("config")),
        ("dres/", "listar_dres", EolConfigError("config")),
    ],
)
def test_catalogos_retorna_erro_de_configuracao(
    cliente_autenticado,
    monkeypatch,
    url_suffix,
    metodo,
    erro,
) -> None:
    """Falhas de configuração da EOL retornam HTTP 500."""
    def _falhar(_self):
        raise erro

    monkeypatch.setattr(PoloService, metodo, _falhar)

    response = cliente_autenticado.get(f"{URL}{url_suffix}")

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.data == {"detalhe": "config"}


@pytest.mark.parametrize(
    ("url_suffix", "metodo", "erro"),
    [
        (
            "tipos-escola/",
            "listar_tipos_escola",
            EolIndisponivelError("indisponivel"),
        ),
        ("dres/", "listar_dres", EolContratoError("contrato")),
    ],
)
def test_catalogos_retorna_erro_de_integracao(
    cliente_autenticado,
    monkeypatch,
    url_suffix,
    metodo,
    erro,
) -> None:
    """Falhas externas da EOL retornam HTTP 502."""
    def _falhar(_self):
        raise erro

    monkeypatch.setattr(PoloService, metodo, _falhar)

    response = cliente_autenticado.get(f"{URL}{url_suffix}")

    assert response.status_code == status.HTTP_502_BAD_GATEWAY
    assert response.data == {"detalhe": str(erro)}


def test_popular_unidades_diretas_exige_autenticacao(api_client) -> None:
    """A população de polos diretos exige autenticação."""
    response = api_client.post(f"{URL}popular/")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data == {
        "detalhe": "Credenciais de autenticacao nao foram informadas."
    }


def test_popular_unidades_diretas_pela_api(
    cliente_autenticado,
    polo_factory,
    monkeypatch,
) -> None:
    """A action devolve o resultado da população em snake_case."""
    polo = polo_factory()
    agora = datetime(2026, 3, 1, 15, 0, tzinfo=UTC)

    def _popular(_self):
        return ResultadoPopularUnidadesDiretas(
            total_consultados=2,
            total_novos=1,
            total_ja_existentes=1,
            polos_criados=[polo],
            executada=True,
            motivo_ignorada=None,
            ultima_execucao_em=agora,
        )

    monkeypatch.setattr(PoloService, "popular_unidades_diretas", _popular)

    response = cliente_autenticado.post(f"{URL}popular/")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["total_consultados"] == 2
    assert response.data["total_novos"] == 1
    assert response.data["total_ja_existentes"] == 1
    assert response.data["executada"] is True
    assert response.data["motivo_ignorada"] is None
    assert response.data["unidades_novas"][0]["uuid"] == str(polo.uuid)
    assert response.data["unidades_novas"][0]["codigo_eol"] == polo.codigo_eol


def test_popular_unidades_diretas_quando_ja_executada(
    cliente_autenticado,
    monkeypatch,
) -> None:
    """A action informa quando a carga do dia já ocorreu."""
    agora = datetime(2026, 3, 1, 15, 0, tzinfo=UTC)

    def _popular(_self):
        return ResultadoPopularUnidadesDiretas(
            total_consultados=0,
            total_novos=0,
            total_ja_existentes=0,
            polos_criados=[],
            executada=False,
            motivo_ignorada=MOTIVO_JA_EXECUTADA_HOJE,
            ultima_execucao_em=agora,
        )

    monkeypatch.setattr(PoloService, "popular_unidades_diretas", _popular)

    response = cliente_autenticado.post(f"{URL}popular/")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["executada"] is False
    assert response.data["motivo_ignorada"] == MOTIVO_JA_EXECUTADA_HOJE
    assert response.data["unidades_novas"] == []


def test_popular_unidades_diretas_retorna_erro_de_configuracao(
    cliente_autenticado,
    monkeypatch,
) -> None:
    """Falha de configuração da EOL retorna HTTP 500."""
    def _falhar(_self):
        raise EolConfigError("config")

    monkeypatch.setattr(PoloService, "popular_unidades_diretas", _falhar)

    response = cliente_autenticado.post(f"{URL}popular/")

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.data == {"detalhe": "config"}


def test_popular_unidades_diretas_retorna_erro_de_integracao(
    cliente_autenticado,
    monkeypatch,
) -> None:
    """Falha externa da EOL retorna HTTP 502."""
    def _falhar(_self):
        raise EolIndisponivelError("indisponivel")

    monkeypatch.setattr(PoloService, "popular_unidades_diretas", _falhar)

    response = cliente_autenticado.post(f"{URL}popular/")

    assert response.status_code == status.HTTP_502_BAD_GATEWAY
    assert response.data == {"detalhe": "indisponivel"}
