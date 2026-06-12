"""Extensões do drf-spectacular para autenticação e schema OpenAPI.

O objetivo é mapear ``RfTokenAuthentication`` (Bearer assinado) para que o
Swagger UI exiba a opção de informar o token no header ``Authorization``.
"""

from drf_spectacular.extensions import OpenApiAuthenticationExtension

from usuarios.authentication import RfTokenAuthentication


class RfTokenAuthenticationScheme(OpenApiAuthenticationExtension):
    """Representa o token Bearer assinado no OpenAPI.

    Esta extensão instrui o drf-spectacular a registrar um security scheme
    equivalente a um ``http`` bearer, permitindo que o Swagger UI inclua um
    campo para ``Authorization: Bearer <token>``.
    """

    target_class = RfTokenAuthentication
    name = "bearerAuth"

    def get_security_definition(self, auto_schema):  # noqa: ANN001
        """Retorna o security scheme para OpenAPI.

        Args:
            auto_schema: Instância interna do drf-spectacular.

        Returns:
            dict: Definição do security scheme em formato OpenAPI.
        """
        return {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "Token",
        }

