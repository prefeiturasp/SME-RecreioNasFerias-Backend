"""Configuração do modelo de polos no Django Admin."""

from django.contrib import admin
from apps.polos.models import Polo, ControleSincronizacaoPolos


@admin.register(Polo)
class PoloAdmin(admin.ModelAdmin):
    """Apresenta e filtra polos no painel administrativo."""

    list_display = (
        "codigo_eol",
        "nome_polo",
        "dre_nome",
        "tipo",
        "status",
        "gestao",
        "quantidade_maxima_alunos",
    )
    list_filter = ("tipo", "status", "gestao", "ativo")
    search_fields = ("codigo_eol", "nome_polo", "nome_osc", "dre_nome")
    readonly_fields = ("uuid", "criado_em", "atualizado_em")
    
    
@admin.register(ControleSincronizacaoPolos)
class ControleSincronizacaoPolosAdmin(admin.ModelAdmin):
    list_display = ("chave", "ultima_execucao_em")
    readonly_fields = ("chave", "ultima_execucao_em")
