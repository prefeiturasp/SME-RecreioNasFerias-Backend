"""Classes DRF do fluxo de autenticação institucional."""

from rest_framework_simplejwt.authentication import JWTAuthentication


class RfTokenAuthentication(JWTAuthentication):
    """Backend JWT local usado pelos endpoints autenticados do projeto."""
