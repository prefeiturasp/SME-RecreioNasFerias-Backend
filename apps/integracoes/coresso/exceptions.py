"""Exceções específicas do CoreSSO."""

from __future__ import annotations


class CoressoError(Exception):
    """Classe base de erros da integração com o CoreSSO."""

    default_message = "Erro na integração com o CoreSSO."

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


class CoressoConfigError(CoressoError):
    """Indica configuração ausente ou inválida do CoreSSO."""

    default_message = "Configuração do CoreSSO incompleta."


class CoressoIndisponivelError(CoressoError):
    """Indica indisponibilidade do serviço CoreSSO."""

    default_message = "CoreSSO indisponível."


class CoressoAutenticacaoError(CoressoError):
    """Indica falha de autenticação no CoreSSO."""

    default_message = "Credenciais inválidas no CoreSSO."


class CoressoContratoError(CoressoError):
    """Indica resposta fora do contrato esperado do CoreSSO."""

    default_message = "Resposta do CoreSSO fora do contrato esperado."
