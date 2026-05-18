"""Autenticação DRF via token assinado emitido após login no CoreSSO."""

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from usuarios.auth_tokens import resolver_usuario_por_token


class RfTokenAuthentication(BaseAuthentication):
    """Resolve ``request.user`` a partir do header ``Authorization: Bearer <token>``."""

    keyword = "Bearer"

    def authenticate(self, request):
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
