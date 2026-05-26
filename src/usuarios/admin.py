"""
Configuração de administração do app usuarios.

Registra models de conta CoreSSO e logs de login com permissões restritas
para preservar integridade da trilha de auditoria.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from usuarios.models import LogLoginModel, Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    """Interface Django Admin para contas sincronizadas com CoreSSO.

    Exibe RF, dados funcionais e permissões RBAC. Campos sensíveis de data
    permanecem somente leitura para evitar inconsistência com o login externo.
    """

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
    """Exibe logs de login somente leitura no admin.

    Impede criação e edição manual para garantir que registros reflitam apenas
    eventos reais capturados pela API de autenticação.
    """

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
        """Impede criação manual de logs pelo admin.

        Args:
            request: Requisição HTTP do Django Admin.

        Returns:
            bool: Sempre ``False``; logs são criados apenas pela API.
        """
        return False

    def has_change_permission(self, request, obj=None):
        """Impede edição de registros de auditoria.

        Args:
            request: Requisição HTTP do Django Admin.
            obj: Instância de ``LogLoginModel`` ou ``None`` na listagem.

        Returns:
            bool: Sempre ``False``.
        """
        return False
