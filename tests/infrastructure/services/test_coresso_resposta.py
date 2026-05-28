import json
from unittest.mock import Mock

from django.test import SimpleTestCase

from infrastructure.services.coresso_resposta import extrair_mensagem_coresso


class ExtrairMensagemCoressoTests(SimpleTestCase):
    def _response(self, body):
        response = Mock()
        if isinstance(body, dict):
            response.text = json.dumps(body)
        else:
            response.text = body
        return response

    def test_deve_extrair_campo_message(self):
        response = self._response({"message": "Usuário ou senha incorretos."})
        self.assertEqual(
            extrair_mensagem_coresso(response), "Usuário ou senha incorretos."
        )

    def test_deve_extrair_texto_plano(self):
        response = self._response("Sem informações na base de dados para o Código Rf informado")
        self.assertEqual(
            extrair_mensagem_coresso(response),
            "Sem informações na base de dados para o Código Rf informado",
        )

    def test_deve_extrair_campo_mensagem(self):
        response = self._response({"mensagem": "Usuário ou senha incorretos."})
        self.assertEqual(
            extrair_mensagem_coresso(response), "Usuário ou senha incorretos."
        )

    def test_deve_retornar_vazio_quando_corpo_vazio(self):
        response = Mock()
        response.text = ""
        self.assertEqual(extrair_mensagem_coresso(response), "")
