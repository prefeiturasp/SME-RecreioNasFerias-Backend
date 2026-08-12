"""Cobertura dos placeholders HTTP e de dominio de `polos`."""

import pytest
from rest_framework import status
from rest_framework.test import APIClient, APIRequestFactory

from apps.polos.api.serializers import PoloSerializer
from apps.polos.api.views.polo_viewset import PoloViewSet
from apps.polos.models import Polo
from apps.polos.services.polo_service import PoloService


def test_polos_placeholder_interno_e_imports() -> None:
    """Mantem o handler placeholder sem expor rota publica do dominio."""
    view = PoloViewSet.as_view({"get": "list"})
    request = APIRequestFactory().get("/api/v1/polos/")
    response = view(request)

    assert response.status_code == status.HTTP_501_NOT_IMPLEMENTED
    assert response.data["detalhe"] == "Recurso ainda nao esta disponivel."
    assert Polo is not None
    assert PoloSerializer() is not None


def test_polos_endpoint_nao_esta_exposto_publicamente() -> None:
    """Garante que o dominio nao publica rota HTTP na API atual."""
    client = APIClient()
    response = client.get("/api/v1/polos/")

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_polos_placeholder_de_service_esta_ativo() -> None:
    """Garante que o placeholder de service continua ativo."""
    with pytest.raises(NotImplementedError):
        PoloService().listar()
