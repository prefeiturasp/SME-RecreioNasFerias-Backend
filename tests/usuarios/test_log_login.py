"""Testes do registro de log de login."""

from django.http import HttpRequest
from django.test import SimpleTestCase, TestCase

from usuarios.log_login import (
    MENSAGEM_SUCESSO_LOGIN,
    extrair_codigo_e_descricao_cargo,
    registrar_log_login,
)
from usuarios.models import LogLoginModel


class RegistrarLogLoginTests(TestCase):
    """Valida persistência de tentativas de login."""

    def test_deve_persistir_log_com_ip_encaminhado(self):
        request = HttpRequest()
        request.META["HTTP_X_FORWARDED_FOR"] = "203.0.113.1, 10.0.0.1"
        request.META["HTTP_USER_AGENT"] = "pytest-agent/1"

        registrar_log_login(
            sucesso=True,
            login_tentativa="8080640",
            codigo_http=200,
            mensagem=MENSAGEM_SUCESSO_LOGIN,
            request=request,
            codigo_cargo=2640,
            descricao_cargo="ASSISTENTE TECNICO",
        )

        log = LogLoginModel.objects.get()
        self.assertIsInstance(log.id, int)
        self.assertGreater(log.id, 0)
        self.assertTrue(log.sucesso)
        self.assertEqual(log.codigo_cargo, 2640)
        self.assertEqual(log.descricao_cargo, "ASSISTENTE TECNICO")
        self.assertEqual(log.mensagem, MENSAGEM_SUCESSO_LOGIN)
        self.assertEqual(log.endereco_ip, "203.0.113.1")
        self.assertEqual(log.user_agent, "pytest-agent/1")

    def test_deve_persistir_log_sem_request(self):
        registrar_log_login(
            sucesso=False,
            login_tentativa="1234567",
            codigo_http=401,
            mensagem="Credenciais inválidas",
            request=None,
        )

        log = LogLoginModel.objects.get()
        self.assertIsInstance(log.id, int)
        self.assertGreater(log.id, 0)
        self.assertFalse(log.sucesso)
        self.assertIsNone(log.codigo_cargo)
        self.assertEqual(log.descricao_cargo, "")
        self.assertEqual(log.endereco_ip, "")
        self.assertEqual(log.user_agent, "")


class ExtrairCargoLogLoginTests(SimpleTestCase):
    """Valida extração de cargo para o log."""

    def test_deve_extrair_primeiro_cargo(self):
        codigo, desc = extrair_codigo_e_descricao_cargo(
            [{"codigoCargo": 2640, "descricaoCargo": "ASSISTENTE I"}]
        )
        self.assertEqual(codigo, 2640)
        self.assertEqual(desc, "ASSISTENTE I")

    def test_deve_converter_codigo_string(self):
        codigo, desc = extrair_codigo_e_descricao_cargo(
            [{"codigoCargo": "2640", "descricaoCargo": "X"}]
        )
        self.assertEqual(codigo, 2640)
        self.assertEqual(desc, "X")

    def test_deve_retornar_vazio_sem_cargos(self):
        self.assertEqual(extrair_codigo_e_descricao_cargo(None), (None, ""))
        self.assertEqual(extrair_codigo_e_descricao_cargo([]), (None, ""))
        self.assertEqual(extrair_codigo_e_descricao_cargo({}), (None, ""))
