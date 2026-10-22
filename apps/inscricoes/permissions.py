"""Permissões DRF do domínio de inscrições."""

from apps.core.permissions import PermissaoPorAcao


class PermissaoInscricaoParticipante(PermissaoPorAcao):
    """Aplica a matriz RBAC às inscrições de participantes."""

    recurso = "inscricoes_participantes"
    acoes_por_view = {
        "cancelar": "change",
        "reativar": "change",
        "polos_elegiveis": "view",
        "polos_oficiais": "view",
        "participante_eol": "view",
        "participante_cpf": "view",
        "valores_choices": "view",
    }
