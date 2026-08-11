"""Cobertura do fluxo de autenticação placeholder do app `core`."""

import pytest
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
from rest_framework.test import APIClient, APIRequestFactory
from rest_framework.views import APIView

from apps.core.api.serializers import AuthMessageSerializer
from apps.core.api.views.auth import login_view, logout_view
from apps.core.authentication import RfTokenAuthentication
from apps.core.exception_handler import tratar_excecoes_drf
from apps.core.permissions import PermissaoNaoImplementada
from apps.core.services import (
    AuthService,
    gerar_token,
    normalizar_permissoes,
    validar_token,
)


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


def test_helpers_de_token_lancam_not_implemented() -> None:
    """Garante o comportamento esperado dos helpers placeholder."""
    with pytest.raises(NotImplementedError):
        gerar_token({"rf": "123"})

    with pytest.raises(NotImplementedError):
        validar_token("token")


def test_service_de_auth_lanca_not_implemented() -> None:
    """Garante que o placeholder de servico continua ativo."""
    service = AuthService()

    with pytest.raises(NotImplementedError):
        service.login("123", "senha")

    with pytest.raises(NotImplementedError):
        service.resolve_token("token")

    with pytest.raises(NotImplementedError):
        service.logout("Bearer token")


def test_rbac_tem_comportamento_basico() -> None:
    """Valida o utilitario simples de normalizacao de permissoes."""
    permissoes = normalizar_permissoes([" Admin ", "admin", "", "Leitura"])

    assert permissoes == {"admin", "leitura"}


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


def test_serializer_placeholder_de_mensagem_esta_configurado() -> None:
    """Valida o serializer de resposta placeholder dos endpoints de auth."""
    serializer = AuthMessageSerializer(data={"detalhe": "ok"})

    assert serializer.is_valid() is True


def test_auth_placeholders_internos_retorna_501() -> None:
    """Mantem os handlers placeholder mesmo sem expor rotas publicas."""
    request_factory = APIRequestFactory()

    login_response = login_view(
        request_factory.post(
            "/api/v1/auth/login/",
            {"login": "123", "senha": "x"},
            format="json",
        )
    )
    logout_response = logout_view(
        request_factory.post("/api/v1/auth/logout/", format="json")
    )

    assert login_response.status_code == status.HTTP_501_NOT_IMPLEMENTED
    assert (
        login_response.data["detalhe"]
        == "Autenticacao institucional ainda nao esta disponivel."
    )
    assert logout_response.status_code == status.HTTP_501_NOT_IMPLEMENTED
    assert (
        logout_response.data["detalhe"]
        == "Autenticacao institucional ainda nao esta disponivel."
    )


def test_auth_endpoints_nao_estao_expostos_publicamente() -> None:
    """Garante que login e logout nao aparecem na API publica atual."""
    client = APIClient()
    login_response = client.post(
        "/api/v1/auth/login/", {"login": "123", "senha": "x"}
    )
    logout_response = client.post("/api/v1/auth/logout/")

    assert login_response.status_code == status.HTTP_404_NOT_FOUND
    assert logout_response.status_code == status.HTTP_404_NOT_FOUND


def test_login_view_valida_payload_no_formato_legado() -> None:
    """Garante que o contrato ja nasce com o campo `login` do legado."""
    request_factory = APIRequestFactory()
    response = login_view(
        request_factory.post(
            "/api/v1/auth/login/",
            {"rf": "123", "senha": "x"},
            format="json",
        )
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_login_view_usa_contrato_de_resposta_previsto(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Garante o payload de sucesso previsto para o contrato de auth."""

    class FakeAuthService:
        def login(self, login: str, senha: str) -> dict:
            assert login == "123"
            assert senha == "x"
            return {
                "usuarioId": "1",
                "status": 1,
                "nome": "Usuario Teste",
                "codigoRf": "123",
            }

        def logout(self, authorization: str | None = None) -> None:
            return None

    from apps.core.api.views import auth

    monkeypatch.setattr(auth, "auth_service", FakeAuthService())
    request_factory = APIRequestFactory()
    response = auth.login_view(
        request_factory.post(
            "/api/v1/auth/login/",
            {"login": "123", "senha": "x"},
            format="json",
        )
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data == {
        "usuarioId": "1",
        "status": 1,
        "nome": "Usuario Teste",
        "codigoRf": "123",
    }
