"""
Caso de uso para remoção de usuário na API legada de exemplo.

Remove registro por UUID e propaga ausência como ``ValueError`` para a view
mapear HTTP 404.
"""

from domain.ports.user_repository import UserRepository


class DeleteUserUseCase:
    """Orquestra a exclusão de um usuário pelo identificador.

    Opera de forma idempotente do ponto de vista do domínio: se o id não
    existir, sinaliza erro explícito para a view retornar 404.

    Attributes:
        user_repository (UserRepository): Adaptador de persistência de usuários.
    """

    def __init__(self, user_repository: UserRepository):
        """Injeta o adaptador de persistência de usuários.

        Args:
            user_repository (UserRepository): Porta de repositório do domínio.
        """
        self.user_repository = user_repository

    def execute(self, user_id: str) -> None:
        """Remove usuário existente ou sinaliza ausência.

        Args:
            user_id (str): Identificador único do usuário.

        Raises:
            ValueError: Se nenhum registro for removido (usuário inexistente).
        """
        deleted = self.user_repository.delete(user_id)
        if not deleted:
            raise ValueError("Usuário não encontrado")
