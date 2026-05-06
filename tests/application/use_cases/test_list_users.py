from unittest.mock import Mock

from django.test import TestCase

from application.use_cases.list_users import ListUsersUseCase
from domain.entities.user import User


class ListUsersUseCaseTests(TestCase):
    def test_deve_listar_usuarios_convertendo_para_output_dto(self):
        repository = Mock()
        repository.find_all.return_value = [
            User(id="u1", nome="Maria", email="maria@example.com"),
            User(id="u2", nome="Joao", email="joao@example.com"),
        ]
        use_case = ListUsersUseCase(repository)

        output = use_case.execute()

        repository.find_all.assert_called_once()
        self.assertEqual(len(output), 2)
        self.assertEqual(output[0].id, "u1")
        self.assertEqual(output[0].nome, "Maria")
        self.assertEqual(output[0].email, "maria@example.com")
        self.assertEqual(output[1].id, "u2")
        self.assertEqual(output[1].nome, "Joao")
        self.assertEqual(output[1].email, "joao@example.com")

    def test_deve_retornar_lista_vazia_quando_repositorio_nao_tem_usuarios(self):
        repository = Mock()
        repository.find_all.return_value = []
        use_case = ListUsersUseCase(repository)

        output = use_case.execute()

        repository.find_all.assert_called_once()
        self.assertEqual(output, [])
