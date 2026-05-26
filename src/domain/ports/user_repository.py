"""
Contrato de persistência para usuários no domínio (cadastro legado).

Descreve operações CRUD sobre a entidade ``User`` sem expor detalhes do
Django ORM ao restante da aplicação.
"""

from abc import ABC, abstractmethod
from domain.entities.user import User


class UserRepository(ABC):
    """Define operações esperadas para armazenamento de usuários de exemplo.

    Implementado por ``DjangoUserRepository``, que mapeia para ``UserModel``.
    Casos de uso de CRUD legado dependem exclusivamente desta porta.
    """

    @abstractmethod
    def save(self, user: User) -> User:
        """Persiste um novo usuário ou atualiza por identificador.

        Args:
            user (User): Entidade de domínio a gravar.

        Returns:
            User: Entidade persistida com identificador definitivo.
        """

    @abstractmethod
    def find_all(self) -> list[User]:
        """Lista todos os usuários cadastrados.

        Returns:
            list[User]: Coleção de entidades de domínio.
        """

    @abstractmethod
    def find_by_id(self, user_id: str) -> User | None:
        """Busca usuário pelo identificador.

        Args:
            user_id (str): UUID ou chave primária em string.

        Returns:
            User | None: Entidade encontrada ou ``None``.
        """

    @abstractmethod
    def update(self, user: User) -> User | None:
        """Atualiza nome e e-mail de um usuário existente.

        Args:
            user (User): Entidade com ``id`` e campos atualizados.

        Returns:
            User | None: Entidade atualizada ou ``None`` se inexistente.
        """

    @abstractmethod
    def delete(self, user_id: str) -> bool:
        """Remove usuário pelo identificador.

        Args:
            user_id (str): Identificador do registro.

        Returns:
            bool: ``True`` se ao menos um registro foi removido.
        """
