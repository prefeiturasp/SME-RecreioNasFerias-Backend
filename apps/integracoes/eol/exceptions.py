"""Exceções específicas da SME Integração/EOL."""


class EolError(Exception):
    """Classe base de erros da integração com a SME Integração."""


class EolIndisponivelError(EolError):
    """Indica indisponibilidade do serviço SME Integração."""


class EolRespostaInvalidaError(EolError):
    """Indica retorno inesperado da SME Integração."""
