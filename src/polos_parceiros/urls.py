"""
Mapeamento de rotas HTTP do app de polos parceiros.

Expõe endpoints de cadastro, listagem, consulta, atualização e exclusão sob ``/api/``.
"""

from django.urls import path

from polos_parceiros.views import polo_parceiro_por_id, polos_parceiros

urlpatterns = [
    path("polos-parceiros/", polos_parceiros),
    path("polos-parceiros/<uuid:polo_id>/", polo_parceiro_por_id),
]
