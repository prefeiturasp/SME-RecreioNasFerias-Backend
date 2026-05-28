from domain.ports.auth_provider import AuthProvider


class AuthProviderImpl(AuthProvider):
    def login(self, rf: str, senha: str) -> tuple[str, str | None]:
        return (f"token-{rf}", senha or None)


def test_auth_provider_login_esta_marcado_como_abstractmethod():
    assert getattr(AuthProvider.login, "__isabstractmethod__", False) is True
    assert "login" in AuthProvider.__abstractmethods__


def test_auth_provider_impl_retorna_tokens():
    provider = AuthProviderImpl()

    access_token, refresh_token = provider.login("1234567", "segredo")

    assert access_token == "token-1234567"
    assert refresh_token == "segredo"


def test_auth_provider_impl_retorna_refresh_none():
    provider = AuthProviderImpl()

    access_token, refresh_token = provider.login("1234567", "")

    assert access_token == "token-1234567"
    assert refresh_token is None
