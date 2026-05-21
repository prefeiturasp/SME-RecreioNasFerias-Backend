"""Contrato para verificação de cargos permitidos no login."""

from abc import ABC, abstractmethod


class CargosPermitidosPort(ABC):
    """Consulta se algum dos códigos de cargo informados está autorizado."""

    @abstractmethod
    def algum_codigo_autorizado(self, codigos_cargo: list[int]) -> bool:
        """Retorna True se pelo menos um código existir na base de cargos permitidos."""
