"""Contrato da integração com o CoreSSO.

Define a fronteira que o `core` consome para autenticação institucional sem
acoplamento direto à implementação HTTP.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class CoressoPort(ABC):
    """Define as operações esperadas para autenticação institucional."""

    @abstractmethod
    def autenticar(self, rf: str, senha: str) -> dict:
        """Autentica um usuário institucional.

        Args:
            rf: Registro funcional informado no login.
            senha: Senha institucional informada pelo usuário.

        Returns:
            Payload bruto retornado pela autenticação institucional.
        """

    @abstractmethod
    def obter_dados_usuario(self, token: str) -> dict:
        """Obtém os dados do usuário autenticado.

        Args:
            token: Token emitido após autenticação bem-sucedida.

        Returns:
            Dados do usuário autenticado necessários ao domínio local.
        """
