"""Testes unitarios do adaptador CoreSSO."""

from __future__ import annotations

import pytest

from apps.integracoes.coresso.adapter import CoressoAdapter
from apps.integracoes.coresso.exceptions import CoressoContratoError

TEST_RF = "0000001"
TEST_NOME = "Pessoa Teste"
TEST_EMAIL = "usuario.teste@example.test"
TEST_CPF = "cpf00000000"
TEST_AUTH_INPUT = "credencial-teste"


class FakeClient:
    """Client fake para testes do adaptador."""

    def __init__(self, payload: dict[str, object]) -> None:
        """Inicializa o fake com o payload que será devolvido."""
        self.payload = payload
        self.calls: list[tuple[str, str]] = []

    def autenticar(self, rf: str, senha: str) -> dict[str, object]:
        """Retorna payload fixo e registra os argumentos recebidos."""
        self.calls.append((rf, senha))
        return self.payload


def test_adapter_usa_cargo_sobreposto_como_cargo_efetivo() -> None:
    """Aplica a precedência de cargosSobrePosto sobre cargos."""
    client = FakeClient(
        {
            "usuarioId": "abc",
            "nome": TEST_NOME,
            "codigoRf": TEST_RF,
            "numeroDocumento": TEST_CPF,
            "email": TEST_EMAIL,
            "perfis": [],
            "cargos": [{"codigo": 3344, "nome": "Professor"}],
            "cargosSobrePosto": [
                {"codigo": 2640, "nome": "Assistente Tecnico"}
            ],
            "unidadesLotacao": [{"codigo": "094633", "nomeUnidade": "EMEF"}],
            "unidadeExercicio": {
                "codigo": "121000",
                "nomeUnidade": "COCEU",
            },
        }
    )

    identidade = CoressoAdapter(client=client).autenticar(
        TEST_RF,
        TEST_AUTH_INPUT,
    )

    assert client.calls == [(TEST_RF, TEST_AUTH_INPUT)]
    assert [cargo.codigo_cargo for cargo in identidade.cargos] == [3344]
    assert [cargo.codigo_cargo for cargo in identidade.cargos_sobrepostos] == [
        2640
    ]
    assert [cargo.codigo_cargo for cargo in identidade.cargos_efetivos] == [
        2640
    ]
    assert identidade.unidade_exercicio is not None
    assert identidade.unidade_exercicio.codigo == "121000"


def test_adapter_faz_fallback_para_cargos_quando_nao_ha_sobreposto() -> None:
    """Usa cargos normais quando não há cargos sobrepostos."""
    client = FakeClient(
        {
            "usuarioId": "abc",
            "nome": TEST_NOME,
            "codigoRf": TEST_RF,
            "numeroDocumento": TEST_CPF,
            "email": TEST_EMAIL,
            "perfis": [],
            "cargos": [{"codigo": 3344, "nome": "Professor"}],
            "cargosSobrePosto": [],
            "unidadesLotacao": [],
            "unidadeExercicio": None,
        }
    )

    identidade = CoressoAdapter(client=client).autenticar(
        TEST_RF,
        TEST_AUTH_INPUT,
    )

    assert [cargo.codigo_cargo for cargo in identidade.cargos_efetivos] == [
        3344
    ]


def test_adapter_rejeita_payload_sem_codigo_rf() -> None:
    """Falha quando o payload não traz os campos obrigatórios."""
    client = FakeClient({"nome": TEST_NOME})

    with pytest.raises(CoressoContratoError, match="codigoRf"):
        CoressoAdapter(client=client).autenticar(TEST_RF, TEST_AUTH_INPUT)


def test_adapter_campos_opcionais_ausentes() -> None:
    """Trata payload mínimo sem campos opcionais do CoreSSO."""
    client = FakeClient({"nome": TEST_NOME, "codigoRf": TEST_RF})

    identidade = CoressoAdapter(client=client).autenticar(
        TEST_RF, TEST_AUTH_INPUT
    )

    assert identidade.usuario_id_externo is None
    assert identidade.email is None
    assert identidade.cpf is None
    assert identidade.perfis == ()
    assert identidade.cargos == ()
    assert identidade.cargos_sobrepostos == ()
    assert identidade.cargos_efetivos == ()
    assert identidade.unidades_lotacao == ()
    assert identidade.unidade_exercicio is None


def test_adapter_normaliza_perfis() -> None:
    """Normaliza perfis ignorando itens vazios."""
    client = FakeClient(
        {
            "nome": TEST_NOME,
            "codigoRf": TEST_RF,
            "perfis": ["DIRETOR", "  "],
        }
    )

    identidade = CoressoAdapter(client=client).autenticar(
        TEST_RF, TEST_AUTH_INPUT
    )

    assert identidade.perfis == ("DIRETOR",)


@pytest.mark.parametrize("cargos", ["nao-lista", [123]])
def test_adapter_rejeita_cargos_invalidos(cargos: object) -> None:
    """Falha quando o campo de cargos foge do contrato esperado."""
    client = FakeClient(
        {"nome": TEST_NOME, "codigoRf": TEST_RF, "cargos": cargos}
    )

    with pytest.raises(CoressoContratoError, match="cargos"):
        CoressoAdapter(client=client).autenticar(TEST_RF, TEST_AUTH_INPUT)


@pytest.mark.parametrize("unidades", ["nao-lista", [123]])
def test_adapter_rejeita_unidades_invalidas(unidades: object) -> None:
    """Falha quando o campo de unidades foge do contrato esperado."""
    client = FakeClient(
        {
            "nome": TEST_NOME,
            "codigoRf": TEST_RF,
            "unidadesLotacao": unidades,
        }
    )

    with pytest.raises(CoressoContratoError, match="unidadesLotacao"):
        CoressoAdapter(client=client).autenticar(TEST_RF, TEST_AUTH_INPUT)


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [
        (None, None),
        ("", None),
        (True, None),
        (3344, 3344),
        ("3344", 3344),
        ("abc", None),
        ([], None),
    ],
)
def test_adapter_inteiro_opcional(
    valor: object,
    esperado: int | None,
) -> None:
    """Converte valores numéricos textuais em inteiro quando possível."""
    assert CoressoAdapter._inteiro_opcional(valor) == esperado
