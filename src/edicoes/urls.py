"""
Mapeamento de rotas HTTP do app de edições.

Expõe endpoints de cadastro, listagem, consulta, atualização e exclusão sob ``/api/``.
"""

from django.urls import path

from edicoes.views import edicao_por_id, edicoes

urlpatterns = [
    path("edicoes/", edicoes),
    path("edicoes/<uuid:edicao_id>/", edicao_por_id),
]
