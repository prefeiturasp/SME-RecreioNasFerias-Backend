"""Cobertura dos placeholders HTTP e de dominio de `edicoes`."""

import pytest
from rest_framework import status
from rest_framework.test import APIClient, APIRequestFactory

from apps.edicoes.api.serializers import EdicaoSerializer
from apps.edicoes.api.views.edicao_viewset import EdicaoViewSet
from apps.edicoes.models import Edicao
from apps.edicoes.services.edicao_service import EdicaoService


def test_edicoes_placeholder_interno_e_imports() -> None:
    """Mantem o handler placeholder sem expor rota publica do dominio."""
    view = EdicaoViewSet.as_view({"get": "list"})
    request = APIRequestFactory().get("/api/v1/edicoes/")
    response = view(request)

    assert response.status_code == status.HTTP_501_NOT_IMPLEMENTED
    assert response.data["detalhe"] == "Recurso ainda nao esta disponivel."
    assert Edicao is not None
    assert EdicaoSerializer() is not None


def test_edicoes_endpoint_nao_esta_exposto_publicamente() -> None:
    """Garante que o dominio nao publica rota HTTP na API atual."""
    client = APIClient()
    response = client.get("/api/v1/edicoes/")

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_edicoes_placeholder_de_service_esta_ativo() -> None:
    """Garante que o placeholder de service continua ativo."""
    with pytest.raises(NotImplementedError):
        EdicaoService().listar()
