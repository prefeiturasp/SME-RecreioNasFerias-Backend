"""Repositório local de contexto/permissões no fluxo de login."""

from domain.ports.usuarios_repository_port import UsuariosRepositoryPort
from usuarios.models import UsuarioAcessoModel


class UsuariosRepository(UsuariosRepositoryPort):
    """Implementação Django para persistência do acesso de usuários."""

    def existe_por_rf(self, rf: str) -> bool:
        """Retorna se há registro local de acesso para o RF."""
        return UsuarioAcessoModel.objects.filter(rf=rf).exists()

    def registrar_localmente(self, rf: str, contexto: str, permissoes: list[str]) -> None:
        """Cria registro local inicial para usuário autenticado."""
        UsuarioAcessoModel.objects.create(
            rf=rf,
            contexto=contexto,
            permissoes=permissoes,
        )

    def vincular_contexto_permissoes(
        self, rf: str, contexto: str, permissoes: list[str]
    ) -> None:
        """Atualiza contexto e permissões para RF já registrado."""
        UsuarioAcessoModel.objects.filter(rf=rf).update(
            contexto=contexto,
            permissoes=permissoes,
        )

    def persistir_acesso(self, rf: str, contexto: str, permissoes: list[str]) -> None:
        """Persiste snapshot final de acesso após aplicação de RBAC."""
        UsuarioAcessoModel.objects.update_or_create(
            rf=rf,
            defaults={"contexto": contexto, "permissoes": permissoes},
        )
