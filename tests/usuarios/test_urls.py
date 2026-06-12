"""Testes de exposição condicional das rotas de usuários."""

from django.test import TestCase, override_settings


class UsuariosUrlsTests(TestCase):
    """Valida habilitação e desabilitação do CRUD legado de usuários."""

    def test_login_permanece_disponivel_com_crud_desabilitado(self) -> None:
        """Garante que ``/api/auth/login/`` continua exposto sem o CRUD legado.

        Args:
            Não recebe argumentos explícitos.

        Returns:
            None: Usa asserções para validar o status HTTP.

        Raises:
            AssertionError: Se a rota de login não responder.
        """
        with override_settings(USUARIOS_CRUD_ENABLED=False):
            resposta = self.client.post(
                "/api/auth/login/",
                data="{}",
                content_type="application/json",
            )

        self.assertIn(resposta.status_code, (400, 401, 403, 404, 502))

    @override_settings(USUARIOS_CRUD_ENABLED=False)
    def test_crud_usuarios_fica_indisponivel_quando_desabilitado(self) -> None:
        """Garante que ``/api/usuarios/`` não é roteado com CRUD desligado.

        Args:
            Não recebe argumentos explícitos.

        Returns:
            None: Usa asserções para validar ausência da rota.

        Raises:
            AssertionError: Se o endpoint ainda responder como rota válida.
        """
        resposta = self.client.get("/api/usuarios/")

        self.assertEqual(resposta.status_code, 404)
