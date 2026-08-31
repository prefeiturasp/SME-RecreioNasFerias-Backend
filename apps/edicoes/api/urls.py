"""Rotas HTTP do app `edicoes`."""

from rest_framework.routers import DefaultRouter

from apps.edicoes.api.views.edicao_viewset import EdicaoViewSet

app_name = "edicoes"

router = DefaultRouter()
router.register("edicoes", EdicaoViewSet, basename="edicoes")

urlpatterns = router.urls
