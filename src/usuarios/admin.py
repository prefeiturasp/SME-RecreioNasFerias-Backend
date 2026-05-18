"""Configuração de administração do app usuarios."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from usuarios.models import LogLoginModel, Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    """Administra contas sincronizadas com CoreSSO."""

    ordering = ("rf",)
    list_display = ("rf", "nome_completo", "email", "contexto", "is_active", "is_staff")
    list_filter = ("is_active", "is_staff", "contexto")
    search_fields = ("rf", "nome_completo", "email", "cpf")
    readonly_fields = ("atualizado_em", "last_login", "date_joined")
    fieldsets = (
        (None, {"fields": ("rf", "password", "is_active", "is_staff", "is_superuser")}),
        ("Dados CoreSSO", {"fields": ("nome_completo", "email", "cpf", "inexistente_eol")}),
        ("Acesso na aplicação", {"fields": ("contexto", "permissoes_rbac")}),
        ("Datas", {"fields": ("last_login", "date_joined", "atualizado_em")}),
        ("Permissões Django", {"fields": ("groups", "user_permissions")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("rf", "email", "nome_completo"),
            },
        ),
    )
    filter_horizontal = ("groups", "user_permissions")


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
