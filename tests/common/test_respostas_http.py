"""Testes das respostas JSON padronizadas da API."""

import json

from django.test import SimpleTestCase

from common.respostas_http import (
    JSON_DUMPS_PARAMS,
    resposta_erro_interno,
    resposta_paginacao_invalida,
)


class RespostasHttpTests(SimpleTestCase):
    """Valida helpers de erro reutilizados pelas views HTTP."""

    def test_resposta_erro_interno_deve_retornar_status_500(self) -> None:
        """Garante conversão de exceção em JSON com status 500."""
        resposta = resposta_erro_interno(RuntimeError("falha inesperada"))

        self.assertEqual(resposta.status_code, 500)
        self.assertEqual(
            json.loads(resposta.content),
            {"error": "falha inesperada"},
        )

    def test_resposta_paginacao_invalida_deve_retornar_status_400(self) -> None:
        """Garante mensagem padronizada para parâmetros de paginação inválidos."""
        resposta = resposta_paginacao_invalida()

        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(
            json.loads(resposta.content),
            {"error": "Parâmetros de paginação inválidos"},
        )

    def test_json_dumps_params_deve_preservar_acentuacao(self) -> None:
        """Garante configuração JSON usada pelas respostas da API."""
        self.assertFalse(JSON_DUMPS_PARAMS["ensure_ascii"])
        self.assertEqual(JSON_DUMPS_PARAMS["indent"], 2)
