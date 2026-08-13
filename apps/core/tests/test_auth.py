"""Cobertura do fluxo de autenticação do app `core`."""

import pytest
from django.urls import resolve
from rest_framework import status
from rest_framework.exceptions import (
    AuthenticationFailed,
    MethodNotAllowed,
    NotAuthenticated,
    ParseError,
    PermissionDenied,
    ValidationError,
)
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.views import APIView

from apps.core.api.views.auth import (
    LoginView,
    MeView,
)
from apps.core.authentication import RfTokenAuthentication
from apps.core.exception_handler import tratar_excecoes_drf
from apps.core.models import CargoPermitido, Usuario
from apps.core.permissions import PermissaoNaoImplementada
from apps.core.services import (
    AuthenticatedSessionData,
    AuthService,
    CargoNaoAutorizadoError,
)
from apps.integracoes.coresso.port import (
    CargoCoresso,
    CoressoIdentity,
    CoressoPort,
)

pytestmark = pytest.mark.django_db

TEST_RF = "0000001"
TEST_NOME = "Pessoa Teste"
TEST_EMAIL = "usuario.teste@example.test"
TEST_CPF = "cpf00000000"
TEST_AUTH_INPUT = "credencial-teste"


def test_authentication_retorna_none_sem_header() -> None:
    """Ignora requisições que ainda não enviam token."""
    request = APIRequestFactory().get("/api/v1/health/")
    autenticacao = RfTokenAuthentication()

    assert autenticacao.authenticate(request) is None


def test_authentication_falha_quando_header_existe() -> None:
    """Garante a falha placeholder quando um token e enviado."""
    request = APIRequestFactory().get(
        "/api/v1/health/",
        HTTP_AUTHORIZATION="Bearer token-placeholder",
    )

    with pytest.raises(AuthenticationFailed):
        RfTokenAuthentication().authenticate(request)


class FakeCoresso(CoressoPort):
    """CoreSSO fake para testes unitários do service."""

    def __init__(self, identidade: CoressoIdentity) -> None:
        """Inicializa o fake com a identidade que será devolvida no login."""
        self.identidade = identidade

    def autenticar(self, rf: str, senha: str) -> CoressoIdentity:
        assert rf == TEST_RF
        assert senha == TEST_AUTH_INPUT
        return self.identidade


def test_permission_placeholder_sempre_bloqueia() -> None:
    """Garante que a permissao placeholder sempre retorna falso."""
    request = Request(APIRequestFactory().get("/api/v1/health/"))
    permissao = PermissaoNaoImplementada()

    assert permissao.has_permission(request, APIView()) is False


def test_exception_handler_traduz_payload_drf() -> None:
    """Traduz campos padrao de erro do DRF para pt-BR."""
    excecao = ValidationError(
        {"detail": "erro", "non_field_errors": ["invalido"]}
    )

    response = tratar_excecoes_drf(excecao, {})

    assert isinstance(response, Response)
    assert response is not None
    assert response.data == {"detalhe": "erro", "erros_gerais": ["invalido"]}


def test_exception_handler_traduz_nao_autenticado() -> None:
    """Traduz a mensagem padrão de credenciais ausentes."""
    response = tratar_excecoes_drf(NotAuthenticated(), {})

    assert isinstance(response, Response)
    assert response is not None
    assert response.data == {
        "detalhe": "Credenciais de autenticacao nao foram informadas."
    }


def test_exception_handler_preserva_authentication_failed_customizado() -> (
    None
):
    """Mantem a mensagem de autenticacao quando ela ja vem do fluxo."""
    response = tratar_excecoes_drf(AuthenticationFailed("token invalido"), {})

    assert isinstance(response, Response)
    assert response is not None
    assert response.data == {"detalhe": "token invalido"}


def test_exception_handler_traduz_sem_permissao() -> None:
    """Traduz a mensagem padrão de permissão negada."""
    response = tratar_excecoes_drf(PermissionDenied(), {})

    assert isinstance(response, Response)
    assert response is not None
    assert response.data == {
        "detalhe": "Voce nao tem permissao para executar esta acao."
    }


def test_exception_handler_traduz_metodo_nao_permitido() -> None:
    """Traduz a mensagem padrão de método não permitido."""
    response = tratar_excecoes_drf(MethodNotAllowed("GET"), {})

    assert isinstance(response, Response)
    assert response is not None
    assert response.data == {"detalhe": "Metodo nao permitido."}


def test_exception_handler_traduz_payload_json_invalido() -> None:
    """Traduz a mensagem padrão de payload inválido."""
    response = tratar_excecoes_drf(ParseError(), {})

    assert isinstance(response, Response)
    assert response is not None
    assert response.data == {"detalhe": "Payload JSON invalido."}


def test_exception_handler_retorna_none_para_erro_desconhecido() -> None:
    """Mantem None quando o DRF nao sabe serializar a excecao."""
    assert tratar_excecoes_drf(RuntimeError("erro"), {}) is None


def test_auth_endpoints_estao_expostos_publicamente() -> None:
    """Confirma que as rotas públicas de auth já estão em `/api/v1/`."""
    assert resolve("/api/v1/auth/login/").url_name == "auth-login"
    assert resolve("/api/v1/auth/token/refresh/").url_name == "auth-refresh"
    assert resolve("/api/v1/auth/token/verify/").url_name == "auth-verify"
    assert resolve("/api/v1/auth/logout/").url_name == "auth-logout"
    assert resolve("/api/v1/auth/me/").url_name == "auth-me"


def test_login_view_valida_payload_no_formato_legado() -> None:
    """Garante que o contrato ja nasce com o campo `login` do legado."""
    request_factory = APIRequestFactory()
    response = LoginView.as_view()(
        request_factory.post(
            "/api/v1/auth/login/",
            {"rf": "123", "senha": "x"},
            format="json",
        )
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_auth_service_persiste_usuario_com_cargo_efetivo_sobreposto() -> None:
    """Usa `cargosSobrePosto` como cargo efetivo e persiste o usuário local."""
    cargo_permitido, _created = CargoPermitido.objects.update_or_create(
        codigo_cargo=2640,
        defaults={"descricao_cargo": "ASSISTENTE TECNICO DE EDUCACAO I"},
    )
    identidade = CoressoIdentity(
        usuario_id_externo="abc",
        rf=TEST_RF,
        nome=TEST_NOME,
        email=TEST_EMAIL,
        cpf=TEST_CPF,
        cargos=(CargoCoresso(3344, "Professor"),),
        cargos_sobrepostos=(CargoCoresso(2640, "Assistente Tecnico"),),
        cargos_efetivos=(CargoCoresso(2640, "Assistente Tecnico"),),
        perfis=(),
        unidades_lotacao=(),
        unidade_exercicio=None,
        payload_bruto={},
    )

    session = AuthService(coresso=FakeCoresso(identidade)).login(
        TEST_RF, TEST_AUTH_INPUT
    )

    usuario = Usuario.objects.get(username=TEST_RF)
    assert session.rf == TEST_RF
    assert session.cargo == cargo_permitido
    assert usuario.rf == TEST_RF
    assert usuario.nome_completo == TEST_NOME
    assert usuario.cargo_permitido == cargo_permitido
    assert usuario.has_usable_password() is False


def test_auth_service_seleciona_o_cargo_autorizado_para_o_usuario() -> None:
    """Seleciona o cargo permitido que vincula o usuário autenticado."""
    cargo_permitido, _created = CargoPermitido.objects.update_or_create(
        codigo_cargo=2640,
        defaults={"descricao_cargo": "ASSISTENTE TECNICO DE EDUCACAO I"},
    )
    identidade = CoressoIdentity(
        usuario_id_externo="abc",
        rf=TEST_RF,
        nome=TEST_NOME,
        email=TEST_EMAIL,
        cpf=TEST_CPF,
        cargos=(
            CargoCoresso(9999, "Cargo Externo"),
            CargoCoresso(2640, "Assistente Tecnico"),
        ),
        cargos_sobrepostos=(),
        cargos_efetivos=(
            CargoCoresso(9999, "Cargo Externo"),
            CargoCoresso(2640, "Assistente Tecnico"),
        ),
        perfis=(),
        unidades_lotacao=(),
        unidade_exercicio=None,
        payload_bruto={},
    )

    session = AuthService(coresso=FakeCoresso(identidade)).login(
        TEST_RF, TEST_AUTH_INPUT
    )

    usuario = Usuario.objects.get(username=TEST_RF)
    assert session.cargo == cargo_permitido
    assert usuario.cargo_permitido == cargo_permitido


def test_auth_service_bloqueia_quando_nao_ha_cargo_autorizado() -> None:
    """Bloqueia o login quando nenhum cargo efetivo está autorizado."""
    identidade = CoressoIdentity(
        usuario_id_externo="abc",
        rf=TEST_RF,
        nome=TEST_NOME,
        email=TEST_EMAIL,
        cpf=TEST_CPF,
        cargos=(CargoCoresso(3344, "Professor"),),
        cargos_sobrepostos=(),
        cargos_efetivos=(CargoCoresso(3344, "Professor"),),
        perfis=(),
        unidades_lotacao=(),
        unidade_exercicio=None,
        payload_bruto={},
    )

    with pytest.raises(CargoNaoAutorizadoError):
        AuthService(coresso=FakeCoresso(identidade)).login(
            TEST_RF, TEST_AUTH_INPUT
        )


def test_login_view_usa_contrato_de_resposta_previsto(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Garante o payload de sucesso previsto para o contrato de auth."""
    usuario = Usuario.objects.create_user(
        TEST_RF, None, TEST_AUTH_INPUT, rf=TEST_RF
    )
    cargo_permitido, _created = CargoPermitido.objects.update_or_create(
        codigo_cargo=2640,
        defaults={"descricao_cargo": "Assistente Tecnico"},
    )

    class FakeAuthService:
        def login(self, login: str, senha: str) -> AuthenticatedSessionData:
            assert login == "123"
            assert senha == "x"
            return AuthenticatedSessionData(
                usuario=usuario,
                rf="123",
                nome=TEST_NOME,
                email=TEST_EMAIL,
                cpf=TEST_CPF,
                cargo=cargo_permitido,
            )

    class FakeAccessToken:
        def __str__(self) -> str:
            return "access-token"

    class FakeRefreshToken:
        access_token = FakeAccessToken()

        @classmethod
        def for_user(cls, user: Usuario) -> "FakeRefreshToken":
            assert user == usuario
            return cls()

        def __str__(self) -> str:
            return "refresh-token"

    from apps.core.api.views import auth

    monkeypatch.setattr(auth, "auth_service", FakeAuthService())
    monkeypatch.setattr(auth, "RefreshToken", FakeRefreshToken)
    request_factory = APIRequestFactory()
    response = auth.LoginView.as_view()(
        request_factory.post(
            "/api/v1/auth/login/",
            {"login": "123", "senha": "x"},
            format="json",
        )
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data == {
        "token": "access-token",
        "rf": "123",
        "nome": TEST_NOME,
        "email": TEST_EMAIL,
        "cpf": TEST_CPF,
        "cargos": [
            {
                "codigoCargo": 2640,
                "descricaoCargo": "Assistente Tecnico",
            }
        ],
    }
    assert response.cookies["refresh_token"].value == "refresh-token"


def test_refresh_view_le_cookie_e_retorna_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Renova o access token usando o refresh token vindo do cookie."""

    class FakeTokenRefreshSerializer:
        seen_data: dict[str, str] | None = None

        def __init__(self, data: dict[str, str]) -> None:
            self.initial_data = data
            self.validated_data = {
                "access": "novo-access-token",
                "refresh": "novo-refresh-token",
            }

        def is_valid(self, raise_exception: bool = False) -> bool:
            FakeTokenRefreshSerializer.seen_data = self.initial_data
            return True

    from apps.core.api.views import auth

    monkeypatch.setattr(
        auth, "TokenRefreshSerializer", FakeTokenRefreshSerializer
    )
    request = APIRequestFactory().post(
        "/api/v1/auth/token/refresh/", {}, format="json"
    )
    request.COOKIES["refresh_token"] = "refresh-cookie-token"

    response = auth.RefreshView.as_view()(request)

    assert response.status_code == status.HTTP_200_OK
    assert response.data == {"token": "novo-access-token"}
    assert FakeTokenRefreshSerializer.seen_data == {
        "refresh": "refresh-cookie-token"
    }
    assert response.cookies["refresh_token"].value == "novo-refresh-token"


def test_verify_view_retorna_200_para_token_valido(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Confirma 200 quando o token informado e valido."""

    class FakeTokenVerifySerializer:
        def __init__(self, data: dict[str, str]) -> None:
            self.initial_data = data
            self.validated_data: dict[str, str] = {}

        def is_valid(self, raise_exception: bool = False) -> bool:
            return True

    from apps.core.api.views import auth

    monkeypatch.setattr(
        auth, "TokenVerifySerializer", FakeTokenVerifySerializer
    )
    request = APIRequestFactory().post(
        "/api/v1/auth/token/verify/",
        {"token": "token-valido"},
        format="json",
    )

    response = auth.VerifyView.as_view()(request)

    assert response.status_code == status.HTTP_200_OK


def test_verify_view_retorna_401_para_token_expirado(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Traduz token expirado ou invalido em 401 no endpoint de verify."""
    from rest_framework_simplejwt.exceptions import TokenError

    class FakeTokenVerifySerializer:
        def __init__(self, data: dict[str, str]) -> None:
            self.initial_data = data

        def is_valid(self, raise_exception: bool = False) -> bool:
            raise TokenError("Token expirado")

    from apps.core.api.views import auth

    monkeypatch.setattr(
        auth, "TokenVerifySerializer", FakeTokenVerifySerializer
    )
    request = APIRequestFactory().post(
        "/api/v1/auth/token/verify/",
        {"token": "token-expirado"},
        format="json",
    )

    response = auth.VerifyView.as_view()(request)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data == {"detalhe": "Token invalido ou expirado."}


def test_logout_view_limpa_cookie(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Remove o refresh token do cliente mesmo quando a view usa blacklist."""
    calls: list[str] = []

    class FakeRefreshToken:
        def __init__(self, token: str) -> None:
            calls.append(token)

        def blacklist(self) -> None:
            return None

    from apps.core.api.views import auth

    monkeypatch.setattr(auth, "RefreshToken", FakeRefreshToken)
    request = APIRequestFactory().post("/api/v1/auth/logout/", format="json")
    request.COOKIES["refresh_token"] = "refresh-cookie-token"

    response = auth.LogoutView.as_view()(request)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert calls == ["refresh-cookie-token"]
    assert response.cookies["refresh_token"].value == ""


def test_me_view_retorna_snapshot_local_do_usuario() -> None:
    """Retorna o payload local do usuário autenticado."""
    cargo_permitido, _created = CargoPermitido.objects.update_or_create(
        codigo_cargo=2640,
        defaults={"descricao_cargo": "Assistente Tecnico"},
    )
    usuario = Usuario.objects.create_user(
        TEST_RF,
        TEST_EMAIL,
        TEST_AUTH_INPUT,
        rf=TEST_RF,
        nome_completo=TEST_NOME,
        cpf=TEST_CPF,
        cargo_permitido=cargo_permitido,
    )

    request = APIRequestFactory().get("/api/v1/auth/me/")
    force_authenticate(request, user=usuario)

    response = MeView.as_view()(request)

    assert response.status_code == status.HTTP_200_OK
    assert response.data == {
        "rf": TEST_RF,
        "nome": TEST_NOME,
        "email": TEST_EMAIL,
        "cpf": TEST_CPF,
        "cargos": [
            {
                "codigoCargo": 2640,
                "descricaoCargo": "Assistente Tecnico",
            }
        ],
    }
