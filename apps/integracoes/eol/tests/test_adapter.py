"""Testes unitarios do adaptador EOL."""

from __future__ import annotations

from typing import Any

from apps.integracoes.eol.adapter import EolAdapter
from apps.integracoes.eol.constants import CODIGO_CARGO_DIRETOR_ESCOLA
from apps.integracoes.eol.exceptions import EolIndisponivelError
from apps.integracoes.eol.port import (
    DadosUnidadeEol,
    DreEol,
    TipoEscolaEol,
    UnidadeEol,
    UnidadeRecreioEol,
)


class FakeClient:
    """Client fake que simula os três endpoints de escolas."""

    def __init__(
        self,
        *,
        unidades: list[dict[str, Any]] | None = None,
        tipos_escola: list[dict[str, Any]] | None = None,
        dres: list[dict[str, Any]] | None = None,
        dados: dict[str, dict[str, Any]] | None = None,
        diretores: dict[str, str] | None = None,
        falhas_dados: set[str] | None = None,
        falhas_diretores: set[str] | None = None,
    ) -> None:
        """Inicializa o fake com os payloads que serão devolvidos."""
        self.unidades = unidades or []
        self.tipos_escola = tipos_escola or []
        self.dres = dres or []
        self.dados = dados or {}
        self.diretores = diretores or {}
        self.falhas_dados = falhas_dados or set()
        self.falhas_diretores = falhas_diretores or set()
        self.calls_obter_dados: list[str] = []
        self.calls_obter_diretor: list[tuple[str, int]] = []

    def listar_todas_unidades(self) -> list[dict[str, Any]]:
        """Devolve o catalogo bruto configurado."""
        return self.unidades

    def listar_tipos_escola(self) -> list[dict[str, Any]]:
        """Devolve os tipos de escola configurados."""
        return self.tipos_escola

    def listar_dres(self) -> list[dict[str, Any]]:
        """Devolve as DREs configuradas."""
        return self.dres

    def obter_dados_unidade(self, codigo_eol: str) -> dict[str, Any] | None:
        """Devolve os dados brutos ou simula indisponibilidade pontual."""
        self.calls_obter_dados.append(codigo_eol)
        if codigo_eol in self.falhas_dados:
            raise EolIndisponivelError()
        return self.dados.get(codigo_eol)

    def obter_funcionarios_por_cargo(
        self,
        codigo_eol: str,
        codigo_cargo: int,
    ) -> list[dict[str, Any]]:
        """Devolve o diretor configurado para a unidade."""
        self.calls_obter_diretor.append((codigo_eol, codigo_cargo))
        if codigo_eol in self.falhas_diretores:
            raise EolIndisponivelError()
        nome = self.diretores.get(codigo_eol)
        if not nome:
            return []
        return [{"nomeServidor": nome}]


def _unidade_bruta(codigo: str, sigla: str) -> dict[str, Any]:
    """Monta um item de catalogo bruto para os testes."""
    return {
        "codigoEscola": codigo,
        "nomeEscola": f"Unidade {codigo}",
        "siglaTipoEscola": sigla,
        "nomeDRE": "DRE Ipiranga",
        "siglaDRE": "IP",
        "codigoDRE": "10",
    }


def test_listar_tipos_escola_normaliza_catalogo() -> None:
    """Converte o catálogo bruto de tipos no contrato tipado."""
    client = FakeClient(
        tipos_escola=[
            {"codigo": "1", "descricaoSigla": " EMEF "},
            {"codigo": 2, "descricaoSigla": "EMEI"},
        ]
    )

    tipos = EolAdapter(client=client).listar_tipos_escola()

    assert tipos == (
        TipoEscolaEol(codigo=1, descricao_sigla="EMEF"),
        TipoEscolaEol(codigo=2, descricao_sigla="EMEI"),
    )


def test_listar_dres_normaliza_catalogo() -> None:
    """Converte o catálogo bruto de DREs no contrato tipado."""
    client = FakeClient(
        dres=[
            {
                "codigoDRE": "108100",
                "nomeDRE": " DRE Butantã ",
                "siglaDRE": "DRE - BT",
            }
        ]
    )

    dres = EolAdapter(client=client).listar_dres()

    assert dres == (
        DreEol(
            codigo_dre="108100",
            nome_dre="DRE Butantã",
            sigla_dre="DRE - BT",
        ),
    )


def test_listar_todas_unidades_normaliza_catalogo() -> None:
    """Converte o catalogo bruto em contratos tipados."""
    client = FakeClient(
        unidades=[
            _unidade_bruta("094633", "EMEF"),
            _unidade_bruta("121000", "CEI DIRET"),
        ]
    )

    unidades = EolAdapter(client=client).listar_todas_unidades()

    assert unidades == (
        UnidadeEol(
            codigo_eol="094633",
            nome_escola="Unidade 094633",
            sigla_tipo_escola="EMEF",
            nome_dre="DRE Ipiranga",
            sigla_dre="IP",
            codigo_dre="10",
        ),
        UnidadeEol(
            codigo_eol="121000",
            nome_escola="Unidade 121000",
            sigla_tipo_escola="CEI DIRET",
            nome_dre="DRE Ipiranga",
            sigla_dre="IP",
            codigo_dre="10",
        ),
    )


def test_obter_dados_unidade_normaliza_payload() -> None:
    """Normaliza dados detalhados incluindo CEP e endereco."""
    client = FakeClient(
        dados={
            "094633": {
                "nome": "EMEF Professora Teste",
                "siglaTipoEscola": "EMEF",
                "nomeDRE": "DRE Ipiranga",
                "siglaDRE": "IP",
                "codigoDRE": "10",
                "email": "emef@exemplo.gov.br",
                "telefone": "1122334455",
                "cep": "04206000",
                "tipoLogradouro": "Rua",
                "logradouro": "das Flores",
                "numero": "123",
                "bairro": "Ipiranga",
            }
        }
    )

    dados = EolAdapter(client=client).obter_dados_unidade("094633")

    assert dados == DadosUnidadeEol(
        nome="EMEF Professora Teste",
        sigla_tipo_escola="EMEF",
        nome_dre="DRE Ipiranga",
        sigla_dre="IP",
        codigo_dre="10",
        email="emef@exemplo.gov.br",
        telefone="1122334455",
        cep="04206-000",
        endereco="Rua das Flores, 123 - Ipiranga",
    )


def test_obter_dados_unidade_retorna_none_para_ausente() -> None:
    """Devolve ``None`` quando a unidade não possui dados detalhados."""
    client = FakeClient()

    dados = EolAdapter(client=client).obter_dados_unidade("094633")

    assert dados is None


def test_obter_nome_diretor_usa_cargo_padrao() -> None:
    """Consulta o diretor usando o código de cargo padrão."""
    client = FakeClient(diretores={"094633": "Diretor Teste"})

    nome = EolAdapter(client=client).obter_nome_diretor("094633")

    assert nome == "Diretor Teste"
    assert client.calls_obter_diretor == [
        ("094633", CODIGO_CARGO_DIRETOR_ESCOLA)
    ]


def test_obter_nome_diretor_com_cargo_personalizado() -> None:
    """Consulta o diretor usando um código de cargo informado."""
    client = FakeClient(diretores={"094633": "Diretor Teste"})

    nome = EolAdapter(client=client).obter_nome_diretor("094633", 9999)

    assert nome == "Diretor Teste"
    assert client.calls_obter_diretor == [("094633", 9999)]


def test_obter_nome_diretor_retorna_vazio_sem_funcionario() -> None:
    """Devolve string vazia quando a unidade não possui diretor."""
    client = FakeClient()

    nome = EolAdapter(client=client).obter_nome_diretor("094633")

    assert nome == ""


def test_filtrar_unidades_recreio_por_sigla() -> None:
    """Mantém apenas as unidades com tipo de UE elegível."""
    unidades = (
        UnidadeEol(
            codigo_eol="1",
            nome_escola="EMEF",
            sigla_tipo_escola="EMEF",
            nome_dre="DRE",
            sigla_dre="DR",
            codigo_dre="1",
        ),
        UnidadeEol(
            codigo_eol="2",
            nome_escola="Outro",
            sigla_tipo_escola="OUTRO",
            nome_dre="DRE",
            sigla_dre="DR",
            codigo_dre="1",
        ),
        UnidadeEol(
            codigo_eol="3",
            nome_escola="CEI DIRET",
            sigla_tipo_escola="CEI DIRET",
            nome_dre="DRE",
            sigla_dre="DR",
            codigo_dre="1",
        ),
    )

    filtradas = EolAdapter(client=FakeClient()).filtrar_unidades_recreio(
        unidades
    )

    assert [u.codigo_eol for u in filtradas] == ["1", "3"]


def test_enriquecer_unidades_agrega_dados_e_diretor() -> None:
    """Enriquece unidades com dados detalhados e nome do diretor."""
    client = FakeClient(
        dados={
            "094633": {
                "nome": "EMEF Professora Teste",
                "email": "emef@exemplo.gov.br",
                "telefone": "1122334455",
                "cep": "04206000",
                "tipoLogradouro": "Rua",
                "logradouro": "das Flores",
                "numero": "123",
                "bairro": "Ipiranga",
            }
        },
        diretores={"094633": "Diretor Teste"},
    )
    unidades = (
        UnidadeEol(
            codigo_eol="094633",
            nome_escola="Unidade 094633",
            sigla_tipo_escola="EMEF",
            nome_dre="DRE Ipiranga",
            sigla_dre="IP",
            codigo_dre="10",
        ),
    )

    enriquecidas = EolAdapter(client=client).enriquecer_unidades(unidades)

    assert enriquecidas == (
        UnidadeRecreioEol(
            codigo_eol="094633",
            nome_escola="EMEF Professora Teste",
            sigla_tipo_escola="EMEF",
            nome_dre="DRE Ipiranga",
            sigla_dre="IP",
            codigo_dre="10",
            email="emef@exemplo.gov.br",
            telefone="1122334455",
            cep="04206-000",
            endereco="Rua das Flores, 123 - Ipiranga",
            nome_diretor="Diretor Teste",
        ),
    )


def test_enriquecer_unidades_tolera_falha_parcial() -> None:
    """Mantém os dados básicos quando o enriquecimento falha pontualmente."""
    client = FakeClient(
        dados={"094633": {"nome": "EMEF Teste"}},
        diretores={"094633": "Diretor Teste"},
        falhas_dados={"121000"},
    )
    unidades = (
        UnidadeEol(
            codigo_eol="094633",
            nome_escola="Unidade 094633",
            sigla_tipo_escola="EMEF",
            nome_dre="DRE Ipiranga",
            sigla_dre="IP",
            codigo_dre="10",
        ),
        UnidadeEol(
            codigo_eol="121000",
            nome_escola="Unidade 121000",
            sigla_tipo_escola="CEI DIRET",
            nome_dre="DRE Ipiranga",
            sigla_dre="IP",
            codigo_dre="10",
        ),
    )

    enriquecidas = EolAdapter(client=client).enriquecer_unidades(unidades)

    por_eol = {u.codigo_eol: u for u in enriquecidas}
    assert por_eol["094633"].nome_escola == "EMEF Teste"
    assert por_eol["094633"].nome_diretor == "Diretor Teste"
    assert por_eol["121000"].nome_escola == "Unidade 121000"
    assert por_eol["121000"].nome_diretor == ""


def test_enriquecer_unidade_tolera_falha_na_consulta_do_diretor() -> None:
    """Mantém dados da unidade quando a consulta do diretor falha."""
    client = FakeClient(
        dados={"094633": {"nome": "EMEF Teste"}},
        falhas_diretores={"094633"},
    )
    unidade = UnidadeEol(
        codigo_eol="094633",
        nome_escola="Unidade 094633",
        sigla_tipo_escola="EMEF",
        nome_dre="DRE",
        sigla_dre="DR",
        codigo_dre="1",
    )

    enriquecida = EolAdapter(client=client).enriquecer_unidades((unidade,))

    assert enriquecida[0].nome_escola == "EMEF Teste"
    assert enriquecida[0].nome_diretor == ""


def test_enriquecer_unidades_usa_fallback_para_falha_inesperada(
    monkeypatch,
) -> None:
    """Mantém dados básicos quando o enriquecimento lança erro."""
    unidade = UnidadeEol(
        codigo_eol="094633",
        nome_escola="Unidade 094633",
        sigla_tipo_escola="EMEF",
        nome_dre="DRE",
        sigla_dre="DR",
        codigo_dre="1",
    )
    adapter = EolAdapter(client=FakeClient())

    def _falhar(_unidade: UnidadeEol) -> UnidadeRecreioEol:
        raise RuntimeError("falha inesperada")

    monkeypatch.setattr(adapter, "_enriquecer_unidade", _falhar)

    enriquecida = adapter.enriquecer_unidades((unidade,))

    assert enriquecida[0].codigo_eol == "094633"
    assert enriquecida[0].nome_escola == "Unidade 094633"
    assert enriquecida[0].email == ""


def test_enriquecer_unidades_ordena_por_nome_e_codigo() -> None:
    """Ordena as unidades enriquecidas por nome de escola e código EOL."""
    client = FakeClient()
    unidades = (
        UnidadeEol(
            codigo_eol="2",
            nome_escola="Bravo",
            sigla_tipo_escola="EMEF",
            nome_dre="DRE",
            sigla_dre="DR",
            codigo_dre="1",
        ),
        UnidadeEol(
            codigo_eol="1",
            nome_escola="Alfa",
            sigla_tipo_escola="EMEF",
            nome_dre="DRE",
            sigla_dre="DR",
            codigo_dre="1",
        ),
    )

    enriquecidas = EolAdapter(client=client).enriquecer_unidades(unidades)

    assert [u.codigo_eol for u in enriquecidas] == ["1", "2"]


def test_enriquecer_unidades_retorna_vazio_sem_unidades() -> None:
    """Devolve tupla vazia quando não há unidades para enriquecer."""
    enriquecidas = EolAdapter(client=FakeClient()).enriquecer_unidades(())

    assert enriquecidas == ()


def test_listar_unidades_diretas_recreio_integra_fluxo() -> None:
    """Integra filtro por tipo de UE, limite e enriquecimento."""
    client = FakeClient(
        unidades=[
            _unidade_bruta("094633", "EMEF"),
            _unidade_bruta("121000", "CEI DIRET"),
            _unidade_bruta("300000", "OUTRO"),
        ],
        diretores={"094633": "Diretor A", "121000": "Diretor B"},
    )

    unidades = EolAdapter(client=client).listar_unidades_diretas_recreio()

    assert [u.codigo_eol for u in unidades] == ["094633", "121000"]
    assert unidades[0].nome_diretor == "Diretor A"
    assert unidades[1].nome_diretor == "Diretor B"


def test_listar_unidades_diretas_recreio_aplica_limite() -> None:
    """Limita a quantidade de unidades antes do enriquecimento."""
    client = FakeClient(
        unidades=[
            _unidade_bruta("094633", "EMEF"),
            _unidade_bruta("121000", "CEI DIRET"),
        ]
    )

    unidades = EolAdapter(client=client).listar_unidades_diretas_recreio(
        limite=1
    )

    assert [u.codigo_eol for u in unidades] == ["094633"]
