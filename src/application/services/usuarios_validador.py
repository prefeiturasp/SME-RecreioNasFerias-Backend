"""Validações de entrada do fluxo de autenticação de usuários."""


class UsuariosValidador:
    """Centraliza validações da requisição de login."""

    def validar_login(self, login: str, senha: str) -> None:
        """Valida login e senha com regras mínimas da história."""
        if login is None or not str(login).strip():
            raise ValueError("Login é obrigatório")

        login_limpo = str(login).strip()
        if len(login_limpo) != 7 or not login_limpo.isdigit():
            raise ValueError("Login deve conter exatamente 7 dígitos")

        if not senha:
            raise ValueError("Senha é obrigatória")
