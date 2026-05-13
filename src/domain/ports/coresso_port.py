"""Contrato de integração com o CoreSSO."""

from abc import ABC, abstractmethod


class CoressoPort(ABC):
    """Define operações de autenticação no CoreSSO."""

    @abstractmethod
    def autenticar(self, login: str, senha: str) -> dict:
        """Autentica no CoreSSO e retorna payload de login."""
