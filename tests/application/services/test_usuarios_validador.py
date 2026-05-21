from django.test import TestCase

from application.services.usuarios_validador import UsuariosValidador


class UsuariosValidadorTests(TestCase):
    """Testes do validador de entrada do login."""

    def setUp(self):
        self.validador = UsuariosValidador()

    def test_deve_validar_com_sucesso(self):
        self.validador.validar_login(login="1234567", senha="123456")

    def test_deve_falhar_quando_login_invalido(self):
        with self.assertRaisesMessage(
            ValueError, "Login deve conter exatamente 7 dígitos"
        ):
            self.validador.validar_login(login="123", senha="123456")
