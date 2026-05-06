"""Entidade de domínio para usuário."""

import uuid


class User:
    """Representa usuário com regras mínimas de validade."""

    def __init__(self, nome: str, email: str, id=None):
        """Inicializa entidade com id, nome e email válidos."""
        self._validate(nome, email)

        self.id = id or str(uuid.uuid4())
        self.nome = nome
        self.email = email

    def _validate(self, nome: str, email: str):
        """Valida presença dos atributos obrigatórios da entidade."""
        if not nome:
            raise ValueError("Nome é obrigatório")

        if not email:
            raise ValueError("Email é obrigatório")
