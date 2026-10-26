"""Testes dos serializers de inscrições."""

from datetime import date
from types import SimpleNamespace

import pytest
from freezegun import freeze_time

from apps.inscricoes.api.serializers import (
    InscricaoCadastroSerializer,
    InscricaoDetalheSerializer,
    InscricaoListagemSerializer,
    ParticipanteRedeSerializer,
    PoloElegivelSerializer,
)
from apps.inscricoes.constants import (
    Deficiencias,
    GrupoInscricao,
    ProblemasSaude,
    StatusInscricao,
    TipoEstudante,
)

pytestmark = pytest.mark.django_db


def test_serializer_basico_retorna_campos_e_choices(
    inscricao_factory,
) -> None:
    """O contrato básico expõe campos editáveis e status somente leitura."""
    inscricao = inscricao_factory()

    dados = InscricaoCadastroSerializer(inscricao).data

    assert dados["uuid"] == str(inscricao.uuid)
    assert dados["tipo_logradouro"] == "Rua"
    assert dados["status"] == StatusInscricao.RASCUNHO


def test_serializer_basico_marca_status_e_metadados_como_somente_leitura(
    inscricao_factory,
) -> None:
    """Status não pode ser controlado pelo payload do cliente."""
    inscricao = inscricao_factory()
    serializer = InscricaoCadastroSerializer(
        inscricao,
        data={
            "tipo_estudante": TipoEstudante.ESTUDANTE_EXTERNO,
            "grupo": GrupoInscricao.QUATRO_A_14_ANOS,
            "status": StatusInscricao.COMPLETA,
            "ativo": False,
        },
        partial=True,
    )

    assert serializer.is_valid(), serializer.errors
    assert "status" not in serializer.validated_data
    assert "ativo" not in serializer.validated_data


def test_serializer_aceita_multiplas_deficiencias_e_problemas_de_saude() -> (
    None
):
    """As seleções múltiplas preservam todas as opções válidas."""
    serializer = InscricaoCadastroSerializer(
        data={
            "deficiencias": [Deficiencias.AUTISMO, Deficiencias.SURDOCEGUEIRA],
            "problemas_saude": [
                ProblemasSaude.ASMA_OU_BRONQUITE,
                ProblemasSaude.DIABETES,
            ],
        },
        partial=True,
    )

    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data["deficiencias"] == [
        Deficiencias.AUTISMO,
        Deficiencias.SURDOCEGUEIRA,
    ]
    assert serializer.validated_data["problemas_saude"] == [
        ProblemasSaude.ASMA_OU_BRONQUITE,
        ProblemasSaude.DIABETES,
    ]


def test_serializer_rejeita_opcao_invalida_em_selecao_multipla() -> None:
    """Cada item das listas precisa pertencer às choices do campo."""
    serializer = InscricaoCadastroSerializer(
        data={"deficiencias": [Deficiencias.AUTISMO, "INVALIDA"]},
        partial=True,
    )

    assert not serializer.is_valid()
    assert "deficiencias" in serializer.errors


def test_serializer_expoe_idade_somente_leitura(inscricao_factory) -> None:
    """A resposta devolve a idade calculada e ignora o valor enviado."""
    inscricao = inscricao_factory(data_nascimento=date(2015, 5, 19))

    with freeze_time("2026-05-18 12:00:00"):
        dados = InscricaoCadastroSerializer(inscricao).data
        detalhe = InscricaoDetalheSerializer(inscricao).data

    assert dados["idade"] == 10
    assert detalhe["idade"] == 10

    serializer = InscricaoCadastroSerializer(
        inscricao,
        data={"idade": 99},
        partial=True,
    )

    assert serializer.is_valid(), serializer.errors
    assert "idade" not in serializer.validated_data


def test_serializer_devolve_idade_nula_sem_nascimento(
    inscricao_factory,
) -> None:
    """Sem data de nascimento, o contrato devolve idade nula."""
    inscricao = inscricao_factory(data_nascimento=None)

    assert InscricaoCadastroSerializer(inscricao).data["idade"] is None


def test_serializer_participante_expoe_idade() -> None:
    """A consulta da rede devolve a idade e a omite sem data."""
    participante = _participante_rede()

    with freeze_time("2026-10-16 12:00:00"):
        dados = ParticipanteRedeSerializer(participante).data

    assert dados["idade"] == 13

    participante.data_nascimento = ""
    assert ParticipanteRedeSerializer(participante).data["idade"] is None


def _participante_rede() -> SimpleNamespace:
    """Monta o mínimo que o contrato da consulta da rede lê."""
    return SimpleNamespace(
        codigo_aluno=1,
        nome_aluno="Ana",
        data_nascimento="2013-10-16",
        nome_responsavel="",
        responsavel_nome_social="",
        cep="",
        logradouro="",
        numero="",
        complemento="",
        bairro="",
        cidade="",
        celular_responsavel="",
        telefone_contato_2="",
        email="",
        nome_turma="",
        ano="",
        unidade_educacional="",
        unidade_educacional_codigo_eol="",
        unidade_educacional_tipo="",
    )


def test_serializer_recebe_grupo_e_ignora_campos_derivados(
    inscricao_factory,
) -> None:
    """O contrato grava o grupo e ignora idade e aluno da rede."""
    inscricao = inscricao_factory(
        tipo_estudante=TipoEstudante.ESTUDANTE_DA_REDE,
        unidade_educacional="EMEI Teste - 094633",
        unidade_educacional_codigo_eol="094633",
        unidade_educacional_tipo="EMEI",
        nome_turma="7C",
        ano="7",
        pode_ir_embora_sozinho=False,
        responsavel_retirada="Maria",
        autoriza_uso_piscina=True,
    )

    dados = InscricaoCadastroSerializer(inscricao).data

    assert dados["unidade_educacional"] == "EMEI Teste - 094633"
    assert dados["unidade_educacional_codigo_eol"] == "094633"
    assert dados["unidade_educacional_tipo"] == "EMEI"
    assert dados["nome_turma"] == "7C"
    assert dados["ano"] == "7"
    assert dados["pode_ir_embora_sozinho"] is False
    assert dados["responsavel_retirada"] == "Maria"
    assert dados["autoriza_uso_piscina"] is True
    assert dados["aluno_rede_municipal"] is True

    serializer = InscricaoCadastroSerializer(
        inscricao,
        data={"idade": 99, "aluno_rede_municipal": False},
        partial=True,
    )

    assert serializer.is_valid(), serializer.errors
    assert "idade" not in serializer.validated_data
    assert "aluno_rede_municipal" not in serializer.validated_data


def test_serializer_detalhe_aninha_polo_e_edicao(
    inscricao_completa_factory,
) -> None:
    """O detalhe retorna UUID e nomes resumidos das relações."""
    inscricao = inscricao_completa_factory()

    dados = InscricaoDetalheSerializer(inscricao).data

    assert dados["polo"] == {
        "uuid": str(inscricao.polo.uuid),
        "nome_polo": inscricao.polo.nome_polo,
    }
    assert dados["edicao"] == {
        "uuid": str(inscricao.edicao.uuid),
        "nome": inscricao.edicao.nome,
    }


def test_serializer_listagem_expoe_nome_do_polo(
    inscricao_completa_factory,
) -> None:
    """A listagem oferece o identificador e o nome do polo."""
    inscricao = inscricao_completa_factory()

    dados = InscricaoListagemSerializer(inscricao).data

    assert str(dados["polo"]) == str(inscricao.polo.uuid)
    assert dados["polo_nome"] == inscricao.polo.nome_polo


def test_serializer_polo_elegivel_eh_somente_leitura(
    polo_factory,
) -> None:
    """O contrato de seleção retorna somente dados do polo."""
    polo = polo_factory()

    serializer = PoloElegivelSerializer(polo)

    assert serializer.data["nome_polo"] == polo.nome_polo
    assert set(serializer.fields) == {
        "uuid",
        "codigo_eol",
        "nome_polo",
        "dre_codigo_eol",
        "dre_nome",
    }
