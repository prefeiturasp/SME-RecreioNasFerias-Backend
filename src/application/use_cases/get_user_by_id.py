"""
Caso de uso para busca de usuário por identificador na API legada.

Retorna DTO de saída ou sinaliza usuário inexistente com mensagem estável.
"""

from application.dtos.user_output_dto import UserOutputDTO
from domain.ports.user_repository import UserRepository


class GetUserByIdUseCase:
    """Orquestra a consulta de um único usuário por id.

    Traduz ausência no repositório em ``ValueError`` com mensagem estável
    consumida pela view para resposta HTTP 404.

    Attributes:
        user_repository (UserRepository): Adaptador de persistência de usuários.
    """

    def __init__(self, user_repository: UserRepository):
        """Injeta o adaptador de persistência de usuários.

        Args:
            user_repository (UserRepository): Porta de repositório do domínio.
        """
        self.user_repository = user_repository

    def execute(self, user_id: str) -> UserOutputDTO:
        """Busca usuário e converte para DTO de saída.

        Args:
            user_id (str): Identificador único do usuário.

        Returns:
            UserOutputDTO: Dados públicos do usuário encontrado.

        Raises:
            ValueError: Se o usuário não existir no repositório.
        """
        user = self.user_repository.find_by_id(user_id)
        if not user:
            raise ValueError("Usuário não encontrado")
        return UserOutputDTO(id=user.id, nome=user.nome, email=user.email)
