from django.test import TestCase

from infrastructure.repositories.usuarios_repository import UsuariosRepository
from usuarios.models import UsuarioAcessoModel


class UsuariosRepositoryTests(TestCase):
    """Testes do repositório local de acesso de usuários."""

    def setUp(self):
        self.repository = UsuariosRepository()

    def test_deve_registrar_vincular_e_persistir_acesso(self):
        self.assertFalse(self.repository.existe_por_rf("1234567"))

        self.repository.registrar_localmente(
            rf="1234567",
            contexto="SME",
            permissoes=["usuarios:listar"],
        )
        self.assertTrue(self.repository.existe_por_rf("1234567"))

        self.repository.vincular_contexto_permissoes(
            rf="1234567",
            contexto="DRE",
            permissoes=["usuarios:editar"],
        )
        model = UsuarioAcessoModel.objects.get(rf="1234567")
        self.assertEqual(model.contexto, "DRE")
        self.assertEqual(model.permissoes, ["usuarios:editar"])

        self.repository.persistir_acesso(
            rf="1234567",
            contexto="DIPED",
            permissoes=["usuarios:listar", "usuarios:editar"],
        )
        model.refresh_from_db()
        self.assertEqual(model.contexto, "DIPED")
        self.assertEqual(model.permissoes, ["usuarios:listar", "usuarios:editar"])
