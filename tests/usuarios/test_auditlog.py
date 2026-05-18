"""Testes de auditoria de alterações em tabelas (django-auditlog)."""

import uuid

from auditlog.models import LogEntry
from django.contrib.auth import get_user_model
from django.test import TestCase

from usuarios.models import CargoPermitidoModel, UserModel

Usuario = get_user_model()


class AuditlogRegistroTests(TestCase):
    def test_criar_cargo_gera_logentry(self):
        cargo = CargoPermitidoModel.objects.create(
            codigo_cargo=99001,
            descricao_cargo="Cargo teste auditlog",
        )

        entries = LogEntry.objects.get_for_object(cargo)
        self.assertEqual(entries.count(), 1)
        self.assertEqual(entries.first().action, LogEntry.Action.CREATE)
        self.assertEqual(cargo.history.count(), 1)
        self.assertEqual(cargo.history.first().action, LogEntry.Action.CREATE)

    def test_atualizar_usuario_django_gera_logentry(self):
        Usuario.objects.create(
            rf="1234567",
            email="1234567@test.local",
            contexto="contexto-inicial",
            permissoes_rbac=["ler"],
        )
        usuario = Usuario.objects.get(rf="1234567")
        usuario.contexto = "contexto-atualizado"
        usuario.permissoes_rbac = ["ler", "escrever"]
        usuario.save()

        entries = LogEntry.objects.get_for_object(usuario)
        self.assertGreaterEqual(entries.count(), 2)
        self.assertEqual(
            entries.order_by("-timestamp").first().action,
            LogEntry.Action.UPDATE,
        )
        self.assertGreaterEqual(usuario.history.count(), 2)
        self.assertEqual(
            usuario.history.order_by("-timestamp").first().action,
            LogEntry.Action.UPDATE,
        )

    def test_excluir_user_model_gera_logentry(self):
        user_id = uuid.uuid4()
        user = UserModel.objects.create(
            id=user_id,
            nome="Usuario Audit",
            email="audit@example.com",
        )
        user_pk = str(user.pk)
        user.delete()

        entries = LogEntry.objects.filter(
            content_type__model="usermodel",
            object_pk=user_pk,
        )
        self.assertTrue(entries.filter(action=LogEntry.Action.DELETE).exists())

    def test_log_login_nao_gera_auditlog(self):
        from usuarios.log_login import registrar_log_login
        from usuarios.models import LogLoginModel

        registrar_log_login(
            sucesso=True,
            login_tentativa="rf123",
            codigo_http=200,
            mensagem="ok",
            request=None,
        )

        self.assertEqual(LogLoginModel.objects.count(), 1)
        self.assertFalse(
            LogEntry.objects.filter(
                content_type__model="logloginmodel",
            ).exists()
        )
