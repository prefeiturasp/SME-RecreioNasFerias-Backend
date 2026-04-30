from django.test import TestCase

from application.dtos.create_user_dto import CreateUserDto


class CreateUserDtoTests(TestCase):
    def test_deve_criar_dto_quando_dados_validos(self):
        dto = CreateUserDto(nome="Maria", email="maria@example.com")

        self.assertEqual(dto.nome, "Maria")
        self.assertEqual(dto.email, "maria@example.com")

    def test_deve_falhar_quando_nome_ausente(self):
        with self.assertRaisesMessage(ValueError, "Nome é obrigatório"):
            CreateUserDto(nome=None, email="maria@example.com")

    def test_deve_falhar_quando_email_ausente(self):
        with self.assertRaisesMessage(ValueError, "Email é obrigatório"):
            CreateUserDto(nome="Maria", email=None)
