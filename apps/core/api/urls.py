"""Rotas HTTP do app `core`."""

from django.urls import path

from apps.core.api.views.auth import (
    LoginView,
    LogoutView,
    MeView,
    RefreshView,
    VerifyView,
)
from apps.core.api.views.health import HealthCheckView

app_name = "core"

urlpatterns = [
    path("health/", HealthCheckView.as_view(), name="health"),
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/token/refresh/", RefreshView.as_view(), name="auth-refresh"),
    path("auth/token/verify/", VerifyView.as_view(), name="auth-verify"),
    path("auth/logout/", LogoutView.as_view(), name="auth-logout"),
    path("auth/me/", MeView.as_view(), name="auth-me"),
]
