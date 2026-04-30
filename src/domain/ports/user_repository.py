from abc import ABC, abstractmethod
from domain.entities.user import User


class UserRepository(ABC):

    @abstractmethod
    def save(self, user: User) -> User:
        pass

    @abstractmethod
    def find_all(self) -> list[User]:
        pass
