"""Caso de uso para busca de usuário por identificador."""

from application.dtos.user_output_dto import UserOutputDTO
from domain.ports.user_repository import UserRepository


class GetUserByIdUseCase:
    """Orquestra a busca de um usuário único."""

    def __init__(self, user_repository: UserRepository):
        """Recebe a dependência de repositório de usuários."""
        self.user_repository = user_repository

    def execute(self, user_id: str) -> UserOutputDTO:
        """Busca usuário por id e retorna DTO ou erro de não encontrado."""
        user = self.user_repository.find_by_id(user_id)
        if not user:
            raise ValueError("Usuário não encontrado")
        return UserOutputDTO(id=user.id, nome=user.nome, email=user.email)
