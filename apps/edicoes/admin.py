"""Configuração do modelo de edições no Django Admin."""

from django.contrib import admin

from apps.edicoes.models import Edicao
from apps.edicoes.services.edicao_service import EdicaoService


@admin.register(Edicao)
class EdicaoAdmin(admin.ModelAdmin):
    """Apresenta e filtra edições no painel administrativo."""

    list_display = (
        "nome",
        "data_inicio",
        "data_fim",
        "inscricoes_inicio",
        "inscricoes_fim",
        "status",
    )
    list_filter = ("status",)
    search_fields = ("nome",)
    readonly_fields = (
        "uuid",
        "status",
        "quantidade_inscritos",
        "quantidade_atendimento_efetivo",
        "quantidade_passeios",
        "quantidade_apresentacoes",
        "criado_em",
        "atualizado_em",
    )

    def get_queryset(self, request):
        """Atualiza os status antes de exibir a lista no Admin."""
        EdicaoService.sincronizar_status()
        return super().get_queryset(request)
