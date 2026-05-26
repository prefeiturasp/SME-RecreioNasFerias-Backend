"""
Contrato para verificação de cargos permitidos no login.

Permite ao caso de uso de login consultar a política de autorização por
código SIGPAE sem depender diretamente do ORM Django.
"""

from abc import ABC, abstractmethod


class CargosPermitidosPort(ABC):
    """Consulta se algum dos códigos de cargo informados está autorizado.

    A lista permitida é mantida localmente (tabela ``usuarios_cargos_permitidos``)
    e administrada via Django Admin ou migrações de dados.
    """

    @abstractmethod
    def algum_codigo_autorizado(self, codigos_cargo: list[int]) -> bool:
        """Verifica interseção entre códigos SIGPAE e a lista local permitida.

        Args:
            codigos_cargo (list[int]): Códigos extraídos da resposta de autenticação.

        Returns:
            bool: ``True`` se pelo menos um código existir na base de cargos
                permitidos.
        """
