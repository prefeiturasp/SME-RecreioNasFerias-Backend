class UserOutputDTO:
    def __init__(self, id, nome, email: str):
        self.id, self.nome, self.email = id, nome, email

    def to_dict(self):
        return {"id": self.id, "nome": self.nome, "email": self.email}
