"""Configuração do domínio no Django Admin."""

from django.contrib import admin

from apps.inscricoes.models import Inscricao


@admin.register(Inscricao)
class InscricaoAdmin(admin.ModelAdmin):
    """Apresenta e filtra inscrições."""

    list_display = (
        "nome_participante",
        "tipo_estudante",
        "grupo",
        "polo",
        "codigo_eol",
        "cpf",
        "status",
        "ativo",
    )
    list_filter = ("tipo_estudante", "grupo", "status", "ativo")
    search_fields = (
        "nome_participante",
        "codigo_eol",
        "cpf",
        "polo__nome_polo",
    )
    raw_id_fields = ("polo", "edicao")
    readonly_fields = ("uuid", "criado_em", "atualizado_em")
