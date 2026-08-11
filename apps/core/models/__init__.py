"""Modelos do app `core`."""

from apps.core.models.identidade import CargoPermitido, LogLogin, Usuario
from apps.core.models.modelo_base import ModeloAtualizavel, ModeloBase

__all__ = [
    "CargoPermitido",
    "LogLogin",
    "ModeloAtualizavel",
    "ModeloBase",
    "Usuario",
]
