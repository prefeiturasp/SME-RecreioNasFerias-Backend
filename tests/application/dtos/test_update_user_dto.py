from django.test import TestCase

from application.dtos.update_user_dto import UpdateUserDto


class UpdateUserDtoTests(TestCase):
    def test_deve_aceitar_apenas_nome(self):
        dto = UpdateUserDto(nome="Maria")
        self.assertEqual(dto.nome, "Maria")
        self.assertIsNone(dto.email)

    def test_deve_aceitar_apenas_email(self):
        dto = UpdateUserDto(email="maria@example.com")
        self.assertIsNone(dto.nome)
        self.assertEqual(dto.email, "maria@example.com")

    def test_deve_aceitar_nome_e_email(self):
        dto = UpdateUserDto(nome="Maria", email="maria@example.com")
        self.assertEqual(dto.nome, "Maria")
        self.assertEqual(dto.email, "maria@example.com")

    def test_deve_falhar_sem_campos_para_atualizar(self):
        with self.assertRaisesMessage(
            ValueError, "Informe ao menos um campo para atualização"
        ):
            UpdateUserDto()

    def test_deve_falhar_quando_nome_vazio(self):
        with self.assertRaisesMessage(ValueError, "Nome é obrigatório"):
            UpdateUserDto(nome="")

    def test_deve_falhar_quando_email_vazio(self):
        with self.assertRaisesMessage(ValueError, "Email é obrigatório"):
            UpdateUserDto(email="")
