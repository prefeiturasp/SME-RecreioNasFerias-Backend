"""DTO de saida para resultado de autenticacao."""


class LoginOutputDto:
    """Encapsula resposta de autenticacao de usuario."""

    def __init__(
        self,
        rf: str,
        cpf: str | None,
        email: str | None,
        cargos: list[dict],
        nome: str,
        inexistente_eol: bool,
    ):
        """Inicializa DTO de resposta de autenticacao."""
        self.rf = rf
        self.cpf = cpf
        self.email = email
        self.cargos = cargos
        self.nome = nome
        self.inexistente_eol = inexistente_eol

    def to_dict(self):
        """Converte DTO para formato serializavel."""
        return {
            "rf": self.rf,
            "cpf": self.cpf,
            "email": self.email,
            "cargos": self.cargos,
            "nome": self.nome,
            "inexistenteEol": self.inexistente_eol,
        }
