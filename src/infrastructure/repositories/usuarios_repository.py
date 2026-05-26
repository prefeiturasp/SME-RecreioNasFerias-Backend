"""
Repositório local de conta Django sincronizada no fluxo de login (CoreSSO).

Implementa ``UsuariosRepositoryPort`` sobre ``AUTH_USER_MODEL``, garantindo
senha inutilizável no Django após cada sincronização bem-sucedida.
"""

from django.contrib.auth import get_user_model

from domain.ports.usuarios_repository_port import UsuariosRepositoryPort

Usuario = get_user_model()


class UsuariosRepository(UsuariosRepositoryPort):
    """Persiste contexto e permissões no model ``Usuario`` (AUTH_USER_MODEL).

    Usa ``get_or_create`` e ``update_or_create`` para idempotência em logins
    repetidos. E-mails ausentes recebem domínio local ``@recreionasferias.local``.
    """

    def existe_por_rf(self, rf: str) -> bool:
        """Verifica existência de conta pelo RF.

        Args:
            rf (str): Registro funcional.

        Returns:
            bool: ``True`` se ``Usuario.objects.filter(rf=rf)`` retornar linha.
        """
        return Usuario.objects.filter(rf=rf).exists()

    def registrar_localmente(
        self, rf: str, contexto: str, permissoes: list[str]
    ) -> None:
        """Cria conta local ou atualiza contexto em reautenticação inicial.

        Args:
            rf (str): Registro funcional.
            contexto (str): Contexto de acesso CoreSSO.
            permissoes (list[str]): Permissões RBAC normalizadas.
        """
        usuario, criado = Usuario.objects.get_or_create(
            rf=rf,
            defaults={
                "email": self._email_padrao(rf),
                "contexto": contexto,
                "permissoes_rbac": permissoes,
                "is_active": True,
            },
        )
        if not criado:
            usuario.contexto = contexto
            usuario.permissoes_rbac = permissoes
            usuario.save(update_fields=["contexto", "permissoes_rbac"])
        self._garantir_senha_nao_utilizavel(usuario)

    def vincular_contexto_permissoes(
        self, rf: str, contexto: str, permissoes: list[str]
    ) -> None:
        """Atualiza contexto e permissões para RF já registrado.

        Args:
            rf (str): Registro funcional.
            contexto (str): Novo contexto.
            permissoes (list[str]): Lista atualizada de permissões.
        """
        Usuario.objects.filter(rf=rf).update(
            contexto=contexto,
            permissoes_rbac=permissoes,
        )

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
        """Sincroniza snapshot final da conta após login bem-sucedido.

        Args:
            rf (str): Registro funcional.
            contexto (str): Contexto vigente.
            permissoes (list[str]): Permissões RBAC.
            nome (str): Nome completo (truncado em 255 caracteres).
            email (str | None): E-mail funcional ou padrão local.
            cpf (str | None): CPF (truncado em 11 caracteres).
            inexistente_eol (bool): Flag EOL ausente.
        """
        usuario, _criado = Usuario.objects.update_or_create(
            rf=rf,
            defaults={
                "email": (email or "").strip() or self._email_padrao(rf),
                "nome_completo": (nome or "")[:255],
                "cpf": (cpf or "")[:11],
                "contexto": contexto,
                "permissoes_rbac": permissoes,
                "inexistente_eol": inexistente_eol,
                "is_active": True,
            },
        )
        self._garantir_senha_nao_utilizavel(usuario)

    @staticmethod
    def _email_padrao(rf: str) -> str:
        """Gera e-mail local quando o CoreSSO não informa endereço.

        Args:
            rf (str): Registro funcional.

        Returns:
            str: E-mail no domínio ``@recreionasferias.local``.
        """
        return f"{rf}@recreionasferias.local"

    @staticmethod
    def _garantir_senha_nao_utilizavel(usuario: Usuario) -> None:
        """Marca senha Django como inutilizável (credencial validada no CoreSSO).

        Args:
            usuario (Usuario): Instância do model de usuário Django.
        """
        usuario.set_unusable_password()
        usuario.save(update_fields=["password"])
