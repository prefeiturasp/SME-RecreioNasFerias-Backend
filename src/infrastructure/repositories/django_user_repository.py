from domain.entities.user import User
from domain.ports.user_repository import UserRepository
from usuarios.models import UserModel


class DjangoUserRepository(UserRepository):

    def save(self, user: User) -> User:
        model, _created = UserModel.objects.update_or_create(
            id=user.id, defaults={"nome": user.nome, "email": user.email}
        )

        return User(id=str(model.id), nome=model.nome, email=model.email)
