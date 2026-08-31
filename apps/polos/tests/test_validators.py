"""Testes das validações centralizadas de polos."""

import pytest
from django.core.exceptions import ValidationError

from apps.polos import validators
from apps.polos.validators import (
    validar_codigo_eol_unico,
    validar_nome_unico,
    validar_polo,
)

pytestmark = pytest.mark.django_db


def _mensagens(exc: ValidationError) -> list[str]:
    """Extrai todas as mensagens de uma ValidationError."""
    if hasattr(exc, "message_dict"):
        return [
            mensagem
            for mensagens in exc.message_dict.values()
            for mensagem in mensagens
        ]
    return exc.messages


def test_rejeita_nome_duplicado_sem_considerar_maiusculas(
    polo_factory,
) -> None:
    """Nomes repetidos são inválidos mesmo com diferença de caixa."""
    polo_factory(nome_polo="Polo Central")
    segundo = polo_factory.build(nome_polo="polo central")

    with pytest.raises(ValidationError) as contexto:
        validar_nome_unico(segundo)

    assert validators.MENSAGEM_NOME_DUPLICADO in _mensagens(contexto.value)


def test_rejeita_codigo_eol_duplicado(polo_factory) -> None:
    """Códigos EOL repetidos são inválidos."""
    polo_factory(codigo_eol="019360")
    segundo = polo_factory.build(codigo_eol="019360")

    with pytest.raises(ValidationError) as contexto:
        validar_codigo_eol_unico(segundo)

    assert validators.MENSAGEM_CODIGO_DUPLICADO in _mensagens(contexto.value)


def test_permite_revalidar_o_proprio_polo(polo_factory) -> None:
    """Um polo existente não conflita consigo mesmo."""
    polo = polo_factory()

    assert validar_nome_unico(polo) is None
    assert validar_codigo_eol_unico(polo) is None
    assert validar_polo(polo) is None


def test_validar_polo_agrega_erros_dos_validadores(
    polo_factory,
    monkeypatch,
) -> None:
    """A validação agregadora reúne erros de todos os validadores."""
    polo = polo_factory.build()

    def _levanta_nome(_polo: object) -> None:
        raise ValidationError({"nome_polo": "Erro de nome."})

    def _levanta_codigo(_polo: object) -> None:
        raise ValidationError({"codigo_eol": "Erro de código."})

    monkeypatch.setattr(validators, "validar_nome_unico", _levanta_nome)
    monkeypatch.setattr(
        validators, "validar_codigo_eol_unico", _levanta_codigo
    )

    with pytest.raises(ValidationError) as contexto:
        validar_polo(polo)

    assert "Erro de nome." in _mensagens(contexto.value)
    assert "Erro de código." in _mensagens(contexto.value)


def test_validar_polo_agrega_erro_sem_dicionario(
    polo_factory,
    monkeypatch,
) -> None:
    """Erros simples também são normalizados pelo agregador."""
    polo = polo_factory.build()

    def _levanta_erro_simples(_polo: object) -> None:
        raise ValidationError("Erro genérico.")

    monkeypatch.setattr(
        validators,
        "validar_nome_unico",
        _levanta_erro_simples,
    )

    with pytest.raises(ValidationError) as contexto:
        validar_polo(polo)

    assert "Erro genérico." in _mensagens(contexto.value)
