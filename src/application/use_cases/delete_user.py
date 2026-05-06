"""Caso de uso para remoção de usuário."""

from domain.ports.user_repository import UserRepository


class DeleteUserUseCase:
    """Orquestra a deleção de um usuário por id."""

    def __init__(self, user_repository: UserRepository):
        """Recebe a dependência de repositório de usuários."""
        self.user_repository = user_repository

    def execute(self, user_id: str) -> None:
        """Remove usuário existente ou lança erro de não encontrado."""
        deleted = self.user_repository.delete(user_id)
        if not deleted:
            raise ValueError("Usuário não encontrado")
