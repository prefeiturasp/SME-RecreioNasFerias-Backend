"""Mapeamento de rotas HTTP do app de usuários."""

from django.urls import path
from .views import login, users, user_by_id

urlpatterns = [
    path("usuarios/", users),
    path("usuarios/<uuid:user_id>/", user_by_id),
    path("auth/login/", login),
]
