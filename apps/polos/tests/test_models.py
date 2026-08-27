"""Testes do modelo persistido de polos."""

import pytest
from django.core.exceptions import ValidationError

from apps.polos.constants import GestaoPolo, StatusPolo, TipoPolo
from apps.polos.models import Polo

pytestmark = pytest.mark.django_db


def test_modelo_define_choices_e_defaults(polo_factory) -> None:
    """O modelo utiliza choices e defaults oficiais do domínio."""
    polo = polo_factory()

    assert Polo._meta.get_field("tipo").choices == list(TipoPolo.choices)
    assert Polo._meta.get_field("status").choices == list(StatusPolo.choices)
    assert Polo._meta.get_field("gestao").choices == list(GestaoPolo.choices)
    assert polo.tipo == TipoPolo.PENDENTE
    assert polo.status == StatusPolo.ATIVO
    assert polo.gestao == GestaoPolo.PARCEIRA


def test_modelo_permite_complemento_ausente(polo_factory) -> None:
    """Complemento é opcional e inicia vazio quando não informado."""
    polo = polo_factory()

    assert polo.complemento == ""
    assert Polo._meta.get_field("complemento").blank is True


def test_modelo_forca_defaults_na_criacao(polo_factory) -> None:
    """Novos polos sempre nascem pendentes e ativos."""
    polo = polo_factory.build(tipo=TipoPolo.OFICIAL, status=StatusPolo.INATIVO)
    polo.save()

    assert polo.tipo == TipoPolo.PENDENTE
    assert polo.status == StatusPolo.ATIVO


def test_modelo_preserva_tipo_e_status_na_atualizacao(polo_factory) -> None:
    """Tipo e status podem ser alterados depois da criação."""
    polo = polo_factory()
    polo.tipo = TipoPolo.OFICIAL
    polo.status = StatusPolo.INATIVO
    polo.save()
    polo.refresh_from_db()

    assert polo.tipo == TipoPolo.OFICIAL
    assert polo.status == StatusPolo.INATIVO


def test_modelo_tem_uuid_e_timestamps(polo_factory) -> None:
    """A entidade herda os campos comuns do modelo base."""
    polo = polo_factory()

    assert polo.uuid is not None
    assert polo.criado_em is not None
    assert polo.atualizado_em is not None
    assert polo.ativo is True


def test_modelo_str_retorna_nome_do_polo(polo_factory) -> None:
    """A representação textual utiliza o nome do polo."""
    polo = polo_factory(nome_polo="Polo representado")

    assert str(polo) == "Polo representado"


def test_modelo_rejeita_quantidade_maxima_negativa(polo_factory) -> None:
    """A capacidade máxima não pode ser negativa."""
    polo = polo_factory.build(quantidade_maxima_alunos=-1)

    with pytest.raises(ValidationError):
        polo.save()
