"""
Implementação Django do repositório de usuários de exemplo.

Adapta a entidade de domínio ``User`` para o model ORM ``UserModel`` usado
pelos endpoints legados ``/api/usuarios/``.
"""

from domain.entities.user import User
from domain.ports.user_repository import UserRepository
from usuarios.models import UserModel


class DjangoUserRepository(UserRepository):
    """Adaptador de persistência de ``User`` baseado em ``UserModel`` (ORM).

    Converte id UUID entre string (domínio) e tipo nativo do banco. Operações
    de atualização usam ``QuerySet.update`` seguido de leitura para retornar
    estado consistente.
    """

    def save(self, user: User) -> User:
        """Cria ou atualiza registro por identificador.

        Args:
            user (User): Entidade de domínio com ``id``, ``nome`` e ``email``.

        Returns:
            User: Entidade reconstruída a partir do model persistido.
        """
        model, _created = UserModel.objects.update_or_create(
            id=user.id, defaults={"nome": user.nome, "email": user.email}
        )

        return User(id=str(model.id), nome=model.nome, email=model.email)

    def find_all(self) -> list[User]:
        """Lista todos os usuários da tabela legada ``usuarios``.

        Returns:
            list[User]: Entidades de domínio para cada linha encontrada.
        """
        models = UserModel.objects.all()
        return [
            User(id=str(model.id), nome=model.nome, email=model.email)
            for model in models
        ]

    def find_by_id(self, user_id: str) -> User | None:
        """Busca usuário pelo UUID.

        Args:
            user_id (str): Identificador primário em string.

        Returns:
            User | None: Entidade ou ``None`` se inexistente.
        """
        model = UserModel.objects.filter(id=user_id).first()
        if not model:
            return None
        return User(id=str(model.id), nome=model.nome, email=model.email)

    def update(self, user: User) -> User | None:
        """Atualiza nome e e-mail de registro existente.

        Args:
            user (User): Entidade com ``id`` definido.

        Returns:
            User | None: Entidade atualizada ou ``None`` se o id não existir.
        """
        updated_rows = UserModel.objects.filter(id=user.id).update(
            nome=user.nome, email=user.email
        )
        if not updated_rows:
            return None
        model = UserModel.objects.get(id=user.id)
        return User(id=str(model.id), nome=model.nome, email=model.email)

    def delete(self, user_id: str) -> bool:
        """Remove usuário pelo identificador.

        Args:
            user_id (str): UUID do registro.

        Returns:
            bool: ``True`` se ao menos uma linha foi excluída.
        """
        deleted_rows, _ = UserModel.objects.filter(id=user_id).delete()
        return deleted_rows > 0
