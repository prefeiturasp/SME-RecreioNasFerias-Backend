"""DTO de saída para dados públicos de usuário."""


class UserOutputDTO:
    """Encapsula os dados retornados pelos casos de uso de usuário."""

    def __init__(self, id, nome, email: str):
        """Inicializa o objeto de saída de usuário."""
        self.id, self.nome, self.email = id, nome, email

    def to_dict(self):
        """Converte o DTO para dicionário serializável."""
        return {"id": self.id, "nome": self.nome, "email": self.email}
