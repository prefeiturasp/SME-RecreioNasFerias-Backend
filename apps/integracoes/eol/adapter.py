"""Adaptador placeholder da integração com a SME Integração/EOL.

Mantém o contrato usado pelos domínios enquanto a integração real ainda não
foi ligada ao client HTTP.
"""

from apps.integracoes.eol.client import EolClient
from apps.integracoes.eol.port import EolPort


class EolAdapter(EolPort):
    """Mantem a superficie publica da integracao enquanto ela evolui."""

    def __init__(self, client: EolClient | None = None) -> None:
        """Inicializa o adaptador com o client HTTP futuro.

        Args:
            client: Client HTTP concreto a ser usado pelo adaptador. Quando
                omitido, utiliza a implementação padrão do projeto.
        """
        self.client = client or EolClient()

    def obter_unidades(self) -> list[dict]:
        """Executa a sincronizacao de unidades quando a integracao existir.

        Returns:
            Lista de unidades retornadas pela integração externa.

        Raises:
            NotImplementedError: Enquanto a integração real não existir.
        """
        raise NotImplementedError("Integracao EOL ainda nao esta disponivel.")

    def obter_cargos(self) -> list[dict]:
        """Executa a sincronizacao de cargos quando a integracao existir.

        Returns:
            Lista de cargos retornados pela integração externa.

        Raises:
            NotImplementedError: Enquanto a integração real não existir.
        """
        raise NotImplementedError("Integracao EOL ainda nao esta disponivel.")
