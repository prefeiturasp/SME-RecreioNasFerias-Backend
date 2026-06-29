"""Testes dos endpoints HTTP de polos parceiros."""

import json
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import DatabaseError
from django.test import TestCase

from polos_parceiros.models import (
    PoloParceiro,
    STATUS_ATIVO,
    STATUS_INATIVO,
    TIPO_POLO_PARCEIRO,
)
from usuarios.auth_tokens import gerar_token_acesso


class PolosParceirosViewTests(TestCase):
    """Valida fluxo HTTP de listagem, consulta, criação, atualização e exclusão."""

    def setUp(self) -> None:
        """Configura um usuário autenticado para chamadas aos endpoints protegidos."""
        Usuario = get_user_model()
        self.usuario = Usuario.objects.create(
            rf="7654321",
            email="polo@test.local",
            is_active=True,
        )
        self.usuario.set_unusable_password()
        self.usuario.save()
        token = gerar_token_acesso(self.usuario)
        self.auth_headers = {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    def _payload_valido(self, **sobrescrever: object) -> dict[str, object]:
        """Montar payload JSON válido para requisições de polo parceiro.

        Args:
            **sobrescrever: Campos do payload a substituir no base.

        Returns:
            dict[str, object]: Payload pronto para serialização JSON.
        """
        payload: dict[str, object] = {
            "nomeOsc": "OSC Parceira Exemplo",
            "nomePolo": "Polo Centro",
            "dre": "DRE Butantã",
            "tipoUe": "EMEF",
            "quantidadeMaximaAlunos": 50,
            "cep": "05508-000",
            "endereco": "Rua Exemplo, 100",
            "nomeGestor": "Maria Silva",
            "emailPolo": "polo@osc.org.br",
            "telefonePolo": "(11) 99999-9999",
        }
        payload.update(sobrescrever)
        return payload

    def _criar_polo(self, **sobrescrever: object) -> PoloParceiro:
        """Persistir um polo parceiro válido diretamente no banco.

        Args:
            **sobrescrever: Campos do modelo a substituir no base.

        Returns:
            PoloParceiro: Instância salva no banco.
        """
        dados: dict[str, object] = {
            "nome_osc": "OSC Parceira Exemplo",
            "nome_polo": "Polo Centro",
            "dre": "DRE Butantã",
            "tipo_ue": "EMEF",
            "quantidade_maxima_alunos": 50,
            "cep": "05508-000",
            "endereco": "Rua Exemplo, 100",
            "nome_gestor": "Maria Silva",
            "email_polo": "polo@osc.org.br",
            "telefone_polo": "(11) 99999-9999",
        }
        dados.update(sobrescrever)
        return PoloParceiro.objects.create(**dados)

    def _serializar_polo(self, polo: PoloParceiro) -> dict[str, object]:
        """Montar representação JSON esperada de um polo parceiro.

        Args:
            polo (PoloParceiro): Instância persistida no banco.

        Returns:
            dict[str, object]: Payload JSON esperado nas respostas da API.
        """
        return {
            "id": str(polo.id),
            "tipo": TIPO_POLO_PARCEIRO,
            "nomeOsc": polo.nome_osc,
            "nomePolo": polo.nome_polo,
            "dre": polo.dre,
            "tipoUe": polo.tipo_ue,
            "quantidadeMaximaAlunos": polo.quantidade_maxima_alunos,
            "cep": polo.cep,
            "endereco": polo.endereco,
            "nomeGestor": polo.nome_gestor,
            "emailPolo": polo.email_polo,
            "telefonePolo": polo.telefone_polo,
            "status": polo.status,
            "observacoesGerais": polo.observacoes_gerais,
        }

    def test_deve_retornar_401_quando_nao_autenticado(self) -> None:
        """Garante que o endpoint exige autenticação."""
        resposta = self.client.get("/api/polos-parceiros/")

        self.assertIn(resposta.status_code, (401, 403))
        self.assertIn("detail", resposta.json())

    def test_deve_listar_polos_parceiros_cadastrados(self) -> None:
        """Garante que GET /api/polos-parceiros/ retorna os registros persistidos."""
        polo = self._criar_polo()

        resposta = self.client.get("/api/polos-parceiros/", **self.auth_headers)

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(
            resposta.json(),
            {
                "results": [self._serializar_polo(polo)],
                "page": 1,
                "pageSize": 10,
                "total": 1,
                "totalPages": 1,
            },
        )

    def test_deve_paginar_listagem_de_polos_parceiros(self) -> None:
        """Garante paginação da listagem via parâmetros ``page`` e ``pageSize``."""
        for indice in range(1, 16):
            self._criar_polo(nome_polo=f"Polo {indice:02d}")

        resposta = self.client.get(
            "/api/polos-parceiros/?page=2&pageSize=5",
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
            "/api/polos-parceiros/?page=0&pageSize=abc",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(
            resposta.json(),
            {"error": "Parâmetros de paginação inválidos"},
        )

    def test_deve_limitar_page_size_maximo_na_listagem(self) -> None:
        """Garante que ``pageSize`` acima do máximo seja limitado automaticamente."""
        self._criar_polo()

        resposta = self.client.get(
            "/api/polos-parceiros/?pageSize=500",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json()["pageSize"], 100)

    def test_deve_filtrar_listagem_por_dre(self) -> None:
        """Garante filtro exato por DRE na listagem paginada."""
        polo = self._criar_polo(dre="DRE Butantã")
        self._criar_polo(nome_polo="Polo Outra DRE", dre="DRE Freguesia")

        resposta = self.client.get(
            "/api/polos-parceiros/?dre=DRE%20Butant%C3%A3",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 200)
        corpo = resposta.json()
        self.assertEqual(corpo["total"], 1)
        self.assertEqual(corpo["results"][0]["id"], str(polo.id))

    def test_deve_filtrar_listagem_por_tipo_ue(self) -> None:
        """Garante filtro exato por tipo de UE na listagem paginada."""
        polo = self._criar_polo(tipo_ue="EMEF")
        self._criar_polo(nome_polo="Polo EMEI", tipo_ue="EMEI")

        resposta = self.client.get(
            "/api/polos-parceiros/?tipoUe=EMEF",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 200)
        corpo = resposta.json()
        self.assertEqual(corpo["total"], 1)
        self.assertEqual(corpo["results"][0]["id"], str(polo.id))

    def test_deve_filtrar_listagem_por_nome_polo_ou_osc_no_nome_do_polo(self) -> None:
        """Garante busca parcial pelo nome do polo via ``nomePoloOuOsc``."""
        polo = self._criar_polo(nome_polo="Polo Recreio Centro")
        self._criar_polo(nome_polo="Polo Recreio Sul")

        resposta = self.client.get(
            "/api/polos-parceiros/?nomePoloOuOsc=Centro",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 200)
        corpo = resposta.json()
        self.assertEqual(corpo["total"], 1)
        self.assertEqual(corpo["results"][0]["id"], str(polo.id))

    def test_deve_filtrar_listagem_por_nome_polo_ou_osc_no_nome_da_osc(self) -> None:
        """Garante busca parcial pelo nome da OSC via ``nomePoloOuOsc``."""
        polo = self._criar_polo(nome_osc="OSC Esperança", nome_polo="Polo Esperança")
        self._criar_polo(nome_osc="OSC Futuro", nome_polo="Polo Futuro")

        resposta = self.client.get(
            "/api/polos-parceiros/?nomePoloOuOsc=Esperan%C3%A7a",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 200)
        corpo = resposta.json()
        self.assertEqual(corpo["total"], 1)
        self.assertEqual(corpo["results"][0]["id"], str(polo.id))

    def test_deve_filtrar_e_paginar_listagem_de_polos_parceiros(self) -> None:
        """Garante que filtros e paginação funcionam em conjunto."""
        for indice in range(1, 7):
            self._criar_polo(
                nome_polo=f"Polo Butantã {indice:02d}",
                dre="DRE Butantã",
            )
        for indice in range(1, 4):
            self._criar_polo(
                nome_polo=f"Polo Freguesia {indice:02d}",
                dre="DRE Freguesia",
            )

        resposta = self.client.get(
            "/api/polos-parceiros/?dre=DRE%20Butant%C3%A3&page=2&pageSize=2",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 200)
        corpo = resposta.json()
        self.assertEqual(len(corpo["results"]), 2)
        self.assertEqual(corpo["page"], 2)
        self.assertEqual(corpo["pageSize"], 2)
        self.assertEqual(corpo["total"], 6)
        self.assertEqual(corpo["totalPages"], 3)

    def test_deve_ignorar_filtros_vazios_na_listagem(self) -> None:
        """Garante que filtros vazios não restrinjam a listagem paginada."""
        polo = self._criar_polo()

        resposta = self.client.get(
            "/api/polos-parceiros/?dre=&tipoUe=&nomePoloOuOsc=",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 200)
        corpo = resposta.json()
        self.assertEqual(corpo["total"], 1)
        self.assertEqual(corpo["results"][0]["id"], str(polo.id))

    def test_deve_retornar_400_para_payload_json_invalido_no_cadastro(self) -> None:
        """Garante erro quando o corpo do POST não for JSON válido."""
        resposta = self.client.post(
            "/api/polos-parceiros/",
            data="{nomePolo:}",
            content_type="application/json",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(resposta.json(), {"error": "Payload JSON inválido"})

    def test_deve_cadastrar_polo_parceiro_com_sucesso(self) -> None:
        """Garante criação de polo parceiro válido via POST /api/polos-parceiros/."""
        payload = self._payload_valido()

        resposta = self.client.post(
            "/api/polos-parceiros/",
            data=json.dumps(payload),
            content_type="application/json",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 201)
        self.assertEqual(resposta.json()["nomePolo"], "Polo Centro")
        self.assertEqual(resposta.json()["tipo"], TIPO_POLO_PARCEIRO)
        self.assertEqual(resposta.json()["status"], STATUS_ATIVO)
        self.assertTrue(PoloParceiro.objects.filter(nome_polo="Polo Centro").exists())

    def test_deve_ignorar_status_informado_no_cadastro(self) -> None:
        """Garante que o cadastro persista o polo sempre com status ativo."""
        payload = self._payload_valido(status="inativo")

        resposta = self.client.post(
            "/api/polos-parceiros/",
            data=json.dumps(payload),
            content_type="application/json",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 201)
        self.assertEqual(resposta.json()["status"], STATUS_ATIVO)

        polo = PoloParceiro.objects.get(nome_polo="Polo Centro")
        self.assertEqual(polo.status, STATUS_ATIVO)

    def test_deve_atualizar_status_do_polo_parceiro(self) -> None:
        """Garante alteração do status via PUT /api/polos-parceiros/<uuid>/."""
        polo = self._criar_polo()

        resposta = self.client.put(
            f"/api/polos-parceiros/{polo.id}/",
            data=json.dumps({"status": STATUS_INATIVO}),
            content_type="application/json",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json()["status"], STATUS_INATIVO)
        polo.refresh_from_db()
        self.assertEqual(polo.status, STATUS_INATIVO)

    def test_deve_retornar_400_para_status_invalido_na_atualizacao(self) -> None:
        """Garante bloqueio de atualização com status fora dos valores permitidos."""
        polo = self._criar_polo(nome_polo="Polo Status Inválido")

        resposta = self.client.put(
            f"/api/polos-parceiros/{polo.id}/",
            data=json.dumps({"status": "suspenso"}),
            content_type="application/json",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(
            resposta.json(),
            {"error": "Erro: o status deve ser ativo ou inativo"},
        )

    def test_deve_cadastrar_polo_parceiro_com_observacoes(self) -> None:
        """Garante persistência de observações gerais informadas no cadastro."""
        payload = self._payload_valido(observacoesGerais="Polo com boa estrutura")

        resposta = self.client.post(
            "/api/polos-parceiros/",
            data=json.dumps(payload),
            content_type="application/json",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 201)
        self.assertEqual(resposta.json()["observacoesGerais"], "Polo com boa estrutura")

    def test_deve_retornar_400_para_nome_polo_duplicado(self) -> None:
        """Garante bloqueio de cadastro com nome de polo já existente."""
        self._criar_polo()
        payload = self._payload_valido(nomePolo="Polo Centro")

        resposta = self.client.post(
            "/api/polos-parceiros/",
            data=json.dumps(payload),
            content_type="application/json",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(
            resposta.json(),
            {"error": "Erro: já existe polo parceiro com o nome cadastrado"},
        )

    def test_deve_buscar_polo_parceiro_por_id(self) -> None:
        """Garante consulta de polo via ``GET /api/polos-parceiros/<uuid>/``."""
        polo = self._criar_polo()

        resposta = self.client.get(
            f"/api/polos-parceiros/{polo.id}/",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json(), self._serializar_polo(polo))

    def test_deve_retornar_401_quando_buscar_polo_sem_autenticacao(self) -> None:
        """Garante que a consulta por ID exige autenticação."""
        polo = self._criar_polo()

        resposta = self.client.get(f"/api/polos-parceiros/{polo.id}/")

        self.assertIn(resposta.status_code, (401, 403))
        self.assertIn("detail", resposta.json())

    def test_deve_retornar_404_quando_buscar_polo_inexistente(self) -> None:
        """Garante 404 ao consultar UUID inexistente."""
        resposta = self.client.get(
            "/api/polos-parceiros/11111111-1111-1111-1111-111111111111/",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 404)
        self.assertEqual(resposta.json(), {"error": "Polo parceiro não encontrado"})

    def test_deve_atualizar_polo_parceiro_com_sucesso(self) -> None:
        """Garante atualização parcial via ``PUT /api/polos-parceiros/<uuid>/``."""
        polo = self._criar_polo()

        resposta = self.client.put(
            f"/api/polos-parceiros/{polo.id}/",
            data=json.dumps({"nomeGestor": "João Santos"}),
            content_type="application/json",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json()["nomeGestor"], "João Santos")
        polo.refresh_from_db()
        self.assertEqual(polo.nome_gestor, "João Santos")

    def test_deve_retornar_400_para_payload_json_invalido_na_atualizacao(self) -> None:
        """Garante erro quando o corpo do PUT não for JSON válido."""
        polo = self._criar_polo()

        resposta = self.client.put(
            f"/api/polos-parceiros/{polo.id}/",
            data="{nomeGestor:}",
            content_type="application/json",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(resposta.json(), {"error": "Payload JSON inválido"})

    def test_deve_retornar_400_quando_atualizar_sem_campos(self) -> None:
        """Garante bloqueio de atualização sem campos no payload."""
        polo = self._criar_polo()

        resposta = self.client.put(
            f"/api/polos-parceiros/{polo.id}/",
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
        """Garante bloqueio de atualização para nome já cadastrado em outro polo."""
        self._criar_polo(nome_polo="Polo Original")
        polo = self._criar_polo(nome_polo="Polo Destino")

        resposta = self.client.put(
            f"/api/polos-parceiros/{polo.id}/",
            data=json.dumps({"nomePolo": "Polo Original"}),
            content_type="application/json",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(
            resposta.json(),
            {"error": "Erro: já existe polo parceiro com o nome cadastrado"},
        )

    def test_deve_retornar_404_quando_atualizar_polo_inexistente(self) -> None:
        """Garante 404 ao atualizar UUID inexistente."""
        resposta = self.client.put(
            "/api/polos-parceiros/11111111-1111-1111-1111-111111111111/",
            data=json.dumps({"nomeGestor": "Gestor Inexistente"}),
            content_type="application/json",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 404)
        self.assertEqual(resposta.json(), {"error": "Polo parceiro não encontrado"})

    def test_deve_deletar_polo_parceiro_com_sucesso(self) -> None:
        """Garante exclusão via ``DELETE /api/polos-parceiros/<uuid>/``."""
        polo = self._criar_polo()

        resposta = self.client.delete(
            f"/api/polos-parceiros/{polo.id}/",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 204)
        self.assertFalse(PoloParceiro.objects.filter(pk=polo.id).exists())

    def test_deve_retornar_404_quando_deletar_polo_inexistente(self) -> None:
        """Garante 404 ao excluir UUID inexistente."""
        resposta = self.client.delete(
            "/api/polos-parceiros/11111111-1111-1111-1111-111111111111/",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 404)
        self.assertEqual(resposta.json(), {"error": "Polo parceiro não encontrado"})

    def test_deve_retornar_500_quando_persistencia_falhar_no_cadastro(self) -> None:
        """Garante resposta 500 para falha inesperada ao criar polo parceiro."""
        payload = self._payload_valido(nomePolo="Polo Falha Persistência")

        with patch(
            "polos_parceiros.views.PoloParceiro.objects.create",
            side_effect=DatabaseError("falha no banco"),
        ):
            resposta = self.client.post(
                "/api/polos-parceiros/",
                data=json.dumps(payload),
                content_type="application/json",
                **self.auth_headers,
            )

        self.assertEqual(resposta.status_code, 500)
        self.assertEqual(resposta.json(), {"error": "falha no banco"})

    def test_deve_retornar_500_quando_persistencia_falhar_na_atualizacao(self) -> None:
        """Garante resposta 500 para falha inesperada ao atualizar polo parceiro."""
        polo = self._criar_polo(nome_polo="Polo Falha Atualização")

        with patch(
            "polos_parceiros.models.PoloParceiro.save",
            side_effect=DatabaseError("falha no banco"),
        ):
            resposta = self.client.put(
                f"/api/polos-parceiros/{polo.id}/",
                data=json.dumps({"nomeGestor": "Gestor Atualizado"}),
                content_type="application/json",
                **self.auth_headers,
            )

        self.assertEqual(resposta.status_code, 500)
        self.assertEqual(resposta.json(), {"error": "falha no banco"})
