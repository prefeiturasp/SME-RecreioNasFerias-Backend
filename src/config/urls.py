"""
Roteamento HTTP principal do projeto.

Expõe schema OpenAPI, Swagger UI e rotas da API em ``/api/``.
"""

from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


class SchemaAPIView(SpectacularAPIView):
    """Endpoint de schema OpenAPI excluído da própria documentação."""

    schema = None


urlpatterns = [
    path("api/schema/", SchemaAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("api/", include("usuarios.urls")),
    path("api/", include("edicoes.urls")),
    path("api/", include("polos.urls")),
]
