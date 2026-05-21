from django.contrib.auth import get_user_model
from django.test import TestCase

from infrastructure.repositories.usuarios_repository import UsuariosRepository

Usuario = get_user_model()


class UsuariosRepositoryTests(TestCase):
    """Testes do repositório de conta Django sincronizada no login."""

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
        usuario = Usuario.objects.get(rf="1234567")
        self.assertEqual(usuario.contexto, "DRE")
        self.assertEqual(usuario.permissoes_rbac, ["usuarios:editar"])
        self.assertFalse(usuario.has_usable_password())

        self.repository.persistir_acesso(
            rf="1234567",
            contexto="DIPED",
            permissoes=["usuarios:listar", "usuarios:editar"],
            nome="Nome Completo",
            email="user@sme.sp.gov.br",
            cpf="12345678901",
        )
        usuario.refresh_from_db()
        self.assertEqual(usuario.contexto, "DIPED")
        self.assertEqual(usuario.permissoes_rbac, ["usuarios:listar", "usuarios:editar"])
        self.assertEqual(usuario.nome_completo, "Nome Completo")
        self.assertEqual(usuario.email, "user@sme.sp.gov.br")
        self.assertEqual(usuario.cpf, "12345678901")
