"""Testes do modelo de inscrições."""

import pytest
from django.core.exceptions import ValidationError

from apps.inscricoes.constants import (
    GrupoInscricao,
    StatusInscricao,
    TipoEstudante,
)
from apps.inscricoes.models import Inscricao

pytestmark = pytest.mark.django_db


def test_modelo_define_choices_defaults_e_metadados(inscricao_factory) -> None:
    """O modelo expõe choices, defaults e campos comuns esperados."""
    inscricao = inscricao_factory()

    assert Inscricao._meta.get_field("grupo").choices == list(
        GrupoInscricao.choices
    )
    assert Inscricao._meta.get_field("status").choices == list(
        StatusInscricao.choices
    )
    assert inscricao.status == StatusInscricao.RASCUNHO
    assert inscricao.ativo is True
    assert inscricao.tipo_logradouro == "Rua"
    assert inscricao.uuid is not None
    assert inscricao.criado_em is not None
    assert inscricao.atualizado_em is not None


def test_modelo_str_usa_nome_ou_uuid(inscricao_factory) -> None:
    """A representação textual usa o nome e tem fallback para o UUID."""
    inscricao = inscricao_factory(nome_participante="Nome Teste")
    sem_nome = inscricao_factory(nome_participante="")

    assert str(inscricao) == "Nome Teste"
    assert str(sem_nome) == str(sem_nome.uuid)


def test_modelo_calcula_status_completo(inscricao_completa_factory) -> None:
    """Dados básicos completos resultam em status COMPLETA."""
    inscricao = inscricao_completa_factory()

    assert inscricao.pode_ser_completa is True
    assert inscricao.status == StatusInscricao.COMPLETA


def test_modelo_reverte_status_ao_limpar_campo_obrigatorio(
    inscricao_completa_factory,
) -> None:
    """A remoção de campo obrigatório reverte para RASCUNHO."""
    inscricao = inscricao_completa_factory()
    inscricao.tipo_logradouro = ""
    inscricao.save()

    assert inscricao.status == StatusInscricao.RASCUNHO


def test_modelo_preserva_cancelamento_manual(
    inscricao_completa_factory,
) -> None:
    """Uma inscrição cancelada não é reclassificada em um save comum."""
    inscricao = inscricao_completa_factory()
    inscricao.status = StatusInscricao.CANCELADA
    inscricao.save()

    assert inscricao.status == StatusInscricao.CANCELADA


def test_modelo_rejeita_grupo_incompativel(inscricao_completa_factory) -> None:
    """Grupos infantis não podem pertencer a estudante externo."""
    with pytest.raises(ValidationError):
        inscricao_completa_factory(
            grupo=GrupoInscricao.BERCARIO_I,
            tipo_estudante=TipoEstudante.ESTUDANTE_EXTERNO,
        )
