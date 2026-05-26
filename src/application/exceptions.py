"""
Exceções de aplicação usadas nos casos de uso e na camada HTTP.

Centraliza erros de negócio que devem ser traduzidos em respostas HTTP
específicas (por exemplo, 403 para cargo não autorizado), sem vazar
detalhes de integração externa ao cliente.
"""


class CargoNaoAutorizadoError(Exception):
    """Indica que o cargo retornado pela integração não está autorizado.

    Levantada quando nenhum código de cargo do CoreSSO consta na lista local
    de cargos permitidos ou quando a integração não retorna cargos válidos
    para autorização no sistema Recreio nas Férias.

    A view de login captura esta exceção e responde com HTTP 403 e mensagem
    amigável definida no construtor.
    """

    def __init__(
        self, message: str = "Cargo não autorizado para acesso ao sistema."
    ) -> None:
        """Inicializa a exceção com mensagem exibida ao cliente (HTTP 403).

        Args:
            message (str): Texto descritivo do motivo da recusa de acesso.
                Deve ser seguro para exibição ao usuário final (sem stack trace
                ou dados internos).
        """
        super().__init__(message)
