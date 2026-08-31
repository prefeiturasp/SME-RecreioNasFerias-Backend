"""Choices e constantes do domínio de polos."""

from django.db import models


class TipoPolo(models.TextChoices):
    """Classificação do polo no programa."""

    PENDENTE = "pendente", "Pendente"
    OFICIAL = "oficial", "Polo oficial"
    RESERVA = "reserva", "Polo reserva"


class StatusPolo(models.TextChoices):
    """Estados possíveis de funcionamento de um polo."""

    ATIVO = "ativo", "Ativo"
    INATIVO = "inativo", "Inativo"


class GestaoPolo(models.TextChoices):
    """Tipos de gestão do polo."""

    PARCEIRA = "parceira", "Parceira"
    DIRETA = "direta", "Direta"
