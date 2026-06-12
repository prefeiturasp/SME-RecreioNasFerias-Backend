"""
Configuração de administração do app edições.

Registra o modelo de edições no Django Admin com campos de consolidação
somente leitura para preservar o controle de cadastro.
"""

from django.contrib import admin

from edicoes.models import Edicao


@admin.register(Edicao)
class EdicaoAdmin(admin.ModelAdmin):
    """Interface Django Admin para cadastro e consulta de edições.

    Permite gerenciar nome e períodos obrigatórios, mantendo travados os
    campos de quantidade que são preenchidos por processos internos.
    """

    list_display = (
        "nome",
        "periodo_edicao_inicio",
        "periodo_edicao_fim",
        "periodo_inscricoes_inicio",
        "periodo_inscricoes_fim",
        "quantidade_inscritos",
    )
    search_fields = ("nome",)
    readonly_fields = (
        "quantidade_inscritos",
        "quantidade_atendimento_efetivo",
        "quantidade_passeios",
        "quantidade_apresentacoes",
        "criado_em",
        "atualizado_em",
    )
