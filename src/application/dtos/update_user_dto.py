"""
DTO para entrada de atualização parcial de usuário.

Permite alterar nome e/ou e-mail de registros na API legada
``PUT /api/usuarios/<id>/``, exigindo ao menos um campo informado.
"""


class UpdateUserDto:
    """Representa dados opcionais para atualização de um usuário existente.

    Campos omitidos (``None``) são interpretados pelo caso de uso como
    "manter valor atual". Strings vazias são rejeitadas quando o campo
    é explicitamente enviado.

    Attributes:
        nome (str | None): Novo nome ou ``None`` para não alterar.
        email (str | None): Novo e-mail ou ``None`` para não alterar.
    """

    def __init__(self, nome: str | None = None, email: str | None = None):
        """Constrói o DTO exigindo ao menos um campo para alteração.

        Args:
            nome (str | None): Novo nome; ``None`` mantém o valor atual.
            email (str | None): Novo e-mail; ``None`` mantém o valor atual.

        Raises:
            ValueError: Se nenhum campo for informado ou se nome/e-mail forem
                strings vazias quando presentes.
        """
        self._validate(nome, email)
        self.nome = nome
        self.email = email

    def _validate(self, nome: str | None, email: str | None) -> None:
        """Valida regras de atualização parcial.

        Args:
            nome (str | None): Nome opcional a atualizar.
            email (str | None): E-mail opcional a atualizar.

        Raises:
            ValueError: Se ambos forem ``None`` ou se algum campo informado for
                string vazia.
        """
        if nome is None and email is None:
            raise ValueError("Informe ao menos um campo para atualização")

        if nome is not None and not nome:
            raise ValueError("Nome é obrigatório")

        if email is not None and not email:
            raise ValueError("Email é obrigatório")
