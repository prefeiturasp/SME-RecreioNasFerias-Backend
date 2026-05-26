"""
Regras de RBAC aplicadas após autenticação no CoreSSO.

Normaliza listas de permissões recebidas do provedor de identidade antes
da persistência em ``Usuario.permissoes_rbac``.
"""


class UsuariosRbac:
    """Normaliza e deduplica permissões recebidas do provedor de identidade.

    Não implementa regras de autorização finas por endpoint; apenas garante
    que a lista armazenada localmente não contenha entradas vazias nem
    duplicatas, preservando a ordem de primeira ocorrência.
    """

    def aplicar(self, permissoes: list[str] | None) -> list[str]:
        """Remove entradas vazias e duplicatas preservando a ordem original.

        Args:
            permissoes (list[str] | None): Lista bruta de permissões do CoreSSO.

        Returns:
            list[str]: Permissões limpas prontas para persistência em
                ``permissoes_rbac``.
        """
        if not permissoes:
            return []

        permissoes_limpas = [p for p in permissoes if p]
        return list(dict.fromkeys(permissoes_limpas))
