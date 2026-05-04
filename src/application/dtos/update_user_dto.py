class UpdateUserDto:
    def __init__(self, nome: str | None = None, email: str | None = None):
        self._validate(nome, email)
        self.nome = nome
        self.email = email

    def _validate(self, nome: str | None, email: str | None):
        if nome is None and email is None:
            raise ValueError("Informe ao menos um campo para atualização")

        if nome is not None and not nome:
            raise ValueError("Nome é obrigatório")

        if email is not None and not email:
            raise ValueError("Email é obrigatório")
