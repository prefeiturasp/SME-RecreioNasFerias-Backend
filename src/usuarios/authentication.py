"""
Autenticação DRF via token assinado emitido após login no CoreSSO.

Integra com ``REST_FRAMEWORK.DEFAULT_AUTHENTICATION_CLASSES`` para
popular ``request.user`` em endpoints protegidos sem sessão Django.
"""

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from usuarios.auth_tokens import resolver_usuario_por_token


class RfTokenAuthentication(BaseAuthentication):
    """Resolve ``request.user`` a partir do header ``Authorization: Bearer``.

    Retorna ``None`` quando o header está ausente ou usa outro esquema,
    permitindo views públicas no mesmo projeto. Tokens inválidos geram
    ``AuthenticationFailed`` (HTTP 401).
    """

    keyword = "Bearer"

    def authenticate(self, request):
        """Valida Bearer token e retorna tupla ``(usuario, token)``.

        Args:
            request: Requisição HTTP do Django/DRF.

        Returns:
            tuple | None: ``(usuario, token)`` quando o header é Bearer válido;
                ``None`` quando outro esquema ou ausência de header (permite
                views públicas).

        Raises:
            AuthenticationFailed: Se o token estiver presente porém inválido ou
                expirado.
        """
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith(f"{self.keyword} "):
            return None

        token = auth_header[len(self.keyword) + 1 :].strip()
        if not token:
            return None

        usuario = resolver_usuario_por_token(token)
        if usuario is None:
            raise AuthenticationFailed("Token inválido ou expirado.")

        return (usuario, token)
