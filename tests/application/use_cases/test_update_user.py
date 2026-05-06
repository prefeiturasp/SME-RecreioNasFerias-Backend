from unittest.mock import Mock

from django.test import TestCase

from application.dtos.update_user_dto import UpdateUserDto
from application.use_cases.update_user import UpdateUserUseCase
from domain.entities.user import User


class UpdateUserUseCaseTests(TestCase):
    def test_deve_atualizar_usuario_com_sucesso(self):
        repository = Mock()
        repository.find_by_id.return_value = User(
            id="u1",
            nome="Maria",
            email="maria@example.com",
        )
        repository.update.return_value = User(
            id="u1",
            nome="Maria Atualizada",
            email="maria.atualizada@example.com",
        )
        use_case = UpdateUserUseCase(repository)
        dto = UpdateUserDto(
            nome="Maria Atualizada",
            email="maria.atualizada@example.com",
        )

        output = use_case.execute("u1", dto)

        repository.find_by_id.assert_called_once_with("u1")
        repository.update.assert_called_once()
        updated_user_arg = repository.update.call_args[0][0]
        self.assertEqual(updated_user_arg.id, "u1")
        self.assertEqual(updated_user_arg.nome, "Maria Atualizada")
        self.assertEqual(updated_user_arg.email, "maria.atualizada@example.com")
        self.assertEqual(output.id, "u1")
        self.assertEqual(output.nome, "Maria Atualizada")
        self.assertEqual(output.email, "maria.atualizada@example.com")

    def test_deve_atualizar_somente_nome(self):
        repository = Mock()
        repository.find_by_id.return_value = User(
            id="u1",
            nome="Maria",
            email="maria@example.com",
        )
        repository.update.return_value = User(
            id="u1",
            nome="Maria Atualizada",
            email="maria@example.com",
        )
        use_case = UpdateUserUseCase(repository)
        dto = UpdateUserDto(nome="Maria Atualizada")

        output = use_case.execute("u1", dto)

        updated_user_arg = repository.update.call_args[0][0]
        self.assertEqual(updated_user_arg.nome, "Maria Atualizada")
        self.assertEqual(updated_user_arg.email, "maria@example.com")
        self.assertEqual(output.nome, "Maria Atualizada")
        self.assertEqual(output.email, "maria@example.com")

    def test_deve_atualizar_somente_email(self):
        repository = Mock()
        repository.find_by_id.return_value = User(
            id="u1",
            nome="Maria",
            email="maria@example.com",
        )
        repository.update.return_value = User(
            id="u1",
            nome="Maria",
            email="maria.atualizada@example.com",
        )
        use_case = UpdateUserUseCase(repository)
        dto = UpdateUserDto(email="maria.atualizada@example.com")

        output = use_case.execute("u1", dto)

        updated_user_arg = repository.update.call_args[0][0]
        self.assertEqual(updated_user_arg.nome, "Maria")
        self.assertEqual(updated_user_arg.email, "maria.atualizada@example.com")
        self.assertEqual(output.nome, "Maria")
        self.assertEqual(output.email, "maria.atualizada@example.com")

    def test_deve_lancar_erro_quando_usuario_nao_existir(self):
        repository = Mock()
        repository.find_by_id.return_value = None
        use_case = UpdateUserUseCase(repository)
        dto = UpdateUserDto(nome="Maria")

        with self.assertRaisesMessage(ValueError, "Usuário não encontrado"):
            use_case.execute("u404", dto)

    def test_deve_lancar_erro_quando_update_retornar_none(self):
        repository = Mock()
        repository.find_by_id.return_value = User(
            id="u1",
            nome="Maria",
            email="maria@example.com",
        )
        repository.update.return_value = None
        use_case = UpdateUserUseCase(repository)
        dto = UpdateUserDto(nome="Maria Atualizada")

        with self.assertRaisesMessage(ValueError, "Usuário não encontrado"):
            use_case.execute("u1", dto)
