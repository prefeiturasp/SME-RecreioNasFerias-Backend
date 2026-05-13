from django.test import TestCase

from application.dtos.login_input_dto import LoginInputDto


class LoginInputDtoTests(TestCase):
    """Testes do DTO de entrada de login."""

    def test_deve_criar_dto_quando_dados_validos(self):
        dto = LoginInputDto(login="1234567", senha="minhaSenha")

        self.assertEqual(dto.login, "1234567")
        self.assertEqual(dto.senha, "minhaSenha")

    def test_deve_normalizar_login_com_espacos_ao_redor(self):
        dto = LoginInputDto(login="  1234567  ", senha="x")

        self.assertEqual(dto.login, "1234567")

    def test_deve_falhar_quando_login_ausente(self):
        with self.assertRaisesMessage(ValueError, "Login é obrigatório"):
            LoginInputDto(login="", senha="123456")

    def test_deve_falhar_quando_login_nao_tem_sete_digitos(self):
        with self.assertRaisesMessage(
            ValueError, "Login deve conter exatamente 7 dígitos"
        ):
            LoginInputDto(login="123456", senha="123456")

    def test_deve_falhar_quando_login_nao_e_numerico(self):
        with self.assertRaisesMessage(
            ValueError, "Login deve conter exatamente 7 dígitos"
        ):
            LoginInputDto(login="123456a", senha="123456")

    def test_deve_falhar_quando_senha_ausente(self):
        with self.assertRaisesMessage(ValueError, "Senha é obrigatória"):
            LoginInputDto(login="1234567", senha="")
