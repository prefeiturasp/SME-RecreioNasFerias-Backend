from django.test import TestCase

from domain.entities.user import User


class UserEntityTests(TestCase):
    def test_deve_criar_usuario_com_dados_validos(self):
        user = User(nome="Maria", email="maria@example.com", id="u1")

        self.assertEqual(user.id, "u1")
        self.assertEqual(user.nome, "Maria")
        self.assertEqual(user.email, "maria@example.com")

    def test_deve_falhar_quando_nome_ausente(self):
        with self.assertRaisesMessage(ValueError, "Nome é obrigatório"):
            User(nome="", email="maria@example.com")

    def test_deve_falhar_quando_email_ausente(self):
        with self.assertRaisesMessage(ValueError, "Email é obrigatório"):
            User(nome="Maria", email="")
