import importlib
import os

from unittest.mock import Mock, patch


def test_asgi_define_variavel_application():
    fake_app = object()
    with patch("django.core.asgi.get_asgi_application", return_value=fake_app):
        module = importlib.reload(importlib.import_module("config.asgi"))

    assert module.application is fake_app
    assert os.environ["DJANGO_SETTINGS_MODULE"] == "config.settings"


def test_wsgi_define_variavel_application():
    fake_app = object()
    with patch("django.core.wsgi.get_wsgi_application", return_value=fake_app):
        module = importlib.reload(importlib.import_module("config.wsgi"))

    assert module.application is fake_app
    assert os.environ["DJANGO_SETTINGS_MODULE"] == "config.settings"


def test_manage_main_executa_comandos_django():
    import manage

    execute_mock = Mock()
    with patch("django.core.management.execute_from_command_line", execute_mock):
        with patch("sys.argv", ["manage.py", "check"]):
            manage.main()

    execute_mock.assert_called_once_with(["manage.py", "check"])


def test_login_debug_so_registra_quando_habilitado():
    from config.login_debug import login_debug

    with patch("config.login_debug.logger.info") as info_mock:
        with patch.dict(os.environ, {"LOGIN_DEBUG": "0"}, clear=False):
            login_debug("fluxo.etapa", chave="valor")
        info_mock.assert_not_called()

        with patch.dict(os.environ, {"LOGIN_DEBUG": "true"}, clear=False):
            login_debug("fluxo.etapa", chave="valor")
        info_mock.assert_called_with("[login] %s | %s", "fluxo.etapa", {"chave": "valor"})


def test_login_debug_sem_contexto():
    from config.login_debug import login_debug

    with patch.dict(os.environ, {"LOGIN_DEBUG": "1"}, clear=False):
        with patch("config.login_debug.logger.info") as info_mock:
            login_debug("fluxo.sem_contexto")

    info_mock.assert_called_once_with("[login] %s", "fluxo.sem_contexto")
