"""Testes das validações do domínio de inscrições."""

from datetime import date
from types import SimpleNamespace

import pytest
from django.core.exceptions import ValidationError
from freezegun import freeze_time

from apps.inscricoes import validators
from apps.inscricoes.constants import (
    GrupoInscricao,
    StatusInscricao,
    TipoEstudante,
)
from apps.inscricoes.validators import (
    calcular_idade_cheia,
    inscricao_eh_completa,
    validar_informacoes_de_saude,
    validar_inscricao,
    validar_polo_e_dre,
    validar_tipo_e_grupo,
    validar_unicidade,
)
from apps.polos.constants import StatusPolo

pytestmark = pytest.mark.django_db


def _mensagens(exc: ValidationError) -> list[str]:
    """Extrai mensagens de qualquer formato de ValidationError."""
    if hasattr(exc, "message_dict"):
        return [
            mensagem
            for mensagens in exc.message_dict.values()
            for mensagem in mensagens
        ]
    return exc.messages


def test_completude_exige_tipo_logradouro(inscricao_completa_factory) -> None:
    """Tipo de logradouro passou a integrar a régua da primeira fase."""
    inscricao = inscricao_completa_factory(tipo_logradouro="")

    assert inscricao_eh_completa(inscricao) is False


def test_completude_exige_codigo_eol_da_rede(
    inscricao_completa_factory,
) -> None:
    """Estudante da rede precisa de Código EOL para completar."""
    inscricao = inscricao_completa_factory(
        tipo_estudante=TipoEstudante.ESTUDANTE_DA_REDE,
        codigo_eol="",
        cpf="",
    )

    assert inscricao_eh_completa(inscricao) is False


def test_completude_da_rede_exige_saida_retirada_e_piscina(
    inscricao_completa_factory,
) -> None:
    """Sem as três respostas, a inscrição da rede fica rascunho."""
    inscricao = inscricao_completa_factory(
        tipo_estudante=TipoEstudante.ESTUDANTE_DA_REDE,
        codigo_eol="6034178",
    )

    assert inscricao_eh_completa(inscricao) is False
    assert inscricao.status == StatusInscricao.RASCUNHO

    inscricao.pode_ir_embora_sozinho = False
    inscricao.autoriza_uso_piscina = True
    inscricao.responsavel_retirada = "   "
    inscricao.save()

    assert inscricao.status == StatusInscricao.RASCUNHO


def test_completude_da_rede_aceita_resposta_negativa(
    inscricao_completa_factory,
) -> None:
    """Não em saída e piscina conta como respondido."""
    inscricao = inscricao_completa_factory(
        tipo_estudante=TipoEstudante.ESTUDANTE_DA_REDE,
        codigo_eol="6034178",
        pode_ir_embora_sozinho=False,
        autoriza_uso_piscina=False,
        responsavel_retirada="Maria",
    )

    assert inscricao_eh_completa(inscricao) is True
    assert inscricao.status == StatusInscricao.COMPLETA


def test_completude_externa_nao_exige_grupo(
    inscricao_completa_factory,
) -> None:
    """Estudante externo completa sem saída, retirada e piscina."""
    inscricao = inscricao_completa_factory()

    assert inscricao_eh_completa(inscricao) is True
    assert inscricao.status == StatusInscricao.COMPLETA


def test_completude_exige_cpf_de_externo(inscricao_completa_factory) -> None:
    """Estudante externo precisa de CPF para completar."""
    inscricao = inscricao_completa_factory(cpf="")

    assert inscricao_eh_completa(inscricao) is False


def test_valida_grupos_de_rede_e_aceita_grupo_maior(
    inscricao_completa_factory,
) -> None:
    """Grupos infantis exigem rede, enquanto 4 a 14 aceita externo."""
    infantil = inscricao_completa_factory(
        grupo=GrupoInscricao.MINI_GRUPO_I,
        tipo_estudante=TipoEstudante.ESTUDANTE_DA_REDE,
    )
    maior = inscricao_completa_factory(
        grupo=GrupoInscricao.QUATRO_A_14_ANOS,
        tipo_estudante=TipoEstudante.ESTUDANTE_EXTERNO,
    )

    assert validar_tipo_e_grupo(infantil) is None
    assert validar_tipo_e_grupo(maior) is None


def test_rejeita_grupo_infantil_externo(inscricao_factory) -> None:
    """Berçário e Mini Grupo rejeitam estudante externo."""
    inscricao = inscricao_factory.build(
        grupo=GrupoInscricao.BERCARIO_II,
        tipo_estudante=TipoEstudante.ESTUDANTE_EXTERNO,
    )

    with pytest.raises(ValidationError) as contexto:
        validar_tipo_e_grupo(inscricao)

    assert validators.MENSAGEM_GRUPO_REDE in _mensagens(contexto.value)


def test_valida_polo_oficial_ativo_e_dre(inscricao_completa_factory) -> None:
    """Polo oficialmente definido e ativo é aceito quando a DRE coincide."""
    inscricao = inscricao_completa_factory()

    assert validar_polo_e_dre(inscricao) is None


def test_rejeita_polo_inativo(inscricao_completa_factory) -> None:
    """Polo inativo não pode ser usado mesmo com histórico oficial."""
    inscricao = inscricao_completa_factory()
    inscricao.polo.status = StatusPolo.INATIVO
    inscricao.polo.save()

    with pytest.raises(ValidationError) as contexto:
        validar_polo_e_dre(inscricao)

    assert validators.MENSAGEM_POLO_INVALIDO in _mensagens(contexto.value)


def test_rejeita_polo_sem_definicao_oficial(
    inscricao_factory,
    polo_factory,
) -> None:
    """Polo sem histórico oficial não é elegível."""
    polo = polo_factory()
    inscricao = inscricao_factory.build(polo=polo)

    with pytest.raises(ValidationError) as contexto:
        validar_polo_e_dre(inscricao)

    assert validators.MENSAGEM_POLO_INVALIDO in _mensagens(contexto.value)


def test_rejeita_dre_diferente(inscricao_completa_factory) -> None:
    """A inscrição deve pertencer à DRE do polo selecionado."""
    inscricao = inscricao_completa_factory()
    inscricao.dre_codigo_eol = "999999"

    with pytest.raises(ValidationError) as contexto:
        validar_polo_e_dre(inscricao)

    assert validators.MENSAGEM_DRE_POLO in _mensagens(contexto.value)


def test_polo_ausente_nao_bloqueia_rascunho(inscricao_factory) -> None:
    """Rascunhos podem ser salvos sem polo."""
    inscricao = inscricao_factory()

    assert validar_polo_e_dre(inscricao) is None


def test_rejeita_cpf_e_codigo_eol_duplicados(
    inscricao_completa_factory, inscricao_factory
) -> None:
    """CPF e Código EOL são identificadores únicos dentro do polo."""
    primeiro = inscricao_completa_factory(
        cpf="11111111111",
        codigo_eol="1234567",
    )
    segundo = inscricao_factory.build(
        polo=primeiro.polo,
        edicao=primeiro.edicao,
        dre_codigo_eol=primeiro.dre_codigo_eol,
        dre_nome=primeiro.dre_nome,
        cpf=primeiro.cpf,
        codigo_eol=primeiro.codigo_eol,
    )

    with pytest.raises(ValidationError) as contexto:
        validar_unicidade(segundo)

    assert validators.MENSAGEM_DUPLICIDADE in _mensagens(contexto.value)


def test_unicidade_ignora_identificadores_vazios_e_o_proprio_registro(
    inscricao_completa_factory,
) -> None:
    """Valores ausentes e a própria inscrição não geram conflito."""
    inscricao = inscricao_completa_factory(cpf="", codigo_eol="")

    assert validar_unicidade(inscricao) is None


@pytest.mark.parametrize(
    ("dados", "campo"),
    [
        ({"possui_deficiencia": True, "deficiencias": []}, "deficiencias"),
        (
            {"deficiencias": ["OUTRA"], "outra_deficiencia": ""},
            "outra_deficiencia",
        ),
        (
            {"possui_problema_saude": True, "problemas_saude": []},
            "problemas_saude",
        ),
        (
            {"problemas_saude": ["OUTRO"], "outro_problema_saude": ""},
            "outro_problema_saude",
        ),
        (
            {
                "usuario_medicacao_ou_tratamento_continuo": True,
                "medicacao_ou_tratamento_continuo": "",
            },
            "medicacao_ou_tratamento_continuo",
        ),
        (
            {
                "possui_restricao_medicamento_pronto_atendimento": True,
                "restricao_medicamento_pronto_atendimento": "",
            },
            "restricao_medicamento_pronto_atendimento",
        ),
        (
            {"possui_convenio_medico": True, "convenio_medico": ""},
            "convenio_medico",
        ),
    ],
)
def test_validar_informacoes_de_saude_rejeita_detalhes_ausentes(
    dados, campo
) -> None:
    """Cada informação de saúde marcada exige seu detalhe correspondente."""
    dados_validos = {
        "possui_deficiencia": False,
        "deficiencias": [],
        "outra_deficiencia": "",
        "possui_problema_saude": False,
        "problemas_saude": [],
        "outro_problema_saude": "",
        "usuario_medicacao_ou_tratamento_continuo": False,
        "medicacao_ou_tratamento_continuo": "",
        "possui_restricao_medicamento_pronto_atendimento": False,
        "restricao_medicamento_pronto_atendimento": "",
        "possui_convenio_medico": False,
        "convenio_medico": "",
    }
    inscricao = SimpleNamespace(**{**dados_validos, **dados})

    with pytest.raises(ValidationError) as contexto:
        validar_informacoes_de_saude(inscricao)

    assert list(contexto.value.message_dict) == [campo]


def test_validar_informacoes_de_saude_aceita_detalhes_preenchidos() -> None:
    """Dados de saúde completos percorrem todas as regras sem erro."""
    inscricao = SimpleNamespace(
        possui_deficiencia=True,
        deficiencias=["OUTRA"],
        outra_deficiencia="Descrição da deficiência",
        possui_problema_saude=True,
        problemas_saude=["OUTRO"],
        outro_problema_saude="Descrição do problema de saúde",
        usuario_medicacao_ou_tratamento_continuo=True,
        medicacao_ou_tratamento_continuo="Medicação informada",
        possui_restricao_medicamento_pronto_atendimento=True,
        restricao_medicamento_pronto_atendimento="Restrição informada",
        possui_convenio_medico=True,
        convenio_medico="Convênio informado",
    )

    assert validar_informacoes_de_saude(inscricao) is None


def test_validar_inscricao_agrega_erros(
    monkeypatch, inscricao_factory
) -> None:
    """O agregador reúne erros de todos os validadores."""
    inscricao = inscricao_factory()

    def erro_tipo(_inscricao):
        raise ValidationError({"tipo_estudante": "Erro de tipo."})

    def erro_polo(_inscricao):
        raise ValidationError("Erro genérico.")

    monkeypatch.setattr(validators, "validar_tipo_e_grupo", erro_tipo)
    monkeypatch.setattr(validators, "validar_polo_e_dre", erro_polo)

    with pytest.raises(ValidationError) as contexto:
        validar_inscricao(inscricao)

    assert "Erro de tipo." in _mensagens(contexto.value)
    assert "Erro genérico." in _mensagens(contexto.value)


def test_validar_inscricao_sem_erros(inscricao_factory) -> None:
    """A inscrição válida percorre todos os validadores até o final."""
    inscricao = inscricao_factory.build()

    assert validar_inscricao(inscricao) is None


def test_idade_cheia_antes_do_aniversario() -> None:
    """Seis anos, onze meses e trinta dias contam como seis."""
    with freeze_time("2026-05-18 12:00:00"):
        assert calcular_idade_cheia(date(2019, 5, 19)) == 6


def test_idade_cheia_no_dia_do_aniversario() -> None:
    """A idade aumenta no dia do aniversário."""
    with freeze_time("2026-05-19 12:00:00"):
        assert calcular_idade_cheia(date(2019, 5, 19)) == 7


def test_idade_cheia_trata_29_de_fevereiro() -> None:
    """Em ano não bissexto, o aniversário de 29/02 vale 1º de março."""
    nascimento = date(2020, 2, 29)

    with freeze_time("2021-02-28 12:00:00"):
        assert calcular_idade_cheia(nascimento) == 0
    with freeze_time("2021-03-01 12:00:00"):
        assert calcular_idade_cheia(nascimento) == 1
    with freeze_time("2024-02-29 12:00:00"):
        assert calcular_idade_cheia(nascimento) == 4


def test_idade_cheia_sem_data_de_nascimento() -> None:
    """Sem data de nascimento, a idade não é calculada."""
    assert calcular_idade_cheia(None) is None
