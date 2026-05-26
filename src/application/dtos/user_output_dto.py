"""
DTO de saída para dados públicos de usuário retornados pelos casos de uso.

Padroniza a resposta JSON dos endpoints de CRUD legado de usuários de
exemplo (listagem, busca, criação e atualização).
"""


class UserOutputDTO:
    """Encapsula identificador, nome e e-mail expostos na API de usuários.

    Evita expor detalhes internos da entidade de domínio ou do model ORM
    diretamente nas views HTTP.

    Attributes:
        id: Identificador único (UUID em string).
        nome (str): Nome do usuário.
        email (str): E-mail do usuário.
    """

    def __init__(self, id, nome: str, email: str):
        """Inicializa o objeto de saída com os atributos do usuário.

        Args:
            id: Identificador único do usuário (UUID ou string).
            nome (str): Nome do usuário.
            email (str): E-mail do usuário.
        """
        self.id, self.nome, self.email = id, nome, email

    def to_dict(self) -> dict:
        """Converte o DTO para dicionário serializável em JSON.

        Returns:
            dict: Mapeamento com chaves ``id``, ``nome`` e ``email``.
        """
        return {"id": self.id, "nome": self.nome, "email": self.email}
