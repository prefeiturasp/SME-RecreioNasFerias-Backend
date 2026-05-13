"""Regras de RBAC para autenticação de usuários."""


class UsuariosRbac:
    """Aplica regras de autorização sobre permissões recebidas."""

    def aplicar(self, permissoes: list[str] | None) -> list[str]:
        """Normaliza permissões removendo vazios e duplicados."""
        if not permissoes:
            return []

        permissoes_limpas = [p for p in permissoes if p]
        return list(dict.fromkeys(permissoes_limpas))
