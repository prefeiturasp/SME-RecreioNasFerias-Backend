"""DTO para entrada de criação de usuário."""


class CreateUserDto:
    """Representa os dados obrigatórios para criar um usuário."""

    def __init__(self, nome: str, email: str):
        """Inicializa o DTO e valida os campos obrigatórios."""
        self._validate(nome, email)

        self.nome = nome
        self.email = email

    def _validate(self, nome: str, email: str):
        """Valida nome e email exigidos para criação."""
        if not nome:
            raise ValueError("Nome é obrigatório")

        if not email:
            raise ValueError("Email é obrigatório")
