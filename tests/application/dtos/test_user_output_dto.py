from django.test import TestCase

from application.dtos.user_output_dto import UserOutputDTO


class UserOutputDtoTests(TestCase):
    def test_deve_converter_para_dict(self):
        dto = UserOutputDTO(id="u1", nome="Maria", email="maria@example.com")

        self.assertEqual(
            dto.to_dict(),
            {"id": "u1", "nome": "Maria", "email": "maria@example.com"},
        )
