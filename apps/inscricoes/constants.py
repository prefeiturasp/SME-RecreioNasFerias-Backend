"""Choices do domínio de inscrições."""

from django.db import models


class GrupoInscricao(models.TextChoices):
    """Grupos de atendimento disponíveis para a inscrição."""

    BERCARIO_I = "BERCARIO_I", "Berçário I"
    BERCARIO_II = "BERCARIO_II", "Berçário II"
    MINI_GRUPO_I = "MINI_GRUPO_I", "Mini Grupo I"
    MINI_GRUPO_II = "MINI_GRUPO_II", "Mini Grupo II"
    QUATRO_A_14_ANOS = "QUATRO_A_14_ANOS", "4 a 14 anos"


class TipoEstudante(models.TextChoices):
    """Origem escolar do participante."""

    ESTUDANTE_DA_REDE = "ESTUDANTE_DA_REDE", "Estudante da rede"
    ESTUDANTE_EXTERNO = "ESTUDANTE_EXTERNO", "Estudante externo"


class StatusInscricao(models.TextChoices):
    """Estados do ciclo de vida da inscrição."""

    RASCUNHO = "RASCUNHO", "Rascunho"
    COMPLETA = "COMPLETA", "Completa"
    CANCELADA = "CANCELADA", "Cancelada"
