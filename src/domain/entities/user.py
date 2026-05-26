"""
Entidade de domínio para usuário do cadastro legado de exemplo.

Representa o núcleo de negócio independente do ORM Django; o repositório
adapta entre esta entidade e ``UserModel``.
"""

import uuid


class User:
    """Representa usuário com identificador, nome e e-mail obrigatórios.

    Gera UUID na criação quando ``id`` não é informado. Valida invariantes
    mínimas antes de permitir persistência pelo caso de uso.

    Attributes:
        id: Identificador único (string UUID por padrão).
        nome (str): Nome do usuário.
        email (str): E-mail do usuário.
    """

    def __init__(self, nome: str, email: str, id=None):
        """Inicializa a entidade validando atributos obrigatórios.

        Args:
            nome (str): Nome do usuário.
            email (str): E-mail do usuário.
            id: Identificador existente; se omitido, gera UUID v4.

        Raises:
            ValueError: Se ``nome`` ou ``email`` estiverem vazios.
        """
        self._validate(nome, email)

        self.id = id or str(uuid.uuid4())
        self.nome = nome
        self.email = email

    def _validate(self, nome: str, email: str) -> None:
        """Garante presença de nome e e-mail na entidade.

        Args:
            nome (str): Nome a validar.
            email (str): E-mail a validar.

        Raises:
            ValueError: Se algum atributo obrigatório estiver ausente.
        """
        if not nome:
            raise ValueError("Nome é obrigatório")

        if not email:
            raise ValueError("Email é obrigatório")
