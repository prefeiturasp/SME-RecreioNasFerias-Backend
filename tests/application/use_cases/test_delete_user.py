from unittest.mock import Mock

from django.test import TestCase

from application.use_cases.delete_user import DeleteUserUseCase


class DeleteUserUseCaseTests(TestCase):
    def test_deve_deletar_usuario_com_sucesso(self):
        repository = Mock()
        repository.delete.return_value = True
        use_case = DeleteUserUseCase(repository)

        use_case.execute("u1")

        repository.delete.assert_called_once_with("u1")

    def test_deve_lancar_erro_quando_usuario_nao_existir(self):
        repository = Mock()
        repository.delete.return_value = False
        use_case = DeleteUserUseCase(repository)

        with self.assertRaisesMessage(ValueError, "Usuário não encontrado"):
            use_case.execute("u404")
