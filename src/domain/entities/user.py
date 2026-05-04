import uuid


class User:
    def __init__(self, nome: str, email: str, id=None):
        self._validate(nome, email)

        self.id = id or str(uuid.uuid4())
        self.nome = nome
        self.email = email

    def _validate(self, nome: str, email: str):
        if not nome:
            raise ValueError("Nome é obrigatório")

        if not email:
            raise ValueError("Email é obrigatório")
