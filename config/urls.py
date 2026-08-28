"""Rotas raiz do projeto Recreio nas Férias."""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

API_V1 = "api/v1/"

urlpatterns = [
    path("admin/", admin.site.urls),
    path(f"{API_V1}schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        f"{API_V1}docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="docs",
    ),
    path(API_V1, include("apps.core.api.urls")),
    path(API_V1, include("apps.edicoes.api.urls")),
    path(API_V1, include("apps.polos.api.urls")),
]
