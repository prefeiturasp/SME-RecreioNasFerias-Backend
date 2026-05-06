"""Caso de uso para atualização de usuário."""

from application.dtos.update_user_dto import UpdateUserDto
from application.dtos.user_output_dto import UserOutputDTO
from domain.entities.user import User
from domain.ports.user_repository import UserRepository


class UpdateUserUseCase:
    """Orquestra atualização total ou parcial de um usuário."""

    def __init__(self, user_repository: UserRepository):
        """Recebe a dependência de repositório de usuários."""
        self.user_repository = user_repository

    def execute(self, user_id: str, update_user_dto: UpdateUserDto) -> UserOutputDTO:
        """Atualiza usuário e retorna o resultado em DTO de saída."""
        existing_user = self.user_repository.find_by_id(user_id)
        if not existing_user:
            raise ValueError("Usuário não encontrado")

        user = User(
            id=user_id,
            nome=update_user_dto.nome
            if update_user_dto.nome is not None
            else existing_user.nome,
            email=update_user_dto.email
            if update_user_dto.email is not None
            else existing_user.email,
        )
        updated_user = self.user_repository.update(user)
        if not updated_user:
            raise ValueError("Usuário não encontrado")
        return UserOutputDTO(
            id=updated_user.id,
            nome=updated_user.nome,
            email=updated_user.email,
        )
