from unittest.mock import Mock

from django.test import TestCase

from application.dtos.create_user_dto import CreateUserDto
from application.use_cases.create_user import CreateUserUseCase
from domain.entities.user import User


class CreateUserUseCaseTests(TestCase):
    def test_deve_salvar_usuario_e_retornar_output(self):
        repository = Mock()
        repository.save.return_value = User(
            id="123",
            nome="Maria",
            email="maria@example.com",
        )
        use_case = CreateUserUseCase(repository)
        dto = CreateUserDto(nome="Maria", email="maria@example.com")

        output = use_case.execute(dto)

        repository.save.assert_called_once()
        saved_user_arg = repository.save.call_args[0][0]
        self.assertEqual(saved_user_arg.nome, "Maria")
        self.assertEqual(saved_user_arg.email, "maria@example.com")
        self.assertEqual(output.id, "123")
        self.assertEqual(output.nome, "Maria")
        self.assertEqual(output.email, "maria@example.com")
