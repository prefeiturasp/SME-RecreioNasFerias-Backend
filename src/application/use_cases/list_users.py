from domain.ports.user_repository import UserRepository
from application.dtos.user_output_dto import UserOutputDTO
from domain.entities.user import User


class ListUsersUseCase:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def execute(self) -> list[UserOutputDTO]:
        users = self.user_repository.find_all()
        return [
            UserOutputDTO(id=user.id, nome=user.nome, email=user.email)
            for user in users
        ]
