from unittest.mock import Mock

from django.test import TestCase

from application.use_cases.get_user_by_id import GetUserByIdUseCase
from domain.entities.user import User


class GetUserByIdUseCaseTests(TestCase):
    def test_deve_retornar_usuario_quando_existir(self):
        repository = Mock()
        repository.find_by_id.return_value = User(
            id="u1",
            nome="Maria",
            email="maria@example.com",
        )
        use_case = GetUserByIdUseCase(repository)

        output = use_case.execute("u1")

        repository.find_by_id.assert_called_once_with("u1")
        self.assertEqual(output.id, "u1")
        self.assertEqual(output.nome, "Maria")
        self.assertEqual(output.email, "maria@example.com")

    def test_deve_lancar_erro_quando_usuario_nao_existir(self):
        repository = Mock()
        repository.find_by_id.return_value = None
        use_case = GetUserByIdUseCase(repository)

        with self.assertRaisesMessage(ValueError, "Usuário não encontrado"):
            use_case.execute("u404")
