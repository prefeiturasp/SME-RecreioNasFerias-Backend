"""
Mapeamento de rotas HTTP do app de usuários.

Monta endpoints de autenticação CoreSSO e, quando habilitado, o CRUD legado
de usuários sob o prefixo ``/api/`` definido em ``config.urls``.

As rotas de CRUD são recalculadas quando ``USUARIOS_CRUD_ENABLED`` muda em
runtime (ex.: testes com ``override_settings``).
"""

from django.conf import settings
from django.core.signals import setting_changed
from django.urls import clear_url_caches, path

from .views import login, user_by_id, users


def _montar_urlpatterns() -> list:
    """Montar rotas conforme a flag ``USUARIOS_CRUD_ENABLED``.

    Returns:
        list: Rotas de autenticação e, opcionalmente, CRUD legado de usuários.
    """
    rotas = [
        path("auth/login/", login),
    ]
    if settings.USUARIOS_CRUD_ENABLED:
        rotas += [
            path("usuarios/", users),
            path("usuarios/<uuid:user_id>/", user_by_id),
        ]
    return rotas


urlpatterns = _montar_urlpatterns()


def _recarregar_urlpatterns_ao_mudar_setting(
    setting: str | None = None,
    **_: object,
) -> None:
    """Atualizar ``urlpatterns`` quando a flag de CRUD for alterada.

    Args:
        setting (str | None): Nome da configuração alterada no Django.
        **_ (object): Demais argumentos enviados pelo sinal (ignorados).
    """
    if setting != "USUARIOS_CRUD_ENABLED":
        return
    urlpatterns.clear()
    urlpatterns.extend(_montar_urlpatterns())
    clear_url_caches()


setting_changed.connect(
    _recarregar_urlpatterns_ao_mudar_setting,
    dispatch_uid="usuarios_urls_crud_toggle",
)
