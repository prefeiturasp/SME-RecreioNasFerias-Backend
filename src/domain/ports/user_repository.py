from abc import ABC, abstractmethod
from domain.entities.user import User


class UserRepository(ABC):

    @abstractmethod
    def save(self, user: User) -> User:
        pass

    @abstractmethod
    def find_all(self) -> list[User]:
        pass

    @abstractmethod
    def find_by_id(self, user_id: str) -> User | None:
        pass

    @abstractmethod
    def update(self, user: User) -> User | None:
        pass

    @abstractmethod
    def delete(self, user_id: str) -> bool:
        pass
