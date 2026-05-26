"""
Caso de uso para listagem de todos os usuários na API legada.

Não aplica filtros; adequado ao volume de demonstração do cadastro de exemplo.
"""

from domain.ports.user_repository import UserRepository
from application.dtos.user_output_dto import UserOutputDTO
from domain.entities.user import User


class ListUsersUseCase:
    """Orquestra a consulta de todos os usuários cadastrados.

    Não aplica paginação nem filtros; retorna a coleção completa convertida
    para DTOs, adequado ao volume esperado do cadastro de exemplo.

    Attributes:
        user_repository (UserRepository): Adaptador de persistência de usuários.
    """

    def __init__(self, user_repository: UserRepository):
        """Injeta o adaptador de persistência de usuários.

        Args:
            user_repository (UserRepository): Porta de repositório do domínio.
        """
        self.user_repository = user_repository

    def execute(self) -> list[UserOutputDTO]:
        """Lista usuários convertendo cada entidade para DTO.

        Returns:
            list[UserOutputDTO]: Coleção de usuários expostos na API; pode ser
                lista vazia quando não houver registros.
        """
        users = self.user_repository.find_all()
        return [
            UserOutputDTO(id=user.id, nome=user.nome, email=user.email)
            for user in users
        ]
