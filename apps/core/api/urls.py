"""Rotas HTTP do app `core`."""

from django.urls import path

from apps.core.api.views.health import health_check

app_name = "core"

urlpatterns = [
    path("health/", health_check, name="health"),
]
