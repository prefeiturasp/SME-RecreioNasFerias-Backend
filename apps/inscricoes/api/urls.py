"""Rotas HTTP do domínio de inscrições."""

from rest_framework.routers import DefaultRouter

from apps.inscricoes.api.views.inscricao_viewset import InscricaoViewSet

app_name = "inscricoes"

router = DefaultRouter()
router.register("inscricoes", InscricaoViewSet, basename="inscricoes")

urlpatterns = router.urls
