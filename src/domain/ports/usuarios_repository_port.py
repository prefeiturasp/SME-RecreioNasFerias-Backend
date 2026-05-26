"""
Contrato de persistência para contexto de autenticação de usuários Django.

Separa a sincronização da conta ``Usuario`` (AUTH_USER_MODEL) do fluxo de
login CoreSSO das operações do cadastro legado ``UserModel``.
"""

from abc import ABC, abstractmethod


class UsuariosRepositoryPort(ABC):
    """Define operações de persistência usadas no fluxo de login CoreSSO.

    Coordena criação/atualização de contexto, permissões RBAC e snapshot
    final de dados funcionais após autenticação bem-sucedida.

    Implementação de referência: ``UsuariosRepository``.
    """

    @abstractmethod
    def existe_por_rf(self, rf: str) -> bool:
        """Indica se já existe conta local vinculada ao RF.

        Args:
            rf (str): Registro funcional do servidor.

        Returns:
            bool: ``True`` se houver registro na tabela de usuários Django.
        """

    @abstractmethod
    def registrar_localmente(
        self, rf: str, contexto: str, permissoes: list[str]
    ) -> None:
        """Cria ou atualiza conta local na primeira autenticação bem-sucedida.

        Args:
            rf (str): Registro funcional.
            contexto (str): Contexto de acesso retornado pelo CoreSSO.
            permissoes (list[str]): Permissões RBAC normalizadas.
        """

    @abstractmethod
    def vincular_contexto_permissoes(
        self, rf: str, contexto: str, permissoes: list[str]
    ) -> None:
        """Atualiza contexto e permissões para RF já existente.

        Args:
            rf (str): Registro funcional.
            contexto (str): Novo contexto de acesso.
            permissoes (list[str]): Lista atualizada de permissões RBAC.
        """

    @abstractmethod
    def persistir_acesso(
        self,
        rf: str,
        contexto: str,
        permissoes: list[str],
        *,
        nome: str = "",
        email: str | None = None,
        cpf: str | None = None,
        inexistente_eol: bool = False,
    ) -> None:
        """Sincroniza snapshot final da conta Django após login no CoreSSO.

        Args:
            rf (str): Registro funcional.
            contexto (str): Contexto de acesso vigente.
            permissoes (list[str]): Permissões RBAC persistidas em JSON.
            nome (str): Nome completo retornado pela integração.
            email (str | None): E-mail funcional; pode ser substituído por padrão local.
            cpf (str | None): CPF quando informado.
            inexistente_eol (bool): Flag de ausência no cadastro EOL.
        """
