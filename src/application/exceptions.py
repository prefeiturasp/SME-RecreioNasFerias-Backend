"""
Exceções de aplicação usadas nos casos de uso e na camada HTTP.

Centraliza erros de negócio que devem ser traduzidos em respostas HTTP
específicas (por exemplo, 403 para cargo não autorizado), sem vazar
detalhes de integração externa ao cliente.
"""

# Mensagens estáveis expostas ao frontend (HTTP 502 / 500).
ERRO_CORESSO_INDISPONIVEL = "O CoreSSO está indisponível no momento."

ERRO_INTERNO_API = "Ocorreu um erro interno na aplicação. Tente novamente mais tarde."

# Fallbacks quando o CoreSSO não envia corpo de erro legível.
MENSAGEM_PADRAO_CREDENCIAIS_INCORRETAS = "Usuário ou senha incorretos."

MENSAGEM_PADRAO_RF_SEM_DADOS = (
    "Sem informações na base de dados para o Código Rf informado"
)


class CoressoIndisponivelError(RuntimeError):
    """Indica que o CoreSSO está inacessível ou não respondeu.

    Levantada em timeout, falha de rede, HTTP 5xx ou resposta malformada.
    A view de login responde com HTTP 502 e ``ERRO_CORESSO_INDISPONIVEL``.
    """

    def __init__(self, mensagem: str | None = None) -> None:
        """Inicializa com mensagem fixa de indisponibilidade.

        Args:
            mensagem (str | None): Texto exibido ao cliente; usa
                ``ERRO_CORESSO_INDISPONIVEL`` quando ``None``.
        """
        super().__init__(mensagem or ERRO_CORESSO_INDISPONIVEL)


class CoressoRespostaError(ValueError):
    """Erro de negócio retornado pelo CoreSSO com mensagem do serviço externo.

    Usada para credenciais inválidas (401) e ausência de dados no SIGPAE (404),
    preservando o texto retornado pela API de integração.
    """

    def __init__(self, mensagem: str, status_http: int) -> None:
        """Associa mensagem do CoreSSO ao status HTTP repassado ao frontend.

        Args:
            mensagem (str): Texto retornado pelo serviço (ou fallback local).
            status_http (int): Código HTTP a propagar na resposta da API.
        """
        super().__init__(mensagem)
        self.status_http = status_http


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
