"""Repositório local de conta Django sincronizada no fluxo de login (CoreSSO)."""

from django.contrib.auth import get_user_model

from domain.ports.usuarios_repository_port import UsuariosRepositoryPort

Usuario = get_user_model()


class UsuariosRepository(UsuariosRepositoryPort):
    """Persiste contexto e permissões no model de usuário Django."""

    def existe_por_rf(self, rf: str) -> bool:
        """Retorna se há conta local para o RF."""
        return Usuario.objects.filter(rf=rf).exists()

    def registrar_localmente(self, rf: str, contexto: str, permissoes: list[str]) -> None:
        """Cria conta local inicial para usuário autenticado no CoreSSO."""
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
        """Atualiza contexto e permissões RBAC para RF já registrado."""
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
        """Sincroniza snapshot final da conta Django após login no CoreSSO."""
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
        """Gera e-mail local quando o CoreSSO não informa um."""
        return f"{rf}@recreionasferias.local"

    @staticmethod
    def _garantir_senha_nao_utilizavel(usuario: Usuario) -> None:
        """Marca senha Django como inutilizável (credencial validada no CoreSSO)."""
        usuario.set_unusable_password()
        usuario.save(update_fields=["password"])
