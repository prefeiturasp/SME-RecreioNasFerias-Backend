from django.test import TestCase

from application.services.usuarios_rbac import UsuariosRbac


class UsuariosRbacTests(TestCase):
    """Testes da aplicação de regras de RBAC."""

    def setUp(self):
        self.rbac = UsuariosRbac()

    def test_deve_remover_vazios_e_duplicados(self):
        output = self.rbac.aplicar(["usuarios:listar", "", "usuarios:listar", "usuarios:editar"])

        self.assertEqual(output, ["usuarios:listar", "usuarios:editar"])
