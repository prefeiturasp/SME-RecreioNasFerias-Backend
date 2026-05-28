import pytest

from rest_framework.exceptions import AuthenticationFailed
from unittest.mock import patch

from usuarios.authentication import RfTokenAuthentication


class RequestFake:
    def __init__(self, authorization: str | None):
        self.headers = {}
        if authorization is not None:
            self.headers["Authorization"] = authorization


def test_authentication_retorna_none_sem_header():
    auth = RfTokenAuthentication()

    resultado = auth.authenticate(RequestFake(None))

    assert resultado is None


def test_authentication_retorna_none_com_schema_diferente():
    auth = RfTokenAuthentication()

    resultado = auth.authenticate(RequestFake("Basic xyz"))

    assert resultado is None


def test_authentication_retorna_none_quando_token_vazio():
    auth = RfTokenAuthentication()

    resultado = auth.authenticate(RequestFake("Bearer    "))

    assert resultado is None


def test_authentication_lanca_erro_quando_token_invalido():
    auth = RfTokenAuthentication()
    with patch("usuarios.authentication.resolver_usuario_por_token", return_value=None):
        with pytest.raises(AuthenticationFailed, match="Token inválido ou expirado"):
            auth.authenticate(RequestFake("Bearer token-invalido"))


def test_authentication_retorna_usuario_e_token():
    auth = RfTokenAuthentication()
    usuario = object()
    with patch(
        "usuarios.authentication.resolver_usuario_por_token", return_value=usuario
    ):
        resultado = auth.authenticate(RequestFake("Bearer token-valido"))

    assert resultado == (usuario, "token-valido")
