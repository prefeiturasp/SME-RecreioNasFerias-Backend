"""
Implementação Django da verificação de cargos permitidos.

Consulta ``CargoPermitidoModel`` para autorizar login com base nos códigos
SIGPAE retornados pelo CoreSSO.
"""

from domain.ports.cargos_permitidos_port import CargosPermitidosPort
from usuarios.models import CargoPermitidoModel


class CargosPermitidosRepository(CargosPermitidosPort):
    """Consulta a tabela local ``usuarios_cargos_permitidos`` via ORM.

    Utiliza ``exists()`` com filtro ``codigo_cargo__in`` para evitar carregar
    todos os registros em memória.
    """

    def algum_codigo_autorizado(self, codigos_cargo: list[int]) -> bool:
        """Verifica se ao menos um código SIGPAE está cadastrado como permitido.

        Args:
            codigos_cargo (list[int]): Códigos extraídos do payload de login.

        Returns:
            bool: ``True`` quando existe interseção com ``CargoPermitidoModel``.
        """
        if not codigos_cargo:
            return False
        return CargoPermitidoModel.objects.filter(
            codigo_cargo__in=codigos_cargo
        ).exists()
