"""Permissões DRF compartilhadas do app `core`."""

from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView


class PermissaoNaoImplementada(BasePermission):
    """Bloqueia acessos a recursos ainda não disponíveis na estrutura atual."""

    message = "Permissao deste recurso ainda nao esta disponivel."

    def has_permission(self, request: Request, view: APIView) -> bool:
        """Sempre bloqueia o acesso ao recurso protegido."""
        return False
