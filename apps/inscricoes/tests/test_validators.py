"""Testes das validações do domínio de inscrições."""

import pytest
from django.core.exceptions import ValidationError

from apps.inscricoes import validators
from apps.inscricoes.constants import GrupoInscricao, TipoEstudante
from apps.inscricoes.validators import (
    inscricao_eh_completa,
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
