"""Permissões DRF do domínio de polos."""

from apps.core.permissions import PermissaoPorAcao


class PermissaoPolo(PermissaoPorAcao):
    """Aplica a matriz RBAC às ações de polos."""

    recurso = "polos"
    acoes_por_view = {"dres": "consultar_dres"}
