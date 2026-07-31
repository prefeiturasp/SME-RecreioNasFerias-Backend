"""Smoke tests do endpoint de health."""

from rest_framework import status
from rest_framework.test import APIClient


def test_health_retorna_status_ok() -> None:
    """Verifica o endpoint publico de healthcheck."""
    client = APIClient()
    response = client.get("/api/v1/health/")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "ok"}
