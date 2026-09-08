"""Rotas HTTP do app `definicoes_polos`."""

from rest_framework.routers import DefaultRouter

from apps.definicoes_polos.api.views.definicao_polo_viewset import (
    DefinicaoPoloViewSet,
)

app_name = "definicoes_polos"

router = DefaultRouter()
router.register(
    "definicoes-polos",
    DefinicaoPoloViewSet,
    basename="definicoes-polos",
)

urlpatterns = router.urls
