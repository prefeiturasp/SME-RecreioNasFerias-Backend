"""
Validações de entrada do fluxo de autenticação de usuários.

Concentra regras síncronas aplicadas antes de qualquer chamada HTTP ao
CoreSSO, permitindo respostas 400 rápidas para payloads malformados.
"""


class UsuariosValidador:
    """Centraliza validações da requisição de login antes da integração externa.

    As mensagens de ``ValueError`` são estáveis e reutilizadas pela view
    para mapear status HTTP (400 para validação, 401 para credenciais
    quando propagadas pelo serviço externo).
    """

    def validar_login(self, login: str, senha: str) -> None:
        """Valida login (7 dígitos) e presença da senha.

        Args:
            login (str): Registro funcional informado pelo cliente.
            senha (str): Senha informada pelo cliente.

        Raises:
            ValueError: Se o login estiver ausente, não tiver exatamente 7 dígitos
                numéricos ou a senha estiver vazia.
        """
        if login is None or not str(login).strip():
            raise ValueError("Login é obrigatório")

        login_limpo = str(login).strip()
        if len(login_limpo) != 7 or not login_limpo.isdigit():
            raise ValueError("Login deve conter exatamente 7 dígitos")

        if not senha:
            raise ValueError("Senha é obrigatória")
