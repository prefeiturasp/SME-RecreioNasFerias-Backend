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

    default_message = "SME Integração/EOL indisponível."


class EolContratoError(EolError):
    """Indica resposta fora do contrato esperado da SME Integração/EOL."""

    default_message = (
        "Resposta da SME Integração/EOL fora do contrato esperado."
    )
