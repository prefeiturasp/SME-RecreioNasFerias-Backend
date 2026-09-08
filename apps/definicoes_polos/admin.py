"""Configuração do domínio no Django Admin."""

from django.contrib import admin

from apps.definicoes_polos.models import DefinicaoPolo


@admin.register(DefinicaoPolo)
class DefinicaoPoloAdmin(admin.ModelAdmin):
    """Apresenta e filtra participações no Admin."""

    list_display = (
        "polo",
        "edicao",
        "tipo",
        "projecao_inscritos",
        "total_inscritos",
        "ponto_focal_nome",
    )
    list_filter = ("tipo", "edicao", "ativo")
    search_fields = (
        "polo__nome_polo",
        "polo__codigo_eol",
        "edicao__nome",
        "ponto_focal_nome",
    )
    raw_id_fields = ("polo", "edicao")
    readonly_fields = ("uuid", "total_inscritos", "criado_em", "atualizado_em")
