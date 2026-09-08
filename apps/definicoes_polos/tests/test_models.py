"""Testes do modelo persistido de definições de polos."""

import pytest
from django.core.exceptions import ValidationError

from apps.definicoes_polos.constants import TipoPolo
from apps.definicoes_polos.models import DefinicaoPolo

pytestmark = pytest.mark.django_db


def test_modelo_define_choices_e_defaults(definicao_polo_factory) -> None:
    """A participação nasce pendente e herda campos comuns."""
    definicao = definicao_polo_factory()

    assert DefinicaoPolo._meta.get_field("tipo").choices == list(
        TipoPolo.choices
    )
    assert definicao.tipo == TipoPolo.PENDENTE
    assert definicao.ativo is True
    assert definicao.total_inscritos == 325


def test_modelo_calcula_total_arredondando_para_baixo(
    definicao_polo_factory,
) -> None:
    """O acréscimo de 30% descarta a parte decimal."""
    definicao = definicao_polo_factory(projecao_inscritos=175)

    assert definicao.total_inscritos == 227


def test_modelo_recalcula_total_mesmo_com_valor_informado(
    definicao_polo_factory,
) -> None:
    """O total enviado não prevalece sobre o cálculo do model."""
    definicao = definicao_polo_factory(projecao_inscritos=100)
    definicao.total_inscritos = 999
    definicao.save()

    assert definicao.total_inscritos == 130


def test_modelo_str_retorna_polo_e_edicao(definicao_polo_factory) -> None:
    """A representação textual identifica os dois lados da participação."""
    definicao = definicao_polo_factory()

    assert str(definicao) == f"{definicao.polo} - {definicao.edicao}"


def test_modelo_rejeita_projecao_negativa(definicao_polo_factory) -> None:
    """A projeção não pode ser negativa."""
    definicao = definicao_polo_factory.build(projecao_inscritos=-1)

    with pytest.raises(ValidationError):
        definicao.save()


def test_modelo_rejeita_participacao_duplicada(
    definicao_polo_factory,
) -> None:
    """O par polo e edição deve ser único."""
    primeira = definicao_polo_factory()
    segunda = DefinicaoPolo(
        polo=primeira.polo,
        edicao=primeira.edicao,
        projecao_inscritos=100,
    )

    with pytest.raises(ValidationError):
        segunda.save()
