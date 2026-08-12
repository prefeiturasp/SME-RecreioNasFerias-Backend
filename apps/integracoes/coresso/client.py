"""Client HTTP placeholder do CoreSSO.

Encapsula as futuras chamadas de rede necessárias para login institucional e
consulta de perfil do usuário autenticado.
"""


class CoressoClient:
    """Encapsula futuras chamadas HTTP do CoreSSO."""

    def autenticar(self, rf: str, senha: str) -> dict:
        """Executa a chamada de autenticacao institucional quando existir.

        Args:
            rf: Registro funcional enviado pelo usuário.
            senha: Senha institucional enviada pelo usuário.

        Returns:
            Resposta bruta da autenticação institucional.

        Raises:
            NotImplementedError: Enquanto o HTTP real não existir.
        """
        raise NotImplementedError("HTTP do CoreSSO ainda nao esta disponivel.")

    def obter_dados_usuario(self, token: str) -> dict:
        """Executa a consulta de dados do usuario quando existir.

        Args:
            token: Token emitido após autenticação bem-sucedida.

        Returns:
            Dados do usuário retornados pelo provedor institucional.

        Raises:
            NotImplementedError: Enquanto o HTTP real não existir.
        """
        raise NotImplementedError("HTTP do CoreSSO ainda nao esta disponivel.")
