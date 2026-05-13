"""Contrato de persistência para contexto de autenticação de usuários."""

from abc import ABC, abstractmethod


class UsuariosRepositoryPort(ABC):
    """Define operações de persistência usadas no fluxo de login."""

    @abstractmethod
    def existe_por_rf(self, rf: str) -> bool:
        """Indica se já existe registro local para o RF."""

    @abstractmethod
    def registrar_localmente(self, rf: str, contexto: str, permissoes: list[str]) -> None:
        """Registra usuário localmente conforme política da aplicação."""

    @abstractmethod
    def vincular_contexto_permissoes(
        self, rf: str, contexto: str, permissoes: list[str]
    ) -> None:
        """Vincula contexto e permissões para usuário já existente."""

    @abstractmethod
    def persistir_acesso(self, rf: str, contexto: str, permissoes: list[str]) -> None:
        """Persiste snapshot final de acesso calculado no login."""
