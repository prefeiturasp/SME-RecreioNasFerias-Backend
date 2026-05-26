"""
DTO de entrada para criação de usuário na API legada de exemplo.

Valida presença de nome e e-mail antes que o caso de uso instancie a
entidade de domínio e persista via repositório.
"""


class CreateUserDto:
    """Representa os dados obrigatórios para criar um usuário na API.

    Utilizado pelo endpoint ``POST /api/usuarios/``. Os campos são validados
    na construção para falhar cedo com ``ValueError`` antes de qualquer
    acesso ao banco de dados.

    Attributes:
        nome (str): Nome do usuário após validação.
        email (str): E-mail único do usuário após validação.
    """

    def __init__(self, nome: str, email: str):
        """Constrói o DTO validando nome e e-mail.

        Args:
            nome (str): Nome completo ou de exibição do usuário.
            email (str): Endereço de e-mail único do usuário.

        Raises:
            ValueError: Se ``nome`` ou ``email`` estiverem vazios.
        """
        self._validate(nome, email)

        self.nome = nome
        self.email = email

    def _validate(self, nome: str, email: str) -> None:
        """Valida campos obrigatórios antes de atribuir ao DTO.

        Args:
            nome (str): Nome informado na requisição.
            email (str): E-mail informado na requisição.

        Raises:
            ValueError: Se ``nome`` ou ``email`` estiverem vazios.
        """
        if not nome:
            raise ValueError("Nome é obrigatório")

        if not email:
            raise ValueError("Email é obrigatório")
