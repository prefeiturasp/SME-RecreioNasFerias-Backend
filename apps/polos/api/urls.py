"""Rotas HTTP do app `polos`."""

from rest_framework.routers import DefaultRouter

from apps.polos.api.views.polo_viewset import PoloViewSet

app_name = "polos"

router = DefaultRouter()
router.register("", PoloViewSet, basename="polos")

urlpatterns = router.urls
