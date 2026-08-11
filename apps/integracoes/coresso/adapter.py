"""Adaptador placeholder da integração com o CoreSSO.

Implementa o contrato consumido pelo `core` e centraliza a futura delegação
para o client HTTP do provedor institucional.
"""

from apps.integracoes.coresso.client import CoressoClient
from apps.integracoes.coresso.port import CoressoPort


class CoressoAdapter(CoressoPort):
    """Mantem a superficie publica da integracao enquanto ela evolui."""

    def __init__(self, client: CoressoClient | None = None) -> None:
        """Inicializa o adaptador com o client HTTP futuro.

        Args:
            client: Client HTTP concreto a ser usado pelo adaptador. Quando
                omitido, utiliza a implementação padrão do projeto.
        """
        self.client = client or CoressoClient()

    def autenticar(self, rf: str, senha: str) -> dict:
        """Executa autenticacao institucional quando a integracao existir.

        Args:
            rf: Registro funcional enviado pelo usuário.
            senha: Senha institucional enviada pelo usuário.

        Returns:
            Payload bruto retornado pelo provedor institucional.

        Raises:
            NotImplementedError: Enquanto a integração real não existir.
        """
        raise NotImplementedError(
            "Integracao CoreSSO ainda nao esta disponivel."
        )

    def obter_dados_usuario(self, token: str) -> dict:
        """Obtem o perfil institucional quando a integracao existir.

        Args:
            token: Token emitido pela autenticação institucional.

        Returns:
            Dados do usuário autenticado retornados pelo provedor.

        Raises:
            NotImplementedError: Enquanto a integração real não existir.
        """
        raise NotImplementedError(
            "Integracao CoreSSO ainda nao esta disponivel."
        )
