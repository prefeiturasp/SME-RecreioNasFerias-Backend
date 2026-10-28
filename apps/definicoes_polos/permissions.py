"""Permissões DRF do domínio de definições de polos."""

from apps.core.permissions import PermissaoPorAcao


class PermissaoDefinicaoPolo(PermissaoPorAcao):
    """Aplica a matriz RBAC às ações das definições de polos."""

    recurso = "definicoes_polos"
    acoes_por_view = {
        "historico": "view",
        "vincular_em_massa": "add",
        "alterar_tipo_em_massa": "change",
        "alterar_edicao_em_massa": "change",
    }
