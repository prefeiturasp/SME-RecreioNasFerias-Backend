"""Testes das validações centralizadas de edições."""

from datetime import date

import pytest
from django.core.exceptions import ValidationError
from freezegun import freeze_time

from apps.edicoes import validators
from apps.edicoes.constants import StatusEdicao
from apps.edicoes.validators import (
    MENSAGEM_EDICAO_ATIVA_DUPLICADA,
    MENSAGEM_EDICAO_ENCERRADA,
    MENSAGEM_NOME_DUPLICADO,
    MENSAGEM_PERIODO_DUPLICADO,
    validar_edicao,
    validar_periodos,
    validar_unicidade_ativa,
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
    edicao_factory,
) -> None:
    """Nomes repetidos são inválidos mesmo com diferença de caixa."""
    edicao_factory(nome="Primeira Edição")
    segunda = edicao_factory.build(nome="primeira edição")

    with pytest.raises(ValidationError) as contexto:
        segunda.save()

    assert MENSAGEM_NOME_DUPLICADO in _mensagens(contexto.value)


def test_rejeita_sobreposicao_do_periodo_da_edicao(edicao_factory) -> None:
    """Períodos de edição não podem compartilhar nenhum dia."""
    edicao_factory(
        data_inicio=date(2099, 1, 1),
        data_fim=date(2099, 1, 10),
        inscricoes_inicio=date(2098, 12, 1),
        inscricoes_fim=date(2099, 1, 10),
    )
    segunda = edicao_factory.build(
        data_inicio=date(2099, 1, 10),
        data_fim=date(2099, 1, 20),
        inscricoes_inicio=date(2099, 1, 11),
        inscricoes_fim=date(2099, 1, 20),
    )

    with pytest.raises(ValidationError) as contexto:
        segunda.save()

    assert MENSAGEM_PERIODO_DUPLICADO in _mensagens(contexto.value)


def test_rejeita_sobreposicao_do_periodo_de_inscricoes(edicao_factory) -> None:
    """Períodos de inscrição não podem compartilhar nenhum dia."""
    edicao_factory(
        data_inicio=date(2099, 1, 1),
        data_fim=date(2099, 1, 10),
        inscricoes_inicio=date(2098, 12, 1),
        inscricoes_fim=date(2099, 1, 5),
    )
    segunda = edicao_factory.build(
        data_inicio=date(2099, 2, 1),
        data_fim=date(2099, 2, 10),
        inscricoes_inicio=date(2099, 1, 5),
        inscricoes_fim=date(2099, 1, 15),
    )

    with pytest.raises(ValidationError) as contexto:
        segunda.save()

    assert MENSAGEM_PERIODO_DUPLICADO in _mensagens(contexto.value)


def test_permite_inscricao_com_inicio_antes_da_edicao(edicao_factory) -> None:
    """O início das inscrições pode anteceder o início da edição."""
    edicao = edicao_factory(
        inscricoes_inicio=date(2098, 12, 1),
        inscricoes_fim=date(2099, 1, 1),
    )

    assert edicao.inscricoes_inicio < edicao.data_inicio


def test_rejeita_mais_de_uma_edicao_ativa(edicao_factory) -> None:
    """Somente uma edição pode estar ativa simultaneamente."""
    with freeze_time("2099-01-15 12:00:00"):
        edicao_factory(
            nome="Primeira Edição",
            data_inicio=date(2099, 1, 1),
            data_fim=date(2099, 1, 31),
        )
        segunda = edicao_factory.build(
            nome="Segunda Edição",
            data_inicio=date(2099, 2, 1),
            data_fim=date(2099, 2, 28),
            inscricoes_inicio=date(2099, 1, 15),
            inscricoes_fim=date(2099, 2, 28),
            status=StatusEdicao.ATIVA,
        )

        with pytest.raises(ValidationError) as contexto:
            validar_unicidade_ativa(segunda)

    assert MENSAGEM_EDICAO_ATIVA_DUPLICADA in _mensagens(contexto.value)


def test_rejeita_alteracao_de_edicao_encerrada(edicao_factory) -> None:
    """Uma edição encerrada não pode ter seus dados alterados."""
    with freeze_time("2099-02-01 12:00:00"):
        edicao = edicao_factory(
            nome="Edição encerrada",
            data_inicio=date(2099, 1, 1),
            data_fim=date(2099, 1, 31),
        )
        edicao.nome = "Novo nome"

        with pytest.raises(ValidationError) as contexto:
            edicao.save()

    assert MENSAGEM_EDICAO_ENCERRADA in _mensagens(contexto.value)


def test_rejeita_inscricoes_com_fim_anterior_ao_inicio(
    edicao_factory,
) -> None:
    """As inscrições não podem terminar antes de começar."""
    edicao = edicao_factory.build(
        data_inicio=date(2099, 1, 1),
        data_fim=date(2099, 1, 31),
        inscricoes_inicio=date(2099, 1, 20),
        inscricoes_fim=date(2099, 1, 10),
    )

    with pytest.raises(ValidationError) as contexto:
        validar_periodos(edicao)

    assert (
        "A data final das inscrições deve ser posterior à inicial."
        in _mensagens(contexto.value)
    )


def test_permite_periodo_sem_todas_as_datas_informadas(
    edicao_factory,
) -> None:
    """A checagem de sobreposição é ignorada quando falta alguma data."""
    edicao = edicao_factory.build(
        data_inicio=date(2099, 1, 1),
        data_fim=date(2099, 1, 31),
        inscricoes_inicio=None,
        inscricoes_fim=date(2099, 1, 15),
    )

    assert validar_periodos(edicao) is None


def test_permite_revalidar_unicidade_da_propria_edicao_ativa(
    edicao_factory,
) -> None:
    """A edição ativa pode ser revalidada sem conflitar consigo mesma."""
    with freeze_time("2099-01-15 12:00:00"):
        edicao = edicao_factory(
            data_inicio=date(2099, 1, 1),
            data_fim=date(2099, 1, 31),
        )

        assert validar_unicidade_ativa(edicao) is None


def test_agrega_mensagem_de_erro_sem_dicionario(
    edicao_factory, monkeypatch
) -> None:
    """Erros sem estrutura de dicionário também são agregados por campo."""
    edicao = edicao_factory.build()
    mensagem = "Erro genérico sem campo."

    def _levanta_erro_simples(_edicao: object) -> None:
        raise ValidationError(mensagem)

    monkeypatch.setattr(
        validators, "validar_nome_unico", _levanta_erro_simples
    )

    with pytest.raises(ValidationError) as contexto:
        validar_edicao(edicao)

    assert mensagem in _mensagens(contexto.value)
