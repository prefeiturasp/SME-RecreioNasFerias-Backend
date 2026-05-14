"""Exceções de aplicação usadas nos casos de uso."""


class CargoNaoAutorizadoError(Exception):
    """Indica que o cargo retornado pela integração não está na lista permitida."""

    def __init__(self, message: str = "Cargo não autorizado para acesso ao sistema.") -> None:
        super().__init__(message)
