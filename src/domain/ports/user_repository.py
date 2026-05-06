"""Contrato de persistência para usuários no domínio."""

from abc import ABC, abstractmethod
from domain.entities.user import User


class UserRepository(ABC):
    """Define operações esperadas para armazenamento de usuários."""

    @abstractmethod
    def save(self, user: User) -> User:
        """Persiste um novo usuário ou sobrescreve por id."""

    @abstractmethod
    def find_all(self) -> list[User]:
        """Retorna todos os usuários cadastrados."""

    @abstractmethod
    def find_by_id(self, user_id: str) -> User | None:
        """Retorna um usuário por id ou None quando inexistente."""

    @abstractmethod
    def update(self, user: User) -> User | None:
        """Atualiza dados de um usuário existente."""

    @abstractmethod
    def delete(self, user_id: str) -> bool:
        """Remove usuário por id e retorna se houve remoção."""
