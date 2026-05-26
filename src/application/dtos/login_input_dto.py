"""
DTO de entrada para autenticação de usuário via CoreSSO.

Encapsula e normaliza credenciais recebidas no corpo JSON do endpoint
``POST /api/auth/login/``, aplicando as mesmas regras de RF de 7 dígitos
usadas pelo validador de aplicação.
"""


class LoginInputDto:
    """Representa credenciais necessárias para login (RF de 7 dígitos e senha).

    O login é armazenado já normalizado (sem espaços) após validação. A senha
    não é alterada neste DTO; a verificação de valor ocorre apenas quanto à
    presença.

    Attributes:
        login (str): RF com exatamente 7 dígitos numéricos.
        senha (str): Senha informada pelo cliente para o CoreSSO.
    """

    def __init__(self, login: str, senha: str):
        """Constrói o DTO normalizando o login e validando a senha.

        Args:
            login (str): Registro funcional com exatamente 7 dígitos numéricos.
            senha (str): Senha do usuário no provedor externo (CoreSSO).

        Raises:
            ValueError: Se o login estiver ausente, não tiver 7 dígitos ou a senha
                estiver vazia.
        """
        login_normalizado, senha_valida = self._validate(login, senha)
        self.login = login_normalizado
        self.senha = senha_valida

    def _validate(self, login: str, senha: str) -> tuple[str, str]:
        """Aplica regras de validação do fluxo de autenticação.

        Args:
            login (str): Valor bruto do campo login recebido na requisição.
            senha (str): Valor bruto do campo senha recebido na requisição.

        Returns:
            tuple[str, str]: Par ``(login_normalizado, senha)`` após validação.

        Raises:
            ValueError: Se o login estiver ausente, não tiver 7 dígitos ou a senha
                estiver vazia.
        """
        if login is None or not str(login).strip():
            raise ValueError("Login é obrigatório")
        login_limpo = str(login).strip()
        if len(login_limpo) != 7 or not login_limpo.isdigit():
            raise ValueError("Login deve conter exatamente 7 dígitos")
        if not senha:
            raise ValueError("Senha é obrigatória")
        return login_limpo, senha
