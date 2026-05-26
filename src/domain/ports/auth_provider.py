"""
Contrato para provedores de autenticação externos.

Abstração legada para integrações que retornam tokens de acesso; o fluxo
principal de login utiliza ``CoressoPort`` e tokens assinados locais.
"""

from abc import ABC, abstractmethod


class AuthProvider(ABC):
    """Define a operação de login em um provedor externo de identidade.

    Implementações concretas devem encapsular protocolo, URLs e tratamento
    de erros do provedor escolhido, retornando tokens utilizáveis pela API.
    """

    @abstractmethod
    def login(self, rf: str, senha: str) -> tuple[str, str | None]:
        """Autentica usuário por RF e senha no provedor configurado.

        Args:
            rf (str): Registro funcional do servidor.
            senha (str): Senha no provedor externo.

        Returns:
            tuple[str, str | None]: Par ``(access_token, refresh_token)``; o refresh
                pode ser ``None`` quando não aplicável.
        """
