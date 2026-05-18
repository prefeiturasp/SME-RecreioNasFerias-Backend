"""Implementação Django da verificação de cargos permitidos."""

from domain.ports.cargos_permitidos_port import CargosPermitidosPort
from usuarios.models import CargoPermitidoModel


class CargosPermitidosRepository(CargosPermitidosPort):
    """Consulta a tabela local de cargos permitidos."""

    def algum_codigo_autorizado(self, codigos_cargo: list[int]) -> bool:
        """Retorna True se ao menos um código SIGPAE está na lista permitida."""
        if not codigos_cargo:
            return False
        return CargoPermitidoModel.objects.filter(codigo_cargo__in=codigos_cargo).exists()
