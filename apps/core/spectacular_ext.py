"""Extensões do drf-spectacular para o app `core`."""

from typing import Any

from drf_spectacular.extensions import OpenApiAuthenticationExtension


class RfTokenAuthenticationScheme(OpenApiAuthenticationExtension):
    """Descreve a autenticação JWT local do projeto no schema OpenAPI."""

    target_class = "apps.core.authentication.RfTokenAuthentication"
    name = "BearerAuth"

    def get_security_definition(self, auto_schema: Any) -> dict[str, str]:
        """Expõe o esquema Bearer JWT da autenticação local no OpenAPI."""
        return {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
