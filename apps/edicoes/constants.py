"""Constantes do domínio de edições.

Define os status possíveis no ciclo de vida de uma edição.
"""

from django.db import models


class StatusEdicao(models.TextChoices):
    """Estados possíveis do ciclo de vida de uma edição."""

    PLANEJADA = "planejada", "Planejada"
    ATIVA = "ativa", "Ativa"
    ENCERRADA = "encerrada", "Encerrada"
