"""Testes dos endpoints HTTP de edições."""

import json
from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import DatabaseError
from django.test import TestCase

from edicoes.models import Edicao
from usuarios.auth_tokens import gerar_token_acesso


class EdicoesViewTests(TestCase):
    """Valida fluxo HTTP de listagem, consulta, criação, atualização e exclusão."""

    def setUp(self) -> None:
        """Configura um usuário autenticado para chamadas aos endpoints protegidos."""
        Usuario = get_user_model()
        self.usuario = Usuario.objects.create(
            rf="1234567",
            email="autenticado@test.local",
            is_active=True,
        )
        self.usuario.set_unusable_password()
        self.usuario.save()
        token = gerar_token_acesso(self.usuario)
        self.auth_headers = {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    def test_deve_retornar_401_quando_nao_autenticado(self) -> None:
        """Garante que o endpoint exige autenticação.

        Args:
            Não recebe argumentos explícitos.

        Returns:
            None: Usa asserções para validar status e formato de erro.

        Raises:
            AssertionError: Se o status ou o corpo não estiverem corretos.
        """
        resposta = self.client.get("/api/edicoes/")
        self.assertIn(resposta.status_code, (401, 403))
        self.assertIn("detail", resposta.json())

    def test_deve_listar_edicoes_cadastradas(self) -> None:
        """Garante que ``GET /api/edicoes/`` retorna os registros persistidos.

        Args:
            Não recebe argumentos explícitos.

        Returns:
            None: Usa asserções para validar status e payload.

        Raises:
            AssertionError: Se status ou corpo da resposta estiverem incorretos.
        """
        edicao = Edicao.objects.create(
            nome="Edição Janeiro 2026",
            periodo_edicao_inicio=date(2026, 1, 10),
            periodo_edicao_fim=date(2026, 1, 20),
            periodo_inscricoes_inicio=date(2025, 12, 1),
            periodo_inscricoes_fim=date(2025, 12, 31),
        )

        resposta = self.client.get("/api/edicoes/", **self.auth_headers)

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(
            resposta.json(),
            {
                "results": [
                    {
                        "id": str(edicao.id),
                        "nome": "Edição Janeiro 2026",
                        "periodoEdicao": {"de": "2026-01-10", "ate": "2026-01-20"},
                        "periodoInscricoes": {"de": "2025-12-01", "ate": "2025-12-31"},
                        "quantidadeInscritos": None,
                        "quantidadeAtendimentoEfetivo": None,
                        "quantidadePasseios": None,
                        "quantidadeApresentacoes": None,
                    }
                ],
                "page": 1,
                "pageSize": 10,
                "total": 1,
                "totalPages": 1,
            },
        )

    def test_deve_paginar_listagem_de_edicoes(self) -> None:
        """Garante paginação da listagem via parâmetros ``page`` e ``pageSize``."""
        for indice in range(1, 16):
            Edicao.objects.create(
                nome=f"Edição {indice:02d}",
                periodo_edicao_inicio=date(2026, 1, indice),
                periodo_edicao_fim=date(2026, 1, indice),
                periodo_inscricoes_inicio=date(2025, 12, 1),
                periodo_inscricoes_fim=date(2025, 12, 31),
            )

        resposta = self.client.get(
            "/api/edicoes/?page=2&pageSize=5",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 200)
        corpo = resposta.json()
        self.assertEqual(len(corpo["results"]), 5)
        self.assertEqual(corpo["page"], 2)
        self.assertEqual(corpo["pageSize"], 5)
        self.assertEqual(corpo["total"], 15)
        self.assertEqual(corpo["totalPages"], 3)

    def test_deve_retornar_400_para_parametros_de_paginacao_invalidos(self) -> None:
        """Garante erro quando ``page`` ou ``pageSize`` forem inválidos."""
        resposta = self.client.get(
            "/api/edicoes/?page=0&pageSize=abc",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(
            resposta.json(),
            {"error": "Parâmetros de paginação inválidos"},
        )

    def test_deve_limitar_page_size_maximo_na_listagem(self) -> None:
        """Garante que ``pageSize`` acima do máximo seja limitado automaticamente."""
        Edicao.objects.create(
            nome="Edição Paginação",
            periodo_edicao_inicio=date(2026, 2, 1),
            periodo_edicao_fim=date(2026, 2, 10),
            periodo_inscricoes_inicio=date(2026, 1, 1),
            periodo_inscricoes_fim=date(2026, 1, 20),
        )

        resposta = self.client.get(
            "/api/edicoes/?pageSize=500",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json()["pageSize"], 100)

    def test_deve_retornar_400_para_payload_json_invalido_no_cadastro(self) -> None:
        """Garante erro quando o corpo do POST não for JSON válido."""
        resposta = self.client.post(
            "/api/edicoes/",
            data="{nome:}",
            content_type="application/json",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(resposta.json(), {"error": "Payload JSON inválido"})

    def test_deve_retornar_400_para_payload_json_invalido_na_atualizacao(self) -> None:
        """Garante erro quando o corpo do PUT não for JSON válido."""
        edicao = Edicao.objects.create(
            nome="Edição JSON Inválido",
            periodo_edicao_inicio=date(2026, 5, 1),
            periodo_edicao_fim=date(2026, 5, 31),
            periodo_inscricoes_inicio=date(2026, 4, 1),
            periodo_inscricoes_fim=date(2026, 4, 20),
        )

        resposta = self.client.put(
            f"/api/edicoes/{edicao.id}/",
            data="{nome:}",
            content_type="application/json",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(resposta.json(), {"error": "Payload JSON inválido"})

    def test_deve_atualizar_periodos_da_edicao(self) -> None:
        """Garante atualização dos períodos de edição e inscrições."""
        edicao = Edicao.objects.create(
            nome="Edição Períodos",
            periodo_edicao_inicio=date(2026, 6, 1),
            periodo_edicao_fim=date(2026, 6, 30),
            periodo_inscricoes_inicio=date(2026, 5, 1),
            periodo_inscricoes_fim=date(2026, 5, 20),
        )
        payload = {
            "periodoEdicao": {"de": "2026-07-01", "ate": "2026-07-31"},
            "periodoInscricoes": {"de": "2026-06-01", "ate": "2026-06-20"},
        }

        resposta = self.client.put(
            f"/api/edicoes/{edicao.id}/",
            data=json.dumps(payload),
            content_type="application/json",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 200)
        edicao.refresh_from_db()
        self.assertEqual(edicao.periodo_edicao_inicio, date(2026, 7, 1))
        self.assertEqual(edicao.periodo_edicao_fim, date(2026, 7, 31))
        self.assertEqual(edicao.periodo_inscricoes_inicio, date(2026, 6, 1))
        self.assertEqual(edicao.periodo_inscricoes_fim, date(2026, 6, 20))

    def test_deve_cadastrar_edicao_com_sucesso(self) -> None:
        """Garante criação de edição válida via ``POST /api/edicoes/``.

        Args:
            Não recebe argumentos explícitos.

        Returns:
            None: Usa asserções para validar status, payload e persistência.

        Raises:
            AssertionError: Se a edição não for criada corretamente.
        """
        payload = {
            "nome": "Edição Julho 2026",
            "periodoEdicao": {"de": "2026-07-01", "ate": "2026-07-31"},
            "periodoInscricoes": {"de": "2026-06-01", "ate": "2026-06-20"},
        }

        resposta = self.client.post(
            "/api/edicoes/",
            data=json.dumps(payload),
            content_type="application/json",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 201)
        self.assertEqual(resposta.json()["nome"], "Edição Julho 2026")
        self.assertTrue(Edicao.objects.filter(nome="Edição Julho 2026").exists())

    def test_deve_cadastrar_edicao_com_quantidades(self) -> None:
        """Garante persistência dos campos de quantidade informados no cadastro."""
        payload = {
            "nome": "Edição Agosto 2026",
            "periodoEdicao": {"de": "2026-08-01", "ate": "2026-08-31"},
            "periodoInscricoes": {"de": "2026-07-01", "ate": "2026-07-20"},
            "quantidadeInscritos": 120,
            "quantidadeAtendimentoEfetivo": 95,
            "quantidadePasseios": 8,
            "quantidadeApresentacoes": 3,
        }

        resposta = self.client.post(
            "/api/edicoes/",
            data=json.dumps(payload),
            content_type="application/json",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 201)
        corpo = resposta.json()
        self.assertEqual(corpo["quantidadeInscritos"], 120)
        self.assertEqual(corpo["quantidadeAtendimentoEfetivo"], 95)
        self.assertEqual(corpo["quantidadePasseios"], 8)
        self.assertEqual(corpo["quantidadeApresentacoes"], 3)

        edicao = Edicao.objects.get(nome="Edição Agosto 2026")
        self.assertEqual(edicao.quantidade_inscritos, 120)
        self.assertEqual(edicao.quantidade_atendimento_efetivo, 95)
        self.assertEqual(edicao.quantidade_passeios, 8)
        self.assertEqual(edicao.quantidade_apresentacoes, 3)

    def test_deve_cadastrar_edicao_com_quantidades_zeradas_como_null(self) -> None:
        """Garante que quantidades zeradas ou ausentes sejam persistidas como null."""
        payload = {
            "nome": "Edição Setembro 2026",
            "periodoEdicao": {"de": "2026-09-01", "ate": "2026-09-30"},
            "periodoInscricoes": {"de": "2026-08-01", "ate": "2026-08-20"},
            "quantidadeInscritos": 0,
            "quantidadeAtendimentoEfetivo": 0,
            "quantidadePasseios": 0,
            "quantidadeApresentacoes": 0,
        }

        resposta = self.client.post(
            "/api/edicoes/",
            data=json.dumps(payload),
            content_type="application/json",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 201)
        corpo = resposta.json()
        self.assertIsNone(corpo["quantidadeInscritos"])
        self.assertIsNone(corpo["quantidadeAtendimentoEfetivo"])
        self.assertIsNone(corpo["quantidadePasseios"])
        self.assertIsNone(corpo["quantidadeApresentacoes"])

        edicao = Edicao.objects.get(nome="Edição Setembro 2026")
        self.assertIsNone(edicao.quantidade_inscritos)
        self.assertIsNone(edicao.quantidade_atendimento_efetivo)
        self.assertIsNone(edicao.quantidade_passeios)
        self.assertIsNone(edicao.quantidade_apresentacoes)

    def test_deve_retornar_400_para_nome_duplicado(self) -> None:
        """Garante bloqueio de cadastro com nome já existente.

        Args:
            Não recebe argumentos explícitos.

        Returns:
            None: Usa asserções para validar status e mensagem de erro.

        Raises:
            AssertionError: Se o erro esperado não for retornado.
        """
        Edicao.objects.create(
            nome="Edição Verão 2026",
            periodo_edicao_inicio=date(2026, 1, 1),
            periodo_edicao_fim=date(2026, 1, 15),
            periodo_inscricoes_inicio=date(2025, 12, 1),
            periodo_inscricoes_fim=date(2025, 12, 20),
        )
        payload = {
            "nome": "Edição Verão 2026",
            "periodoEdicao": {"de": "2026-02-01", "ate": "2026-02-15"},
            "periodoInscricoes": {"de": "2026-01-01", "ate": "2026-01-20"},
        }

        resposta = self.client.post(
            "/api/edicoes/",
            data=json.dumps(payload),
            content_type="application/json",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(
            resposta.json(),
            {"error": "Erro: já existe edição com o nome cadastrado"},
        )

    def test_deve_retornar_400_para_periodo_duplicado(self) -> None:
        """Garante bloqueio de cadastro com período de edição repetido.

        Args:
            Não recebe argumentos explícitos.

        Returns:
            None: Usa asserções para validar status e mensagem de erro.

        Raises:
            AssertionError: Se o erro esperado não for retornado.
        """
        Edicao.objects.create(
            nome="Edição Outono 2026",
            periodo_edicao_inicio=date(2026, 3, 1),
            periodo_edicao_fim=date(2026, 3, 31),
            periodo_inscricoes_inicio=date(2026, 2, 1),
            periodo_inscricoes_fim=date(2026, 2, 20),
        )
        payload = {
            "nome": "Edição Inverno 2026",
            "periodoEdicao": {"de": "2026-03-01", "ate": "2026-03-31"},
            "periodoInscricoes": {"de": "2026-06-01", "ate": "2026-06-20"},
        }

        resposta = self.client.post(
            "/api/edicoes/",
            data=json.dumps(payload),
            content_type="application/json",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(
            resposta.json(),
            {"error": "Erro: já existe edição no período cadastrado"},
        )

    def test_deve_retornar_401_quando_buscar_edicao_sem_autenticacao(self) -> None:
        """Garante que a consulta por ID exige autenticação."""
        edicao = Edicao.objects.create(
            nome="Edição Protegida",
            periodo_edicao_inicio=date(2026, 4, 1),
            periodo_edicao_fim=date(2026, 4, 30),
            periodo_inscricoes_inicio=date(2026, 3, 1),
            periodo_inscricoes_fim=date(2026, 3, 20),
        )

        resposta = self.client.get(f"/api/edicoes/{edicao.id}/")

        self.assertIn(resposta.status_code, (401, 403))
        self.assertIn("detail", resposta.json())

    def test_deve_buscar_edicao_por_id(self) -> None:
        """Garante consulta de edição via ``GET /api/edicoes/<uuid>/``."""
        edicao = Edicao.objects.create(
            nome="Edição Consulta 2026",
            periodo_edicao_inicio=date(2026, 3, 1),
            periodo_edicao_fim=date(2026, 3, 31),
            periodo_inscricoes_inicio=date(2026, 2, 1),
            periodo_inscricoes_fim=date(2026, 2, 20),
            quantidade_inscritos=50,
            quantidade_atendimento_efetivo=40,
            quantidade_passeios=5,
            quantidade_apresentacoes=2,
        )

        resposta = self.client.get(f"/api/edicoes/{edicao.id}/", **self.auth_headers)

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(
            resposta.json(),
            {
                "id": str(edicao.id),
                "nome": "Edição Consulta 2026",
                "periodoEdicao": {"de": "2026-03-01", "ate": "2026-03-31"},
                "periodoInscricoes": {"de": "2026-02-01", "ate": "2026-02-20"},
                "quantidadeInscritos": 50,
                "quantidadeAtendimentoEfetivo": 40,
                "quantidadePasseios": 5,
                "quantidadeApresentacoes": 2,
            },
        )

    def test_deve_retornar_404_quando_buscar_edicao_inexistente(self) -> None:
        """Garante 404 ao consultar UUID inexistente."""
        resposta = self.client.get(
            "/api/edicoes/11111111-1111-1111-1111-111111111111/",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 404)
        self.assertEqual(resposta.json(), {"error": "Edição não encontrada"})

    def test_deve_atualizar_edicao_com_sucesso(self) -> None:
        """Garante atualização parcial via ``PUT /api/edicoes/<uuid>/``.

        Args:
            Não recebe argumentos explícitos.

        Returns:
            None: Usa asserções para validar status, payload e persistência.

        Raises:
            AssertionError: Se a edição não for atualizada corretamente.
        """
        edicao = Edicao.objects.create(
            nome="Edição Primavera 2026",
            periodo_edicao_inicio=date(2026, 9, 1),
            periodo_edicao_fim=date(2026, 9, 30),
            periodo_inscricoes_inicio=date(2026, 8, 1),
            periodo_inscricoes_fim=date(2026, 8, 20),
        )

        resposta = self.client.put(
            f"/api/edicoes/{edicao.id}/",
            data=json.dumps({"nome": "Edição Primavera Atualizada 2026"}),
            content_type="application/json",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json()["nome"], "Edição Primavera Atualizada 2026")
        edicao.refresh_from_db()
        self.assertEqual(edicao.nome, "Edição Primavera Atualizada 2026")

    def test_deve_retornar_404_quando_atualizar_edicao_inexistente(self) -> None:
        """Garante 404 ao atualizar UUID inexistente.

        Args:
            Não recebe argumentos explícitos.

        Returns:
            None: Usa asserções para validar status e mensagem.

        Raises:
            AssertionError: Se o status não for 404.
        """
        resposta = self.client.put(
            "/api/edicoes/11111111-1111-1111-1111-111111111111/",
            data=json.dumps({"nome": "Edição Inexistente"}),
            content_type="application/json",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 404)
        self.assertEqual(resposta.json(), {"error": "Edição não encontrada"})

    def test_deve_retornar_400_quando_atualizar_sem_campos(self) -> None:
        """Garante bloqueio de atualização sem campos no payload.

        Args:
            Não recebe argumentos explícitos.

        Returns:
            None: Usa asserções para validar status e mensagem.

        Raises:
            AssertionError: Se o erro esperado não for retornado.
        """
        edicao = Edicao.objects.create(
            nome="Edição Outubro 2026",
            periodo_edicao_inicio=date(2026, 10, 1),
            periodo_edicao_fim=date(2026, 10, 31),
            periodo_inscricoes_inicio=date(2026, 9, 1),
            periodo_inscricoes_fim=date(2026, 9, 20),
        )

        resposta = self.client.put(
            f"/api/edicoes/{edicao.id}/",
            data=json.dumps({}),
            content_type="application/json",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(
            resposta.json(),
            {"error": "Informe ao menos um campo para atualização"},
        )

    def test_deve_retornar_400_ao_atualizar_com_nome_duplicado(self) -> None:
        """Garante bloqueio de atualização para nome já cadastrado em outra edição.

        Args:
            Não recebe argumentos explícitos.

        Returns:
            None: Usa asserções para validar status e mensagem.

        Raises:
            AssertionError: Se o erro esperado não for retornado.
        """
        Edicao.objects.create(
            nome="Edição Original",
            periodo_edicao_inicio=date(2026, 4, 1),
            periodo_edicao_fim=date(2026, 4, 30),
            periodo_inscricoes_inicio=date(2026, 3, 1),
            periodo_inscricoes_fim=date(2026, 3, 20),
        )
        edicao = Edicao.objects.create(
            nome="Edição Destino",
            periodo_edicao_inicio=date(2026, 5, 1),
            periodo_edicao_fim=date(2026, 5, 31),
            periodo_inscricoes_inicio=date(2026, 4, 1),
            periodo_inscricoes_fim=date(2026, 4, 20),
        )

        resposta = self.client.put(
            f"/api/edicoes/{edicao.id}/",
            data=json.dumps({"nome": "Edição Original"}),
            content_type="application/json",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(
            resposta.json(),
            {"error": "Erro: já existe edição com o nome cadastrado"},
        )

    def test_deve_deletar_edicao_com_sucesso(self) -> None:
        """Garante exclusão via ``DELETE /api/edicoes/<uuid>/``.

        Args:
            Não recebe argumentos explícitos.

        Returns:
            None: Usa asserções para validar status e remoção no banco.

        Raises:
            AssertionError: Se a edição não for removida.
        """
        edicao = Edicao.objects.create(
            nome="Edição Para Excluir",
            periodo_edicao_inicio=date(2026, 11, 1),
            periodo_edicao_fim=date(2026, 11, 30),
            periodo_inscricoes_inicio=date(2026, 10, 1),
            periodo_inscricoes_fim=date(2026, 10, 20),
        )

        resposta = self.client.delete(f"/api/edicoes/{edicao.id}/", **self.auth_headers)

        self.assertEqual(resposta.status_code, 204)
        self.assertFalse(Edicao.objects.filter(pk=edicao.id).exists())

    def test_deve_retornar_404_quando_deletar_edicao_inexistente(self) -> None:
        """Garante 404 ao excluir UUID inexistente.

        Args:
            Não recebe argumentos explícitos.

        Returns:
            None: Usa asserções para validar status e mensagem.

        Raises:
            AssertionError: Se o status não for 404.
        """
        resposta = self.client.delete(
            "/api/edicoes/11111111-1111-1111-1111-111111111111/",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 404)
        self.assertEqual(resposta.json(), {"error": "Edição não encontrada"})

    def test_deve_retornar_500_quando_persistencia_falhar_no_cadastro(self) -> None:
        """Garante resposta 500 para falha inesperada ao criar edição."""
        payload = {
            "nome": "Edição com falha",
            "periodoEdicao": {"de": "2026-12-01", "ate": "2026-12-31"},
            "periodoInscricoes": {"de": "2026-11-01", "ate": "2026-11-20"},
        }

        with patch(
            "edicoes.views.Edicao.objects.create",
            side_effect=DatabaseError("falha no banco"),
        ):
            resposta = self.client.post(
                "/api/edicoes/",
                data=json.dumps(payload),
                content_type="application/json",
                **self.auth_headers,
            )

        self.assertEqual(resposta.status_code, 500)
        self.assertEqual(resposta.json(), {"error": "falha no banco"})
