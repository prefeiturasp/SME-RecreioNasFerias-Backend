"""Testes do serializer de polos."""

import pytest

from apps.integracoes.eol.port import DreEol, TipoEscolaEol
from apps.polos.api.serializers import (
    DreSerializer,
    PoloSerializer,
    PopularUnidadesDiretasSerializer,
    TipoEscolaSerializer,
)
from apps.polos.constants import StatusPolo, TipoPolo

pytestmark = pytest.mark.django_db


def test_serializer_retorna_campos_publicos_do_polo(polo_factory) -> None:
    """A resposta contém os campos públicos do contrato."""
    polo = polo_factory()

    dados = PoloSerializer(polo).data

    assert dados["uuid"] == str(polo.uuid)
    assert dados["codigo_eol"] == polo.codigo_eol
    assert dados["nome_polo"] == polo.nome_polo
    assert dados["tipo"] == TipoPolo.PENDENTE
    assert dados["status"] == StatusPolo.ATIVO
    assert dados["gestao"] == "parceira"
    assert dados["complemento"] == ""


def test_serializer_marca_campos_gerenciados_como_somente_leitura() -> None:
    """Campos gerenciados pelo sistema não entram nos dados validados."""
    serializer = PoloSerializer(
        data={
            "codigo_eol": "019360",
            "nome_polo": "Polo novo",
            "nome_osc": "OSC nova",
            "dre_nome": "DRE nova",
            "dre_codigo_eol": "108200",
            "gestao": "parceira",
            "tipo_ue": "CEU",
            "quantidade_maxima_alunos": 250,
            "cep": "01001000",
            "tipo_logradouro": "Rua",
            "logradouro": "Principal",
            "bairro": "Centro",
            "numero": "10",
            "nome_gestor": "Gestor",
            "email": "gestor@example.com",
            "telefone": "1130000000",
            "tipo": TipoPolo.OFICIAL,
            "status": StatusPolo.INATIVO,
            "ativo": False,
            "criado_em": "2026-01-01T00:00:00Z",
            "atualizado_em": "2026-01-01T00:00:00Z",
        }
    )

    assert serializer.is_valid(), serializer.errors
    assert "ativo" not in serializer.validated_data
    assert "criado_em" not in serializer.validated_data
    assert "atualizado_em" not in serializer.validated_data
    assert serializer.validated_data["tipo"] == TipoPolo.OFICIAL


def test_serializer_exige_campos_obrigatorios() -> None:
    """O contrato rejeita payload sem os campos obrigatórios."""
    serializer = PoloSerializer(data={"nome_polo": "Incompleto"})

    assert not serializer.is_valid()
    assert "codigo_eol" in serializer.errors
    assert "nome_osc" in serializer.errors
    assert "gestao" not in serializer.errors
    assert "complemento" not in serializer.errors


def test_serializer_permite_omitir_gestao_com_default() -> None:
    """Gestão pode ser omitida porque possui default no modelo."""
    dados = {
        "codigo_eol": "019361",
        "nome_polo": "Polo com default",
        "nome_osc": "OSC",
        "dre_nome": "DRE",
        "dre_codigo_eol": "108201",
        "tipo_ue": "EMEF",
        "quantidade_maxima_alunos": 100,
        "cep": "01001000",
        "tipo_logradouro": "Rua",
        "logradouro": "Principal",
        "bairro": "Centro",
        "numero": "10",
        "nome_gestor": "Gestor",
        "email": "gestor-default@example.com",
        "telefone": "1130000000",
    }
    serializer = PoloSerializer(data=dados)

    assert serializer.is_valid(), serializer.errors
    assert "gestao" not in serializer.validated_data


def test_serializer_retorna_dre_normalizada() -> None:
    """O serializer de DRE expõe os três campos normalizados."""
    dre = DreEol(
        codigo_dre="108100",
        nome_dre="DRE Butantã",
        sigla_dre="DRE - BT",
    )

    dados = DreSerializer(dre).data

    assert dados == {
        "codigo_dre": "108100",
        "nome_dre": "DRE Butantã",
        "sigla_dre": "DRE - BT",
    }


def test_serializer_retorna_tipo_de_escola_normalizado() -> None:
    """O serializer de tipo de escola expõe código e sigla."""
    tipo = TipoEscolaEol(codigo=1, descricao_sigla="EMEF")

    dados = TipoEscolaSerializer(tipo).data

    assert dados == {"codigo": 1, "descricao_sigla": "EMEF"}


def test_serializer_retorna_resultado_da_populacao(polo_factory) -> None:
    """O contrato da população expõe totais e os polos criados."""
    polo = polo_factory()

    dados = PopularUnidadesDiretasSerializer(
        {
            "total_consultados": 1,
            "total_novos": 1,
            "total_ja_existentes": 0,
            "unidades_novas": [polo],
            "executada": True,
            "motivo_ignorada": None,
            "ultima_execucao_em": None,
        }
    ).data

    assert dados["total_consultados"] == 1
    assert dados["total_novos"] == 1
    assert dados["executada"] is True
    assert dados["motivo_ignorada"] is None
    assert dados["ultima_execucao_em"] is None
    assert dados["unidades_novas"][0]["uuid"] == str(polo.uuid)
