from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import TestCase

from domain.entities.user import User
from infrastructure.repositories.django_user_repository import DjangoUserRepository


class DjangoUserRepositoryTests(TestCase):
    @patch("infrastructure.repositories.django_user_repository.UserModel")
    def test_save_deve_persistir_e_retornar_entidade(self, user_model_cls):
        model = SimpleNamespace(id="u1", nome="Maria", email="maria@example.com")
        user_model_cls.objects.update_or_create.return_value = (model, True)
        repository = DjangoUserRepository()

        output = repository.save(User(id="u1", nome="Maria", email="maria@example.com"))

        self.assertEqual(output.id, "u1")
        self.assertEqual(output.nome, "Maria")
        self.assertEqual(output.email, "maria@example.com")

    @patch("infrastructure.repositories.django_user_repository.UserModel")
    def test_find_all_deve_converter_todos_os_modelos(self, user_model_cls):
        user_model_cls.objects.all.return_value = [
            SimpleNamespace(id="u1", nome="Maria", email="maria@example.com"),
            SimpleNamespace(id="u2", nome="Joao", email="joao@example.com"),
        ]
        repository = DjangoUserRepository()

        output = repository.find_all()

        self.assertEqual(len(output), 2)
        self.assertEqual(output[0].id, "u1")
        self.assertEqual(output[1].id, "u2")

    @patch("infrastructure.repositories.django_user_repository.UserModel")
    def test_find_by_id_deve_retornar_none_quando_nao_encontrar(self, user_model_cls):
        user_model_cls.objects.filter.return_value.first.return_value = None
        repository = DjangoUserRepository()

        output = repository.find_by_id("u404")

        self.assertIsNone(output)

    @patch("infrastructure.repositories.django_user_repository.UserModel")
    def test_find_by_id_deve_retornar_entidade_quando_encontrar(self, user_model_cls):
        user_model_cls.objects.filter.return_value.first.return_value = SimpleNamespace(
            id="u1", nome="Maria", email="maria@example.com"
        )
        repository = DjangoUserRepository()

        output = repository.find_by_id("u1")

        self.assertEqual(output.id, "u1")
        self.assertEqual(output.nome, "Maria")
        self.assertEqual(output.email, "maria@example.com")

    @patch("infrastructure.repositories.django_user_repository.UserModel")
    def test_update_deve_retornar_none_quando_nao_encontrar(self, user_model_cls):
        user_model_cls.objects.filter.return_value.update.return_value = 0
        repository = DjangoUserRepository()

        output = repository.update(User(id="u404", nome="Maria", email="maria@example.com"))

        self.assertIsNone(output)

    @patch("infrastructure.repositories.django_user_repository.UserModel")
    def test_update_deve_retornar_entidade_atualizada(self, user_model_cls):
        user_model_cls.objects.filter.return_value.update.return_value = 1
        user_model_cls.objects.get.return_value = SimpleNamespace(
            id="u1", nome="Maria Nova", email="nova@example.com"
        )
        repository = DjangoUserRepository()

        output = repository.update(User(id="u1", nome="Maria Nova", email="nova@example.com"))

        self.assertEqual(output.id, "u1")
        self.assertEqual(output.nome, "Maria Nova")
        self.assertEqual(output.email, "nova@example.com")

    @patch("infrastructure.repositories.django_user_repository.UserModel")
    def test_delete_deve_retornar_true_quando_remover(self, user_model_cls):
        filter_result = Mock()
        filter_result.delete.return_value = (1, {"usuarios.UserModel": 1})
        user_model_cls.objects.filter.return_value = filter_result
        repository = DjangoUserRepository()

        output = repository.delete("u1")

        self.assertTrue(output)

    @patch("infrastructure.repositories.django_user_repository.UserModel")
    def test_delete_deve_retornar_false_quando_nao_remover(self, user_model_cls):
        filter_result = Mock()
        filter_result.delete.return_value = (0, {})
        user_model_cls.objects.filter.return_value = filter_result
        repository = DjangoUserRepository()

        output = repository.delete("u404")

        self.assertFalse(output)
