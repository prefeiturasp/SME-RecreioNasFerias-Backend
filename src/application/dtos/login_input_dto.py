"""DTO de entrada para autenticacao de usuario."""


class LoginInputDto:
    """Representa credenciais necessarias para login (login e senha)."""

    def __init__(self, login: str, senha: str):
        """Inicializa DTO e valida login (7 digitos) e senha."""
        login_normalizado, senha_valida = self._validate(login, senha)
        self.login = login_normalizado
        self.senha = senha_valida

    def _validate(self, login: str, senha: str) -> tuple[str, str]:
        """Valida login com exatamente 7 digitos e presenca da senha."""
        if login is None or not str(login).strip():
            raise ValueError("Login é obrigatório")
        login_limpo = str(login).strip()
        if len(login_limpo) != 7 or not login_limpo.isdigit():
            raise ValueError("Login deve conter exatamente 7 dígitos")
        if not senha:
            raise ValueError("Senha é obrigatória")
        return login_limpo, senha
