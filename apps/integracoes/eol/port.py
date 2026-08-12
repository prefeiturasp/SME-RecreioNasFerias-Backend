"""Contrato da integração com a SME Integração/EOL.

Define a fronteira consumida pelos domínios que precisam sincronizar dados
externos sem depender do client HTTP concreto.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class EolPort(ABC):
    """Define as operações esperadas para sincronização de dados externos."""

    @abstractmethod
    def obter_unidades(self) -> list[dict]:
        """Obtém as unidades elegíveis no EOL.

        Returns:
            Lista de unidades no formato bruto esperado pelo domínio local.
        """

    @abstractmethod
    def obter_cargos(self) -> list[dict]:
        """Obtém os cargos relevantes para o sistema.

        Returns:
            Lista de cargos retornados pela integração externa.
        """
