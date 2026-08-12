"""Exceções específicas do CoreSSO."""


class CoressoError(Exception):
    """Classe base de erros da integração com o CoreSSO."""


class CoressoIndisponivelError(CoressoError):
    """Indica indisponibilidade do serviço CoreSSO."""


class CoressoAutenticacaoError(CoressoError):
    """Indica falha de autenticação no CoreSSO."""
