"""Caso de uso para listagem de usuários."""

from domain.ports.user_repository import UserRepository
from application.dtos.user_output_dto import UserOutputDTO
from domain.entities.user import User


class ListUsersUseCase:
    """Orquestra a consulta de usuários cadastrados."""

    def __init__(self, user_repository: UserRepository):
        """Recebe a dependência de repositório de usuários."""
        self.user_repository = user_repository

    def execute(self) -> list[UserOutputDTO]:
        """Retorna todos os usuários convertidos para DTO de saída."""
        users = self.user_repository.find_all()
        return [
            UserOutputDTO(id=user.id, nome=user.nome, email=user.email)
            for user in users
        ]
