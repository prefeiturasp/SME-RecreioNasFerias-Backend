from domain.ports.user_repository import UserRepository


class DeleteUserUseCase:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def execute(self, user_id: str) -> None:
        deleted = self.user_repository.delete(user_id)
        if not deleted:
            raise ValueError("Usuário não encontrado")
