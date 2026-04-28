from domain.ports.user_repository import UserRepository
from application.dtos.create_user_dto import CreateUserDto
from application.dtos.user_output_dto import UserOutputDTO
from domain.entities.user import User


class CreateUserUseCase:

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def execute(self, create_user_dto: CreateUserDto) -> UserOutputDTO:

        user = User(create_user_dto.nome, create_user_dto.email)
        saved_user: User = self.user_repository.save(user)

        return UserOutputDTO(
            id=saved_user.id, nome=saved_user.nome, email=saved_user.email
        )
