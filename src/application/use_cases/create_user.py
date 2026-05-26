"""
Caso de uso para criação de usuário na API legada de exemplo.

Converte ``CreateUserDto`` em entidade de domínio, persiste via repositório
e retorna ``UserOutputDTO`` para serialização JSON na view.
"""

from domain.ports.user_repository import UserRepository
from application.dtos.create_user_dto import CreateUserDto
from application.dtos.user_output_dto import UserOutputDTO
from domain.entities.user import User


class CreateUserUseCase:
    """Orquestra a criação e persistência de um usuário no repositório.

    Instancia a entidade de domínio ``User``, delega ``save`` ao repositório
    injetado e devolve um DTO de saída sem expor detalhes de ORM.

    Attributes:
        user_repository (UserRepository): Adaptador de persistência configurado
            na camada de infraestrutura (ex.: ``DjangoUserRepository``).
    """

    def __init__(self, user_repository: UserRepository):
        """Injeta o adaptador de persistência de usuários.

        Args:
            user_repository (UserRepository): Porta de repositório do domínio.
        """
        self.user_repository = user_repository

    def execute(self, create_user_dto: CreateUserDto) -> UserOutputDTO:
        """Cria entidade de domínio, persiste e retorna DTO de saída.

        Args:
            create_user_dto (CreateUserDto): Dados validados de entrada.

        Returns:
            UserOutputDTO: Representação pública do usuário recém-criado.
        """
        user = User(create_user_dto.nome, create_user_dto.email)
        saved_user: User = self.user_repository.save(user)

        return UserOutputDTO(
            id=saved_user.id, nome=saved_user.nome, email=saved_user.email
        )
