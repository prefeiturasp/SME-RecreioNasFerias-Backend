import json
from unittest.mock import Mock, patch

from django.test import TestCase


class CreateUserViewTests(TestCase):
    def test_deve_retornar_405_para_metodo_nao_permitido(self):
        response = self.client.put("/api/usuarios/")

        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.json(), {"error": "Método não permitido"})

    @patch("usuarios.views.ListUsersUseCase")
    @patch("usuarios.views.DjangoUserRepository")
    def test_deve_listar_usuarios_com_sucesso(self, repository_cls, use_case_cls):
        user_1 = Mock(
            to_dict=lambda: {
                "id": "u1",
                "nome": "Maria",
                "email": "maria@example.com",
            }
        )
        user_2 = Mock(
            to_dict=lambda: {
                "id": "u2",
                "nome": "Joao",
                "email": "joao@example.com",
            }
        )
        use_case_instance = Mock()
        use_case_instance.execute.return_value = [user_1, user_2]
        use_case_cls.return_value = use_case_instance

        response = self.client.get("/api/usuarios/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            [
                {"id": "u1", "nome": "Maria", "email": "maria@example.com"},
                {"id": "u2", "nome": "Joao", "email": "joao@example.com"},
            ],
        )
        repository_cls.assert_called_once()
        use_case_cls.assert_called_once()
        use_case_instance.execute.assert_called_once()

    @patch("usuarios.views.GetUserByIdUseCase")
    @patch("usuarios.views.DjangoUserRepository")
    def test_deve_buscar_usuario_por_id_com_sucesso(self, repository_cls, use_case_cls):
        use_case_instance = Mock()
        use_case_instance.execute.return_value = Mock(
            to_dict=lambda: {
                "id": "u1",
                "nome": "Maria",
                "email": "maria@example.com",
            }
        )
        use_case_cls.return_value = use_case_instance

        response = self.client.get("/api/usuarios/11111111-1111-1111-1111-111111111111/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"id": "u1", "nome": "Maria", "email": "maria@example.com"},
        )
        repository_cls.assert_called_once()
        use_case_cls.assert_called_once()
        use_case_instance.execute.assert_called_once()

    @patch("usuarios.views.GetUserByIdUseCase")
    @patch("usuarios.views.DjangoUserRepository")
    def test_deve_retornar_404_quando_get_by_id_nao_encontrar(
        self, repository_cls, use_case_cls
    ):
        use_case_instance = Mock()
        use_case_instance.execute.side_effect = ValueError("Usuário não encontrado")
        use_case_cls.return_value = use_case_instance

        response = self.client.get("/api/usuarios/11111111-1111-1111-1111-111111111111/")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"error": "Usuário não encontrado"})
        repository_cls.assert_called_once()
        use_case_cls.assert_called_once()
        use_case_instance.execute.assert_called_once()

    @patch("usuarios.views.ListUsersUseCase")
    @patch("usuarios.views.DjangoUserRepository")
    def test_deve_retornar_500_quando_listagem_falhar(self, repository_cls, use_case_cls):
        use_case_instance = Mock()
        use_case_instance.execute.side_effect = Exception("Erro ao listar usuários")
        use_case_cls.return_value = use_case_instance

        response = self.client.get("/api/usuarios/")

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json(), {"error": "Erro ao listar usuários"})
        repository_cls.assert_called_once()
        use_case_cls.assert_called_once()
        use_case_instance.execute.assert_called_once()

    @patch("usuarios.views.CreateUserUseCase")
    @patch("usuarios.views.DjangoUserRepository")
    def test_deve_criar_usuario_com_sucesso(self, repository_cls, use_case_cls):
        use_case_instance = Mock()
        use_case_instance.execute.return_value = Mock(
            to_dict=lambda: {
                "id": "abc-123",
                "nome": "Maria",
                "email": "maria@example.com",
            }
        )
        use_case_cls.return_value = use_case_instance

        response = self.client.post(
            "/api/usuarios/",
            data=json.dumps({"nome": "Maria", "email": "maria@example.com"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.json(),
            {
                "id": "abc-123",
                "nome": "Maria",
                "email": "maria@example.com",
            },
        )
        repository_cls.assert_called_once()
        use_case_cls.assert_called_once()
        use_case_instance.execute.assert_called_once()

    @patch("usuarios.views.UpdateUserUseCase")
    @patch("usuarios.views.DjangoUserRepository")
    def test_deve_atualizar_usuario_com_sucesso(self, repository_cls, use_case_cls):
        use_case_instance = Mock()
        use_case_instance.execute.return_value = Mock(
            to_dict=lambda: {
                "id": "u1",
                "nome": "Maria Atualizada",
                "email": "maria.atualizada@example.com",
            }
        )
        use_case_cls.return_value = use_case_instance

        response = self.client.put(
            "/api/usuarios/11111111-1111-1111-1111-111111111111/",
            data=json.dumps(
                {"nome": "Maria Atualizada", "email": "maria.atualizada@example.com"}
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "id": "u1",
                "nome": "Maria Atualizada",
                "email": "maria.atualizada@example.com",
            },
        )
        repository_cls.assert_called_once()
        use_case_cls.assert_called_once()
        use_case_instance.execute.assert_called_once()

    @patch("usuarios.views.UpdateUserUseCase")
    @patch("usuarios.views.DjangoUserRepository")
    def test_deve_atualizar_usuario_com_sucesso_apenas_nome(
        self, repository_cls, use_case_cls
    ):
        use_case_instance = Mock()
        use_case_instance.execute.return_value = Mock(
            to_dict=lambda: {
                "id": "u1",
                "nome": "Maria Atualizada",
                "email": "maria@example.com",
            }
        )
        use_case_cls.return_value = use_case_instance

        response = self.client.put(
            "/api/usuarios/11111111-1111-1111-1111-111111111111/",
            data=json.dumps({"nome": "Maria Atualizada"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"id": "u1", "nome": "Maria Atualizada", "email": "maria@example.com"},
        )
        repository_cls.assert_called_once()
        use_case_cls.assert_called_once()
        use_case_instance.execute.assert_called_once()

    @patch("usuarios.views.UpdateUserUseCase")
    @patch("usuarios.views.DjangoUserRepository")
    def test_deve_atualizar_usuario_com_sucesso_apenas_email(
        self, repository_cls, use_case_cls
    ):
        use_case_instance = Mock()
        use_case_instance.execute.return_value = Mock(
            to_dict=lambda: {
                "id": "u1",
                "nome": "Maria",
                "email": "maria.atualizada@example.com",
            }
        )
        use_case_cls.return_value = use_case_instance

        response = self.client.put(
            "/api/usuarios/11111111-1111-1111-1111-111111111111/",
            data=json.dumps({"email": "maria.atualizada@example.com"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "id": "u1",
                "nome": "Maria",
                "email": "maria.atualizada@example.com",
            },
        )
        repository_cls.assert_called_once()
        use_case_cls.assert_called_once()
        use_case_instance.execute.assert_called_once()

    @patch("usuarios.views.UpdateUserUseCase")
    @patch("usuarios.views.DjangoUserRepository")
    def test_deve_retornar_404_quando_update_nao_encontrar_usuario(
        self, repository_cls, use_case_cls
    ):
        use_case_instance = Mock()
        use_case_instance.execute.side_effect = ValueError("Usuário não encontrado")
        use_case_cls.return_value = use_case_instance

        response = self.client.put(
            "/api/usuarios/11111111-1111-1111-1111-111111111111/",
            data=json.dumps({"nome": "Maria", "email": "maria@example.com"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"error": "Usuário não encontrado"})
        repository_cls.assert_called_once()
        use_case_cls.assert_called_once()
        use_case_instance.execute.assert_called_once()

    def test_deve_retornar_400_quando_update_sem_campos(self):
        response = self.client.put(
            "/api/usuarios/11111111-1111-1111-1111-111111111111/",
            data=json.dumps({}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(), {"error": "Informe ao menos um campo para atualização"}
        )

    @patch("usuarios.views.DeleteUserUseCase")
    @patch("usuarios.views.DjangoUserRepository")
    def test_deve_deletar_usuario_com_sucesso(self, repository_cls, use_case_cls):
        use_case_instance = Mock()
        use_case_cls.return_value = use_case_instance

        response = self.client.delete(
            "/api/usuarios/11111111-1111-1111-1111-111111111111/"
        )

        self.assertEqual(response.status_code, 204)
        repository_cls.assert_called_once()
        use_case_cls.assert_called_once()
        use_case_instance.execute.assert_called_once()

    @patch("usuarios.views.DeleteUserUseCase")
    @patch("usuarios.views.DjangoUserRepository")
    def test_deve_retornar_404_quando_delete_nao_encontrar_usuario(
        self, repository_cls, use_case_cls
    ):
        use_case_instance = Mock()
        use_case_instance.execute.side_effect = ValueError("Usuário não encontrado")
        use_case_cls.return_value = use_case_instance

        response = self.client.delete(
            "/api/usuarios/11111111-1111-1111-1111-111111111111/"
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"error": "Usuário não encontrado"})
        repository_cls.assert_called_once()
        use_case_cls.assert_called_once()
        use_case_instance.execute.assert_called_once()

    def test_deve_retornar_500_quando_payload_invalido(self):
        response = self.client.post(
            "/api/usuarios/",
            data=json.dumps({"nome": "", "email": "maria@example.com"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json(), {"error": "Nome é obrigatório"})
