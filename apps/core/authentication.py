"""Classes DRF do fluxo de autenticação institucional.

Este módulo concentra a adaptação do fluxo de autenticação do projeto para a
interface esperada pelo Django REST Framework.
"""

from typing import Any

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request

from apps.core.services import AuthService


class RfTokenAuthentication(BaseAuthentication):
    """Valida o header de autenticação do fluxo institucional.

    No estado atual o autenticador apenas preserva a superficie publica do
    DRF: requisicoes sem header seguem sem autenticacao e qualquer token
    informado ainda e tratado como nao implementado.
    """

    def __init__(self, auth_service: AuthService | None = None) -> None:
        """Inicializa a dependência do fluxo futuro de autenticação.

        Args:
            auth_service: Serviço de autenticação a ser usado pela classe.
                Quando omitido, utiliza a implementação padrão do projeto.
        """
        self.auth_service = auth_service or AuthService()

    def authenticate(self, request: Request) -> tuple[Any, Any] | None:
        """Valida o header Authorization presente na requisição.

        Args:
            request: Requisição HTTP recebida pelo DRF.

        Returns:
            Tupla ``(usuario, token)`` quando a autenticação existir, ou
            ``None`` quando a requisição não informar credenciais.

        Raises:
            AuthenticationFailed: Se um token for informado antes da
                implementacao do fluxo real.
        """
        autorizacao = request.headers.get("Authorization", "").strip()
        if not autorizacao:
            return None

        raise AuthenticationFailed("Autenticacao ainda nao implementada.")
