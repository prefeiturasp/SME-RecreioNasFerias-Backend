"""Permissões DRF compartilhadas do app `core`."""

from collections.abc import Mapping

from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from apps.core.permission_catalog import ACOES_POR_METODO, RECURSOS


class PermissaoPorAcao(BasePermission):
    """Autoriza ações usando permissões Django de usuário ou de grupo."""

    recurso: str | None = None
    acoes_por_view: Mapping[str, str] = {}
    message = "Você não tem permissão para executar esta ação."

    def has_permission(self, request: Request, view: APIView) -> bool:
        """Valida a permissão correspondente ao método/ação DRF."""
        user = request.user
        if (
            not user
            or not user.is_authenticated
            or self.recurso not in RECURSOS
        ):
            return False

        acao = self.acoes_por_view.get(getattr(view, "action", ""))
        if acao is None:
            acao = ACOES_POR_METODO.get(request.method or "")
        codename = RECURSOS[self.recurso].permissoes.get(acao or "")
        return bool(codename and user.has_perm(f"core.{codename}"))


class PermissaoConsultaPerfis(BasePermission):
    """Permite consultar papéis a quem pode visualizar usuários."""

    message = "Você não tem permissão para consultar os perfis disponíveis."

    def has_permission(self, request: Request, view: APIView) -> bool:
        """Exige autenticação e permissão de consulta de usuários."""
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.has_perm("core.visualizar_usuarios")
        )


class PermissaoNaoImplementada(BasePermission):
    """Bloqueia explicitamente recursos sem uma regra de autorização."""

    message = "A permissão para este recurso ainda não foi implementada."

    def has_permission(self, request: Request, view: APIView) -> bool:
        """Falha de forma segura até que o domínio declare sua regra."""
        return False
