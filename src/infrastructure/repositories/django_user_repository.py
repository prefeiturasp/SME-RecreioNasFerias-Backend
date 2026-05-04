from domain.entities.user import User
from domain.ports.user_repository import UserRepository
from usuarios.models import UserModel


class DjangoUserRepository(UserRepository):

    def save(self, user: User) -> User:
        model, _created = UserModel.objects.update_or_create(
            id=user.id, defaults={"nome": user.nome, "email": user.email}
        )

        return User(id=str(model.id), nome=model.nome, email=model.email)

    def find_all(self) -> list[User]:
        models = UserModel.objects.all()
        return [
            User(id=str(model.id), nome=model.nome, email=model.email)
            for model in models
        ]

    def find_by_id(self, user_id: str) -> User | None:
        model = UserModel.objects.filter(id=user_id).first()
        if not model:
            return None
        return User(id=str(model.id), nome=model.nome, email=model.email)

    def update(self, user: User) -> User | None:
        updated_rows = UserModel.objects.filter(id=user.id).update(
            nome=user.nome, email=user.email
        )
        if not updated_rows:
            return None
        model = UserModel.objects.get(id=user.id)
        return User(id=str(model.id), nome=model.nome, email=model.email)

    def delete(self, user_id: str) -> bool:
        deleted_rows, _ = UserModel.objects.filter(id=user_id).delete()
        return deleted_rows > 0
