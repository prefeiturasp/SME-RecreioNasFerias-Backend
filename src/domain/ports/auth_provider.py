"""Contrato para provedores de autenticacao externos."""

from abc import ABC, abstractmethod


class AuthProvider(ABC):
    """Define a operacao de login em um provedor externo."""

    @abstractmethod
    def login(self, rf: str, senha: str) -> tuple[str, str | None]:
        """Autentica usuario por RF e senha; retorna access e refresh opcional."""
