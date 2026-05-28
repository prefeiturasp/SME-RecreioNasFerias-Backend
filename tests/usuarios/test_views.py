import json
from unittest.mock import Mock, patch

from django.test import TestCase

from application.exceptions import CargoNaoAutorizadoError
from usuarios.log_login import MENSAGEM_SUCESSO_LOGIN
from usuarios.models import LogLoginModel


class CreateUserViewTests(TestCase):
    def test_login_deve_retornar_405_para_metodo_nao_permitido(self):
        response = self.client.get("/api/auth/login/")

        self.assertEqual(response.status_code, 405)
        self.assertIn("detail", response.json())

    @patch("usuarios.views.LoginUserUseCase")
    @patch("usuarios.views.UsuariosService")
    @patch("usuarios.views.get_user_model")
    @patch("usuarios.views.gerar_token_acesso")
    def test_login_deve_autenticar_com_sucesso(
        self, gerar_token_mock, get_user_model_mock, service_cls, use_case_cls
    ):
        usuario_mock = Mock()
        get_user_model_mock.return_value.objects.get.return_value = usuario_mock
        gerar_token_mock.return_value = "token-de-teste"
        use_case_instance = Mock()
        use_case_instance.execute.return_value = Mock(
            to_dict=lambda: {
                "rf": "8080640",
                "cpf": "22712612876",
                "email": "vania.montefusco@sme.prefeitura.sp.gov.br",
                "cargos": [
                    {
                        "codigoCargo": 2640,
                        "descricaoCargo": "ASSISTENTE TECNICO DE EDUCACAO I",
                        "codigoUnidade": "121000",
                        "descricaoUnidade": "COORDENADORIA DOS CENTROS EDUCACIONAIS UNIFICADOS - COCEU",
                        "codigoDre": "121000",
                        "contratoExterno": False,
                    }
                ],
                "nome": "VANIA FERREIRA DA SILVA CANEKI",
                "inexistenteEol": False,
            }
        )
        use_case_cls.return_value = use_case_instance

        response = self.client.post(
            "/api/auth/login/",
            data=json.dumps({"login": "1234567", "senha": "123456"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "rf": "8080640",
                "cpf": "22712612876",
                "email": "vania.montefusco@sme.prefeitura.sp.gov.br",
                "cargos": [
                    {
                        "codigoCargo": 2640,
                        "descricaoCargo": "ASSISTENTE TECNICO DE EDUCACAO I",
                        "codigoUnidade": "121000",
                        "descricaoUnidade": "COORDENADORIA DOS CENTROS EDUCACIONAIS UNIFICADOS - COCEU",
                        "codigoDre": "121000",
                        "contratoExterno": False,
                    }
                ],
                "nome": "VANIA FERREIRA DA SILVA CANEKI",
                "inexistenteEol": False,
                "token": "token-de-teste",
            },
        )
        get_user_model_mock.return_value.objects.get.assert_called_once()
        gerar_token_mock.assert_called_once_with(usuario_mock)
        service_cls.assert_called_once()
        use_case_cls.assert_called_once()
        use_case_instance.execute.assert_called_once()
        log = LogLoginModel.objects.get()
        self.assertIsInstance(log.id, int)
        self.assertGreater(log.id, 0)
        self.assertTrue(log.sucesso)
        self.assertEqual(log.login_tentativa, "8080640")
        self.assertEqual(log.codigo_http, 200)
        self.assertEqual(log.mensagem, MENSAGEM_SUCESSO_LOGIN)
        self.assertEqual(log.codigo_cargo, 2640)
        self.assertEqual(log.descricao_cargo, "ASSISTENTE TECNICO DE EDUCACAO I")

    @patch("usuarios.views.LoginUserUseCase")
    @patch("usuarios.views.UsuariosService")
    def test_login_deve_retornar_401_para_credenciais_invalidas(
        self, service_cls, use_case_cls
    ):
        from application.exceptions import CoressoRespostaError

        mensagem = "Usuário ou senha incorretos."
        use_case_instance = Mock()
        use_case_instance.execute.side_effect = CoressoRespostaError(
            mensagem, status_http=401
        )
        use_case_cls.return_value = use_case_instance

        response = self.client.post(
            "/api/auth/login/",
            data=json.dumps({"login": "1234567", "senha": "errada"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"error": mensagem})
        service_cls.assert_called_once()
        use_case_cls.assert_called_once()
        use_case_instance.execute.assert_called_once()
        log = LogLoginModel.objects.get()
        self.assertIsInstance(log.id, int)
        self.assertGreater(log.id, 0)
        self.assertFalse(log.sucesso)
        self.assertEqual(log.login_tentativa, "1234567")
        self.assertEqual(log.codigo_http, 401)
        self.assertEqual(log.mensagem, mensagem)
        self.assertIsNone(log.codigo_cargo)
        self.assertEqual(log.descricao_cargo, "")

    @patch("usuarios.views.LoginUserUseCase")
    @patch("usuarios.views.UsuariosService")
    def test_login_deve_retornar_404_quando_dados_sigpae_sem_rf(
        self, service_cls, use_case_cls
    ):
        from application.exceptions import CoressoRespostaError

        mensagem = "Sem informações na base de dados para o Código Rf informado"
        use_case_instance = Mock()
        use_case_instance.execute.side_effect = CoressoRespostaError(
            mensagem, status_http=404
        )
        use_case_cls.return_value = use_case_instance

        response = self.client.post(
            "/api/auth/login/",
            data=json.dumps({"login": "1234567", "senha": "123456"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"error": mensagem})
        log = LogLoginModel.objects.get()
        self.assertFalse(log.sucesso)
        self.assertEqual(log.login_tentativa, "1234567")
        self.assertEqual(log.codigo_http, 404)
        self.assertEqual(log.mensagem, mensagem)

    @patch("usuarios.views.LoginUserUseCase")
    @patch("usuarios.views.UsuariosService")
    def test_login_deve_retornar_403_quando_cargo_nao_autorizado(
        self, service_cls, use_case_cls
    ):
        use_case_instance = Mock()
        use_case_instance.execute.side_effect = CargoNaoAutorizadoError(
            "Cargo não autorizado para acesso ao sistema."
        )
        use_case_cls.return_value = use_case_instance

        response = self.client.post(
            "/api/auth/login/",
            data=json.dumps({"login": "1234567", "senha": "123456"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json(),
            {"error": "Cargo não autorizado para acesso ao sistema."},
        )
        log = LogLoginModel.objects.get()
        self.assertFalse(log.sucesso)
        self.assertEqual(log.codigo_http, 403)

    @patch("usuarios.views.UsuariosService")
    def test_login_integracao_retorna_403_quando_cargo_nao_esta_nos_permitidos(
        self, service_cls
    ):
        """Fluxo real até o banco: integração devolve cargo cujo código não existe na tabela."""
        codigo_nao_permitido = 888877766
        service_instancia = Mock()
        service_instancia.autenticar.return_value = {
            "usuarioId": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            "status": 1,
            "nome": "USUARIO CARGO BLOQUEADO",
            "codigoRf": "1234567",
            "rf": "1234567",
            "cpf": None,
            "email": None,
            "cargos": [
                {
                    "codigoCargo": codigo_nao_permitido,
                    "descricaoCargo": "CARGO FORA DA LISTA PERMITIDA",
                }
            ],
            "inexistenteEol": False,
            "contexto": "SME",
            "permissoes": [],
        }
        service_cls.return_value = service_instancia

        response = self.client.post(
            "/api/auth/login/",
            data=json.dumps({"login": "1234567", "senha": "qualquer123"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)
        body = response.json()
        self.assertEqual(
            body,
            {"error": "Cargo não autorizado para acesso ao sistema."},
        )
        self.assertNotIn("token", body)
        service_cls.assert_called_once()
        service_instancia.autenticar.assert_called_once_with(
            login="1234567", senha="qualquer123"
        )
        log = LogLoginModel.objects.get()
        self.assertFalse(log.sucesso)
        self.assertEqual(log.codigo_http, 403)
        self.assertEqual(log.login_tentativa, "1234567")
        self.assertIn("autorizado", log.mensagem.lower())

    def test_login_deve_retornar_400_quando_payload_json_invalido(self):
        response = self.client.post(
            "/api/auth/login/",
            data="{rf:1234567",
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"error": "Payload JSON inválido"})
        log = LogLoginModel.objects.get()
        self.assertIsInstance(log.id, int)
        self.assertGreater(log.id, 0)
        self.assertFalse(log.sucesso)
        self.assertEqual(log.login_tentativa, "")
        self.assertEqual(log.codigo_http, 400)
        self.assertEqual(log.mensagem, "Payload JSON inválido")

    def test_login_deve_retornar_400_quando_login_invalido(self):
        response = self.client.post(
            "/api/auth/login/",
            data=json.dumps({"login": "123", "senha": "123456"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(), {"error": "Login deve conter exatamente 7 dígitos"}
        )
        log = LogLoginModel.objects.get()
        self.assertIsInstance(log.id, int)
        self.assertGreater(log.id, 0)
        self.assertFalse(log.sucesso)
        self.assertEqual(log.login_tentativa, "123")
        self.assertEqual(log.codigo_http, 400)
        self.assertEqual(log.mensagem, "Login deve conter exatamente 7 dígitos")

    @patch("usuarios.views.LoginUserUseCase")
    @patch("usuarios.views.UsuariosService")
    def test_login_deve_retornar_502_quando_coresso_indisponivel(
        self, service_cls, use_case_cls
    ):
        from application.exceptions import CoressoIndisponivelError, ERRO_CORESSO_INDISPONIVEL

        use_case_instance = Mock()
        use_case_instance.execute.side_effect = CoressoIndisponivelError()
        use_case_cls.return_value = use_case_instance

        response = self.client.post(
            "/api/auth/login/",
            data=json.dumps({"login": "1234567", "senha": "123456"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json(), {"error": ERRO_CORESSO_INDISPONIVEL})
        service_cls.assert_called_once()
        use_case_cls.assert_called_once()
        use_case_instance.execute.assert_called_once()
        log = LogLoginModel.objects.get()
        self.assertIsInstance(log.id, int)
        self.assertGreater(log.id, 0)
        self.assertFalse(log.sucesso)
        self.assertEqual(log.login_tentativa, "1234567")
        self.assertEqual(log.codigo_http, 502)
        self.assertEqual(log.mensagem, ERRO_CORESSO_INDISPONIVEL)

    @patch("usuarios.views.LoginUserUseCase")
    @patch("usuarios.views.UsuariosService")
    def test_login_deve_retornar_500_com_mensagem_generica_em_erro_interno(
        self, service_cls, use_case_cls
    ):
        from application.exceptions import ERRO_INTERNO_API

        use_case_instance = Mock()
        use_case_instance.execute.side_effect = Exception("detalhe interno")
        use_case_cls.return_value = use_case_instance

        response = self.client.post(
            "/api/auth/login/",
            data=json.dumps({"login": "1234567", "senha": "123456"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json(), {"error": ERRO_INTERNO_API})
        log = LogLoginModel.objects.get()
        self.assertEqual(log.mensagem, ERRO_INTERNO_API)

    def test_deve_retornar_405_para_metodo_nao_permitido(self):
        response = self.client.put("/api/usuarios/")

        self.assertEqual(response.status_code, 405)
        self.assertIn("detail", response.json())

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
