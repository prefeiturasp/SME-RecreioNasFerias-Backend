"""
Contrato de integração com o CoreSSO.

Define a operação de autenticação e o formato de payload esperado pelo caso
de uso de login após enriquecimento com dados SIGPAE.
"""

from abc import ABC, abstractmethod


class CoressoPort(ABC):
    """Define operações de autenticação e enriquecimento de dados no CoreSSO.

    A implementação de referência é ``UsuariosService``, que realiza chamadas
    HTTP com ``urllib`` e variáveis de ambiente ``AUTH_API_*``.
    """

    @abstractmethod
    def autenticar(self, login: str, senha: str) -> dict:
        """Autentica no CoreSSO e retorna payload padronizado de login.

        Args:
            login (str): RF com 7 dígitos.
            senha (str): Senha do usuário.

        Returns:
            dict: Dicionário com chaves como ``codigoRf``, ``nome``, ``cargos``,
                ``permissoes`` e demais campos usados pelo caso de uso.

        Raises:
            ValueError: Para credenciais inválidas ou usuário não autorizado.
            RuntimeError: Para falhas de integração ou resposta malformada.
        """
