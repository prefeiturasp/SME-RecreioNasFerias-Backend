"""Exceções específicas da SME Integração/EOL."""

from __future__ import annotations


class EolError(Exception):
    """Classe base de erros da integração com a SME Integração/EOL."""

    default_message = "Erro na integração com a SME Integração/EOL."

    def __init__(
        self,
        message: str | None = None,
        *,
        status_code: int | None = None,
    ) -> None:
        """Inicializa a exceção com mensagem opcional e status HTTP."""
        mensagem = message or self.default_message
        super().__init__(mensagem)
        self.status_code = status_code


class EolConfigError(EolError):
    """Indica configuração ausente ou inválida da integração EOL."""

    default_message = "Configuração da integração EOL incompleta."


class EolIndisponivelError(EolError):
    """Indica indisponibilidade do serviço SME Integração/EOL."""

    default_message = "Serviço SME Integração/EOL indisponível."


class EolContratoError(EolError):
    """Indica resposta fora do contrato esperado da SME Integração/EOL."""

    default_message = (
        "Resposta da SME Integração/EOL fora do contrato esperado."
    )


class ServidorNaoEncontradoError(EolError):
    """Indica que o registro funcional não existe na base da SME."""

    default_message = (
        "Não foi possível encontrar o servidor com o RF informado."
    )


class ConsultaServidorIndisponivelError(EolError):
    """Indica que a consulta do servidor não pôde ser realizada."""

    default_message = "A consulta não pôde ser realizada. Tente novamente."
