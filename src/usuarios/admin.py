"""Configuração de administração do app usuarios."""

from django.contrib import admin

from usuarios.models import LogLoginModel


@admin.register(LogLoginModel)
class LogLoginModelAdmin(admin.ModelAdmin):
    """Exibe logs de login somente leitura no admin."""

    list_display = (
        "id",
        "criado_em",
        "sucesso",
        "login_tentativa",
        "codigo_cargo",
        "descricao_cargo",
        "codigo_http",
        "endereco_ip",
    )
    list_filter = ("sucesso", "codigo_http")
    readonly_fields = (
        "id",
        "criado_em",
        "sucesso",
        "login_tentativa",
        "codigo_cargo",
        "descricao_cargo",
        "codigo_http",
        "mensagem",
        "endereco_ip",
        "user_agent",
    )

    def has_add_permission(self, request):
        """Impede criação manual de logs pelo admin."""
        return False

    def has_change_permission(self, request, obj=None):
        """Impede edição de logs."""
        return False
