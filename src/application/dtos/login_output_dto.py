"""
DTO de saída para resultado de autenticação bem-sucedida.

Serializa dados funcionais retornados pelo caso de uso de login para o
formato JSON da API, incluindo conversão de nomes de campos para camelCase
quando exigido pelo contrato HTTP.
"""


class LoginOutputDto:
    """Encapsula a resposta de autenticação retornada ao cliente após login.

    Não inclui o token Bearer; a view adiciona ``token`` após gerar o
    acesso assinado para o usuário Django sincronizado.

    Attributes:
        rf (str): Registro funcional do servidor autenticado.
        cpf (str | None): CPF quando informado pela integração SIGPAE.
        email (str | None): E-mail funcional quando disponível.
        cargos (list[dict]): Lista de cargos com metadados SIGPAE.
        nome (str): Nome completo do usuário.
        inexistente_eol (bool): Indica ausência do usuário no cadastro EOL.
    """

    def __init__(
        self,
        rf: str,
        cpf: str | None,
        email: str | None,
        cargos: list[dict],
        nome: str,
        inexistente_eol: bool,
    ):
        """Inicializa o DTO com dados funcionais vindos do CoreSSO/SIGPAE.

        Args:
            rf (str): Registro funcional do servidor autenticado.
            cpf (str | None): CPF quando informado pela integração.
            email (str | None): E-mail funcional quando disponível.
            cargos (list[dict]): Lista de cargos com códigos e descrições SIGPAE.
            nome (str): Nome completo do usuário.
            inexistente_eol (bool): Indica ausência do usuário no cadastro EOL.
        """
        self.rf = rf
        self.cpf = cpf
        self.email = email
        self.cargos = cargos
        self.nome = nome
        self.inexistente_eol = inexistente_eol

    def to_dict(self) -> dict:
        """Serializa o DTO para o formato JSON da API.

        Returns:
            dict: Dicionário com chaves em camelCase para compatibilidade com o
                contrato HTTP (ex.: ``inexistenteEol``).
        """
        return {
            "rf": self.rf,
            "cpf": self.cpf,
            "email": self.email,
            "cargos": self.cargos,
            "nome": self.nome,
            "inexistenteEol": self.inexistente_eol,
        }
