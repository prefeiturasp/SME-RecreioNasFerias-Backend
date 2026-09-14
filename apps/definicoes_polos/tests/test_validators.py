"""Testes das validações de definições de polos."""

import pytest
from django.core.exceptions import ValidationError

from apps.definicoes_polos import validators
from apps.definicoes_polos.validators import (
    validar_definicao_polo,
    validar_projecao_inscritos,
    validar_unicidade_polo_edicao,
)

pytestmark = pytest.mark.django_db


def _mensagens(exc: ValidationError) -> list[str]:
    """Extrai mensagens de uma ValidationError."""
    if hasattr(exc, "message_dict"):
        return [
            mensagem
            for mensagens in exc.message_dict.values()
            for mensagem in mensagens
        ]
    return exc.messages


def test_rejeita_par_polo_edicao_duplicado(definicao_polo_factory) -> None:
    """Uma participação não pode repetir polo e edição."""
    primeira = definicao_polo_factory()
    segunda = definicao_polo_factory.build(
        polo=primeira.polo,
        edicao=primeira.edicao,
    )

    with pytest.raises(ValidationError) as contexto:
        validar_unicidade_polo_edicao(segunda)

    assert validators.MENSAGEM_PARTICIPACAO_DUPLICADA in _mensagens(
        contexto.value
    )


def test_permite_revalidar_a_propria_participacao(
    definicao_polo_factory,
) -> None:
    """Uma participação existente não conflita consigo mesma."""
    definicao = definicao_polo_factory()

    assert validar_unicidade_polo_edicao(definicao) is None


def test_rejeita_projecao_negativa(definicao_polo_factory) -> None:
    """A validação explícita rejeita projeção negativa."""
    definicao = definicao_polo_factory.build(projecao_inscritos=-1)

    with pytest.raises(ValidationError) as contexto:
        validar_projecao_inscritos(definicao)

    assert validators.MENSAGEM_PROJECAO_INVALIDA in _mensagens(contexto.value)


def test_permite_projecao_nula_antes_da_validacao_estrutural(
    definicao_polo_factory,
) -> None:
    """O validador de domínio não duplica a validação estrutural do Django."""
    definicao = definicao_polo_factory.build(projecao_inscritos=None)

    assert validar_projecao_inscritos(definicao) is None


def test_agregador_retorna_sem_erros(definicao_polo_factory) -> None:
    """O agregador permite uma definição válida."""
    assert validar_definicao_polo(definicao_polo_factory()) is None


def test_agregador_reune_erros_dos_validadores(
    definicao_polo_factory,
    monkeypatch,
) -> None:
    """O agregador reúne mensagens de todos os validadores."""
    definicao = definicao_polo_factory.build()

    def _erro_unicidade(_definicao):
        raise ValidationError({"__all__": "Erro de vínculo."})

    def _erro_projecao(_definicao):
        raise ValidationError({"projecao_inscritos": "Erro de projeção."})

    monkeypatch.setattr(
        validators, "validar_unicidade_polo_edicao", _erro_unicidade
    )
    monkeypatch.setattr(
        validators, "validar_projecao_inscritos", _erro_projecao
    )

    with pytest.raises(ValidationError) as contexto:
        validar_definicao_polo(definicao)

    assert "Erro de vínculo." in _mensagens(contexto.value)
    assert "Erro de projeção." in _mensagens(contexto.value)
