"""Permissões DRF do domínio de edições."""

from apps.core.permissions import PermissaoPorAcao


class PermissaoEdicao(PermissaoPorAcao):
    """Aplica a matriz RBAC às ações de edições."""

    recurso = "edicoes"
