"""
Caso de uso para atualização de usuário na API legada de exemplo.

Mescla campos opcionais do DTO com estado atual antes de persistir alterações.
"""

from application.dtos.update_user_dto import UpdateUserDto
from application.dtos.user_output_dto import UserOutputDTO
from domain.entities.user import User
from domain.ports.user_repository import UserRepository


class UpdateUserUseCase:
    """Orquestra atualização parcial ou total de um usuário existente.

    Carrega o estado atual, mescla campos opcionais do DTO e persiste via
    repositório, garantindo que apenas usuários existentes sejam alterados.

    Attributes:
        user_repository (UserRepository): Adaptador de persistência de usuários.
    """

    def __init__(self, user_repository: UserRepository):
        """Injeta o adaptador de persistência de usuários.

        Args:
            user_repository (UserRepository): Porta de repositório do domínio.
        """
        self.user_repository = user_repository

    def execute(self, user_id: str, update_user_dto: UpdateUserDto) -> UserOutputDTO:
        """Mescla campos informados e persiste a entidade atualizada.

        Args:
            user_id (str): Identificador do usuário a alterar.
            update_user_dto (UpdateUserDto): Campos opcionais de atualização.

        Returns:
            UserOutputDTO: Estado final do usuário após persistência.

        Raises:
            ValueError: Se o usuário não existir antes ou depois da atualização.
        """
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
