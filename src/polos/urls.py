"""
Mapeamento de rotas HTTP do app de polos.

Expõe endpoints de cadastro, listagem, consulta, atualização, exclusão,
opções de filtro e sincronização de unidades diretas sob ``/api/``.
"""

from django.urls import path

from polos.views import (
    atualizar_polos_em_lote,
    listar_opcoes_filtro_polos,
    listar_unidades_diretas,
    polo_por_id,
    polos,
)

urlpatterns = [
    path("polos/unidades-diretas/", listar_unidades_diretas),
    path("polos/opcoes-filtro/", listar_opcoes_filtro_polos),
    path("polos/atualizacao-lote/", atualizar_polos_em_lote),
    path("polos/", polos),
    path("polos/<uuid:polo_id>/", polo_por_id),
]
