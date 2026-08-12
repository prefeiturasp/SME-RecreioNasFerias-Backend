"""Client HTTP placeholder da SME Integração/EOL.

Encapsula as futuras chamadas de rede usadas para sincronização de unidades e
cargos no fluxo real da aplicacao.
"""


class EolClient:
    """Encapsula futuras chamadas HTTP da SME Integração."""

    def obter_unidades(self) -> list[dict]:
        """Executa a consulta de unidades quando a integracao existir.

        Returns:
            Lista bruta de unidades devolvida pela integração externa.

        Raises:
            NotImplementedError: Enquanto o HTTP real não existir.
        """
        raise NotImplementedError(
            "HTTP da integracao EOL ainda nao esta disponivel."
        )

    def obter_cargos(self) -> list[dict]:
        """Executa a consulta de cargos quando a integracao existir.

        Returns:
            Lista bruta de cargos devolvida pela integração externa.

        Raises:
            NotImplementedError: Enquanto o HTTP real não existir.
        """
        raise NotImplementedError(
            "HTTP da integracao EOL ainda nao esta disponivel."
        )
