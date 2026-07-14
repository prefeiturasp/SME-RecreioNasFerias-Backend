"""Testes dos endpoints HTTP de polos parceiros."""

import json
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import DatabaseError
from django.test import TestCase

from polos.models import (
    GESTAO_PARCEIRA,
    Polo,
    STATUS_ATIVO,
    STATUS_INATIVO,
    TIPO_POLO_OFICIAL,
    TIPO_POLO_PENDENTE,
)
from usuarios.auth_tokens import gerar_token_acesso


class PolosViewTests(TestCase):
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

    def _criar_polo(self, **sobrescrever: object) -> Polo:
        """Persistir um polo parceiro válido diretamente no banco.

        Args:
            **sobrescrever: Campos do modelo a substituir no base.

        Returns:
            Polo: Instância salva no banco.
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
        return Polo.objects.create(**dados)

    def _serializar_polo(self, polo: Polo) -> dict[str, object]:
        """Montar representação JSON esperada de um polo parceiro.

        Args:
            polo (Polo): Instância persistida no banco.

        Returns:
            dict[str, object]: Payload JSON esperado nas respostas da API.
        """
        return {
            "id": str(polo.id),
            "tipo": polo.tipo,
            "gestao": polo.gestao,
            "codigoEol": polo.codigo_eol,
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
            "nomeEdicao": polo.nome_edicao,
            "status": polo.status,
            "observacoesGerais": polo.observacoes_gerais,
        }

    def test_deve_retornar_401_quando_nao_autenticado(self) -> None:
        """Garante que o endpoint exige autenticação."""
        resposta = self.client.get("/api/polos/")

        self.assertIn(resposta.status_code, (401, 403))
        self.assertIn("detail", resposta.json())

    def test_deve_listar_polos_cadastrados(self) -> None:
        """Garante que GET /api/polos/ retorna os registros persistidos."""
        polo = self._criar_polo()

        resposta = self.client.get("/api/polos/", **self.auth_headers)

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

    def test_deve_paginar_listagem_de_polos(self) -> None:
        """Garante paginação da listagem via parâmetros ``page`` e ``pageSize``."""
        for indice in range(1, 16):
            self._criar_polo(nome_polo=f"Polo {indice:02d}")

        resposta = self.client.get(
            "/api/polos/?page=2&pageSize=5",
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
            "/api/polos/?page=0&pageSize=abc",
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
            "/api/polos/?pageSize=500",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json()["pageSize"], 100)

    def test_deve_filtrar_listagem_por_dre(self) -> None:
        """Garante filtro exato por DRE na listagem paginada."""
        polo = self._criar_polo(dre="DRE Butantã")
        self._criar_polo(nome_polo="Polo Outra DRE", dre="DRE Freguesia")

        resposta = self.client.get(
            "/api/polos/?dre=DRE%20Butant%C3%A3",
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
            "/api/polos/?tipoUe=EMEF",
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
            "/api/polos/?nomePoloOuOsc=Centro",
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
            "/api/polos/?nomePoloOuOsc=Esperan%C3%A7a",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 200)
        corpo = resposta.json()
        self.assertEqual(corpo["total"], 1)
        self.assertEqual(corpo["results"][0]["id"], str(polo.id))

    def test_deve_filtrar_e_paginar_listagem_de_polos(self) -> None:
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
            "/api/polos/?dre=DRE%20Butant%C3%A3&page=2&pageSize=2",
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
            "/api/polos/?dre=&tipoUe=&nomePoloOuOsc=",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 200)
        corpo = resposta.json()
        self.assertEqual(corpo["total"], 1)
        self.assertEqual(corpo["results"][0]["id"], str(polo.id))

    def test_deve_retornar_400_para_payload_json_invalido_no_cadastro(self) -> None:
        """Garante erro quando o corpo do POST não for JSON válido."""
        resposta = self.client.post(
            "/api/polos/",
            data="{nomePolo:}",
            content_type="application/json",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(resposta.json(), {"error": "Payload JSON inválido"})

    def test_deve_cadastrar_polo_com_sucesso(self) -> None:
        """Garante criação de polo parceiro válido via POST /api/polos/."""
        payload = self._payload_valido()

        resposta = self.client.post(
            "/api/polos/",
            data=json.dumps(payload),
            content_type="application/json",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 201)
        self.assertEqual(resposta.json()["nomePolo"], "Polo Centro")
        self.assertEqual(resposta.json()["tipo"], TIPO_POLO_PENDENTE)
        self.assertEqual(resposta.json()["gestao"], GESTAO_PARCEIRA)
        self.assertEqual(resposta.json()["status"], STATUS_ATIVO)
        self.assertTrue(Polo.objects.filter(nome_polo="Polo Centro").exists())

    def test_deve_ignorar_status_informado_no_cadastro(self) -> None:
        """Garante que o cadastro persista o polo sempre com status ativo."""
        payload = self._payload_valido(status="inativo")

        resposta = self.client.post(
            "/api/polos/",
            data=json.dumps(payload),
            content_type="application/json",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 201)
        self.assertEqual(resposta.json()["status"], STATUS_ATIVO)

        polo = Polo.objects.get(nome_polo="Polo Centro")
        self.assertEqual(polo.status, STATUS_ATIVO)

    def test_deve_gravar_gestao_parceira_no_cadastro(self) -> None:
        """Garante que o cadastro manual persista gestão Parceira."""
        payload = self._payload_valido(gestao="Direta")

        resposta = self.client.post(
            "/api/polos/",
            data=json.dumps(payload),
            content_type="application/json",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 201)
        self.assertEqual(resposta.json()["gestao"], GESTAO_PARCEIRA)

        polo = Polo.objects.get(nome_polo="Polo Centro")
        self.assertEqual(polo.gestao, GESTAO_PARCEIRA)

    def test_deve_atualizar_status_do_polo(self) -> None:
        """Garante alteração do status via PUT /api/polos/<uuid>/."""
        polo = self._criar_polo()

        resposta = self.client.put(
            f"/api/polos/{polo.id}/",
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
            f"/api/polos/{polo.id}/",
            data=json.dumps({"status": "suspenso"}),
            content_type="application/json",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(
            resposta.json(),
            {"error": "Erro: o status deve ser ativo ou inativo"},
        )

    def test_deve_cadastrar_polo_com_observacoes(self) -> None:
        """Garante persistência de observações gerais informadas no cadastro."""
        payload = self._payload_valido(observacoesGerais="Polo com boa estrutura")

        resposta = self.client.post(
            "/api/polos/",
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
            "/api/polos/",
            data=json.dumps(payload),
            content_type="application/json",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(
            resposta.json(),
            {"error": "Erro: já existe polo com o nome cadastrado"},
        )

    def test_deve_buscar_polo_por_id(self) -> None:
        """Garante consulta de polo via ``GET /api/polos/<uuid>/``."""
        polo = self._criar_polo()

        resposta = self.client.get(
            f"/api/polos/{polo.id}/",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json(), self._serializar_polo(polo))

    def test_deve_retornar_401_quando_buscar_polo_sem_autenticacao(self) -> None:
        """Garante que a consulta por ID exige autenticação."""
        polo = self._criar_polo()

        resposta = self.client.get(f"/api/polos/{polo.id}/")

        self.assertIn(resposta.status_code, (401, 403))
        self.assertIn("detail", resposta.json())

    def test_deve_retornar_404_quando_buscar_polo_inexistente(self) -> None:
        """Garante 404 ao consultar UUID inexistente."""
        resposta = self.client.get(
            "/api/polos/11111111-1111-1111-1111-111111111111/",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 404)
        self.assertEqual(resposta.json(), {"error": "Polo não encontrado"})

    def test_deve_atualizar_polo_com_sucesso(self) -> None:
        """Garante atualização parcial via ``PUT /api/polos/<uuid>/``."""
        polo = self._criar_polo()

        resposta = self.client.put(
            f"/api/polos/{polo.id}/",
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
            f"/api/polos/{polo.id}/",
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
            f"/api/polos/{polo.id}/",
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
            f"/api/polos/{polo.id}/",
            data=json.dumps({"nomePolo": "Polo Original"}),
            content_type="application/json",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(
            resposta.json(),
            {"error": "Erro: já existe polo com o nome cadastrado"},
        )

    def test_deve_retornar_404_quando_atualizar_polo_inexistente(self) -> None:
        """Garante 404 ao atualizar UUID inexistente."""
        resposta = self.client.put(
            "/api/polos/11111111-1111-1111-1111-111111111111/",
            data=json.dumps({"nomeGestor": "Gestor Inexistente"}),
            content_type="application/json",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 404)
        self.assertEqual(resposta.json(), {"error": "Polo não encontrado"})

    def test_deve_deletar_polo_com_sucesso(self) -> None:
        """Garante exclusão via ``DELETE /api/polos/<uuid>/``."""
        polo = self._criar_polo()

        resposta = self.client.delete(
            f"/api/polos/{polo.id}/",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 204)
        self.assertFalse(Polo.objects.filter(pk=polo.id).exists())

    def test_deve_retornar_404_quando_deletar_polo_inexistente(self) -> None:
        """Garante 404 ao excluir UUID inexistente."""
        resposta = self.client.delete(
            "/api/polos/11111111-1111-1111-1111-111111111111/",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 404)
        self.assertEqual(resposta.json(), {"error": "Polo não encontrado"})

    def test_deve_retornar_500_quando_persistencia_falhar_no_cadastro(self) -> None:
        """Garante resposta 500 para falha inesperada ao criar polo parceiro."""
        payload = self._payload_valido(nomePolo="Polo Falha Persistência")

        with patch(
            "polos.views.Polo.objects.create",
            side_effect=DatabaseError("falha no banco"),
        ):
            resposta = self.client.post(
                "/api/polos/",
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
            "polos.models.Polo.save",
            side_effect=DatabaseError("falha no banco"),
        ):
            resposta = self.client.put(
                f"/api/polos/{polo.id}/",
                data=json.dumps({"nomeGestor": "Gestor Atualizado"}),
                content_type="application/json",
                **self.auth_headers,
            )

        self.assertEqual(resposta.status_code, 500)
        self.assertEqual(resposta.json(), {"error": "falha no banco"})

    def test_deve_sincronizar_unidades_diretas_da_integracao(self) -> None:
        """Garante GET /api/polos/unidades-diretas/ retorna resultado da sync."""
        from polos.models import GESTAO_DIRETA
        from polos.sincronizacao import ResultadoSincronizacaoUnidadesDiretas

        polo = Polo.objects.create(
            gestao=GESTAO_DIRETA,
            codigo_eol="019242",
            nome_polo="EMEI TESTE",
            dre="DRE TESTE",
            tipo_ue="EMEI",
            quantidade_maxima_alunos=1,
        )

        resultado = ResultadoSincronizacaoUnidadesDiretas(
            total_consultados=3,
            total_novos=1,
            total_ja_existentes=2,
            polos_criados=[polo],
        )

        with patch(
            "polos.views.sincronizar_unidades_diretas",
            return_value=resultado,
        ) as mock_sync:
            resposta = self.client.get(
                "/api/polos/unidades-diretas/?limite=5",
                **self.auth_headers,
            )

        self.assertEqual(resposta.status_code, 200)
        corpo = resposta.json()
        self.assertEqual(corpo["totalConsultados"], 3)
        self.assertEqual(corpo["totalNovos"], 1)
        self.assertEqual(corpo["totalJaExistentes"], 2)
        self.assertEqual(len(corpo["unidadesNovas"]), 1)
        self.assertEqual(corpo["unidadesNovas"][0]["codigoEol"], "019242")
        self.assertEqual(corpo["unidadesNovas"][0]["gestao"], GESTAO_DIRETA)
        self.assertTrue(corpo["executada"])
        self.assertIsNone(corpo["motivoIgnorada"])
        mock_sync.assert_called_once_with(limite=5, forcar=False)

    def test_deve_rejeitar_limite_invalido_em_unidades_diretas(self) -> None:
        """Garante HTTP 400 quando ``limite`` não é positivo."""
        resposta = self.client.get(
            "/api/polos/unidades-diretas/?limite=0",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(resposta.json(), {"error": "Parâmetro limite inválido"})

    def test_deve_retornar_503_quando_integracao_indisponivel(self) -> None:
        """Garante HTTP 503 quando a SME Integração falha."""
        from infrastructure.services.escolas_integracao_service import (
            EscolasIntegracaoIndisponivelError,
        )

        with patch(
            "polos.views.sincronizar_unidades_diretas",
            side_effect=EscolasIntegracaoIndisponivelError("SME indisponível"),
        ):
            resposta = self.client.get(
                "/api/polos/unidades-diretas/",
                **self.auth_headers,
            )

        self.assertEqual(resposta.status_code, 503)
        self.assertEqual(resposta.json(), {"error": "SME indisponível"})

    def test_deve_filtrar_listagem_por_gestao(self) -> None:
        """Garante filtro exato por gestão na listagem paginada."""
        from polos.models import GESTAO_DIRETA

        polo = self._criar_polo(
            nome_polo="Polo Direta",
            gestao=GESTAO_DIRETA,
            codigo_eol="019001",
        )
        self._criar_polo(nome_polo="Polo Parceira")

        resposta = self.client.get(
            "/api/polos/?gestao=Direta",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 200)
        corpo = resposta.json()
        self.assertEqual(corpo["total"], 1)
        self.assertEqual(corpo["results"][0]["id"], str(polo.id))

    def test_deve_filtrar_listagem_por_gestao_parceira(self) -> None:
        """Garante filtro por gestão Parceira na listagem paginada."""
        from polos.models import GESTAO_DIRETA

        self._criar_polo(
            nome_polo="Polo Direta Filtro",
            gestao=GESTAO_DIRETA,
            codigo_eol="019002",
        )
        polo_parceira = self._criar_polo(nome_polo="Polo Parceira Filtro")

        resposta = self.client.get(
            "/api/polos/?gestao=Parceira",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 200)
        corpo = resposta.json()
        self.assertEqual(corpo["total"], 1)
        self.assertEqual(corpo["results"][0]["id"], str(polo_parceira.id))
        self.assertEqual(corpo["results"][0]["gestao"], GESTAO_PARCEIRA)

    def test_deve_filtrar_listagem_por_gestao_case_insensitive(self) -> None:
        """Garante que o filtro de gestão aceite o valor em minúsculas."""
        from polos.models import GESTAO_DIRETA

        self._criar_polo(
            nome_polo="Polo Direta Case",
            gestao=GESTAO_DIRETA,
            codigo_eol="019003",
        )
        polo_parceira = self._criar_polo(nome_polo="Polo Parceira Case")

        resposta = self.client.get(
            "/api/polos/?gestao=parceira",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 200)
        corpo = resposta.json()
        self.assertEqual(corpo["total"], 1)
        self.assertEqual(corpo["results"][0]["id"], str(polo_parceira.id))

    def test_deve_filtrar_listagem_por_nome_edicao(self) -> None:
        """Garante filtro exato por nome da edição na listagem paginada."""
        polo = self._criar_polo(
            nome_polo="Polo Com Edicao",
            nome_edicao="Janeiro 2025",
        )
        self._criar_polo(nome_polo="Polo Sem Edicao", nome_edicao="-")

        resposta = self.client.get(
            "/api/polos/?nomeEdicao=Janeiro%202025",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 200)
        corpo = resposta.json()
        self.assertEqual(corpo["total"], 1)
        self.assertEqual(corpo["results"][0]["id"], str(polo.id))
        self.assertEqual(corpo["results"][0]["nomeEdicao"], "Janeiro 2025")

    def test_deve_filtrar_listagem_por_tipo_polo(self) -> None:
        """Garante filtro exato por tipo na listagem paginada."""
        polo = self._criar_polo(
            nome_polo="Polo Oficial Filtro",
            tipo=TIPO_POLO_OFICIAL,
        )
        self._criar_polo(nome_polo="Polo Pendente Filtro")

        resposta = self.client.get(
            "/api/polos/?tipoPolo=Polo%20oficial",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 200)
        corpo = resposta.json()
        self.assertEqual(corpo["total"], 1)
        self.assertEqual(corpo["results"][0]["id"], str(polo.id))
        self.assertEqual(corpo["results"][0]["tipo"], TIPO_POLO_OFICIAL)

    def test_deve_filtrar_listagem_por_nome_ue_ou_codigo_eol(self) -> None:
        """Garante busca parcial por código EOL via ``nomeUeOuCodigoEol``."""
        from polos.models import GESTAO_DIRETA

        polo = self._criar_polo(
            nome_polo="Polo EOL",
            gestao=GESTAO_DIRETA,
            codigo_eol="019777",
        )
        self._criar_polo(nome_polo="Polo Outro")

        resposta = self.client.get(
            "/api/polos/?nomeUeOuCodigoEol=019777",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 200)
        corpo = resposta.json()
        self.assertEqual(corpo["total"], 1)
        self.assertEqual(corpo["results"][0]["id"], str(polo.id))

    def test_deve_listar_opcoes_de_filtro_a_partir_do_banco(self) -> None:
        """Garante opções de filtro derivadas dos valores persistidos."""
        from polos.models import GESTAO_DIRETA

        self._criar_polo(
            nome_polo="Polo Direta Filtro",
            gestao=GESTAO_DIRETA,
            codigo_eol="019888",
            dre="DIRETORIA REGIONAL DE EDUCACAO PENHA",
            tipo_ue="CEI DIRET",
        )
        self._criar_polo(
            nome_polo="Polo Parceira Filtro",
            dre="DIRETORIA REGIONAL DE EDUCACAO BUTANTA",
            tipo_ue="EMEF",
        )

        resposta = self.client.get(
            "/api/polos/opcoes-filtro/",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 200)
        corpo = resposta.json()
        self.assertIn("DIRETORIA REGIONAL DE EDUCACAO PENHA", corpo["dres"])
        self.assertIn("DIRETORIA REGIONAL DE EDUCACAO BUTANTA", corpo["dres"])
        self.assertIn("CEI DIRET", corpo["tiposUe"])
        self.assertIn("EMEF", corpo["tiposUe"])
        self.assertIn("Direta", corpo["gestoes"])
        self.assertIn("Parceira", corpo["gestoes"])
        self.assertIn("-", corpo["nomesEdicao"])
        self.assertEqual(
            corpo["tiposPolo"],
            ["Pendente", "Polo oficial", "Polo reserva"],
        )

    def test_deve_atualizar_nome_edicao_em_lote(self) -> None:
        """Garante alteração de nome da edição para um ou mais polos."""
        polo_a = self._criar_polo(nome_polo="Polo Edicao A")
        polo_b = self._criar_polo(nome_polo="Polo Edicao B")

        resposta = self.client.patch(
            "/api/polos/atualizacao-lote/",
            data=json.dumps(
                {
                    "ids": [str(polo_a.id), str(polo_b.id)],
                    "nomeEdicao": "Janeiro 2026",
                },
            ),
            content_type="application/json",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 200)
        corpo = resposta.json()
        self.assertEqual(corpo["totalAtualizados"], 2)
        polo_a.refresh_from_db()
        polo_b.refresh_from_db()
        self.assertEqual(polo_a.nome_edicao, "Janeiro 2026")
        self.assertEqual(polo_b.nome_edicao, "Janeiro 2026")

    def test_deve_atualizar_tipo_em_lote(self) -> None:
        """Garante alteração de tipo para um ou mais polos."""
        polo_a = self._criar_polo(nome_polo="Polo Tipo A")
        polo_b = self._criar_polo(nome_polo="Polo Tipo B")

        resposta = self.client.patch(
            "/api/polos/atualizacao-lote/",
            data=json.dumps(
                {
                    "ids": [str(polo_a.id), str(polo_b.id)],
                    "tipo": TIPO_POLO_OFICIAL,
                },
            ),
            content_type="application/json",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 200)
        corpo = resposta.json()
        self.assertEqual(corpo["totalAtualizados"], 2)
        polo_a.refresh_from_db()
        polo_b.refresh_from_db()
        self.assertEqual(polo_a.tipo, TIPO_POLO_OFICIAL)
        self.assertEqual(polo_b.tipo, TIPO_POLO_OFICIAL)

    def test_deve_rejeitar_atualizacao_lote_com_json_invalido(self) -> None:
        """Garante 400 quando o corpo da atualização em lote não é JSON."""
        resposta = self.client.patch(
            "/api/polos/atualizacao-lote/",
            data="{invalido",
            content_type="application/json",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(resposta.json(), {"error": "Payload JSON inválido"})

    def test_deve_rejeitar_atualizacao_lote_sem_ids(self) -> None:
        """Garante 400 quando a lista de identificadores estiver vazia."""
        resposta = self.client.patch(
            "/api/polos/atualizacao-lote/",
            data=json.dumps({"ids": [], "tipo": TIPO_POLO_OFICIAL}),
            content_type="application/json",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(
            resposta.json(),
            {"error": "Informe ao menos um identificador de polo"},
        )

    def test_deve_rejeitar_atualizacao_lote_sem_campos_de_atualizacao(self) -> None:
        """Garante 400 quando não há ``nomeEdicao`` nem ``tipo`` no payload."""
        polo = self._criar_polo(nome_polo="Polo Sem Campos Lote")

        resposta = self.client.patch(
            "/api/polos/atualizacao-lote/",
            data=json.dumps({"ids": [str(polo.id)]}),
            content_type="application/json",
            **self.auth_headers,
        )

        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(
            resposta.json(),
            {"error": "Informe nomeEdicao e/ou tipo para atualização"},
        )
