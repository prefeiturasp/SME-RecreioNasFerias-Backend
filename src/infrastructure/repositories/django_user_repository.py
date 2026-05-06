"""Implementação Django do repositório de usuários."""

from domain.entities.user import User
from domain.ports.user_repository import UserRepository
from usuarios.models import UserModel


class DjangoUserRepository(UserRepository):
    """Adaptador de persistência baseado em Django ORM."""

    def save(self, user: User) -> User:
        """Salva usuário e retorna a entidade persistida."""
        model, _created = UserModel.objects.update_or_create(
            id=user.id, defaults={"nome": user.nome, "email": user.email}
        )

        return User(id=str(model.id), nome=model.nome, email=model.email)

    def find_all(self) -> list[User]:
        """Lista todos os usuários convertidos para entidade de domínio."""
        models = UserModel.objects.all()
        return [
            User(id=str(model.id), nome=model.nome, email=model.email)
            for model in models
        ]

    def find_by_id(self, user_id: str) -> User | None:
        """Busca usuário por id e retorna entidade ou None."""
        model = UserModel.objects.filter(id=user_id).first()
        if not model:
            return None
        return User(id=str(model.id), nome=model.nome, email=model.email)

    def update(self, user: User) -> User | None:
        """Atualiza usuário existente e retorna versão atualizada."""
        updated_rows = UserModel.objects.filter(id=user.id).update(
            nome=user.nome, email=user.email
        )
        if not updated_rows:
            return None
        model = UserModel.objects.get(id=user.id)
        return User(id=str(model.id), nome=model.nome, email=model.email)

    def delete(self, user_id: str) -> bool:
        """Remove usuário por id e informa se houve deleção."""
        deleted_rows, _ = UserModel.objects.filter(id=user_id).delete()
        return deleted_rows > 0
