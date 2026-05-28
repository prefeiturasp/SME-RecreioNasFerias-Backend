import json
from unittest.mock import Mock, patch

from django.test import TestCase
from requests.exceptions import ConnectionError, ReadTimeout

from application.exceptions import (
    CoressoIndisponivelError,
    CoressoRespostaError,
    ERRO_CORESSO_INDISPONIVEL,
    MENSAGEM_PADRAO_CREDENCIAIS_INCORRETAS,
    MENSAGEM_PADRAO_RF_SEM_DADOS,
)
from infrastructure.services.usuarios_service import UsuariosService


def _resposta_json(status_code: int, payload: dict | str) -> Mock:
    response = Mock()
    response.status_code = status_code
    response.ok = 200 <= status_code < 300
    if isinstance(payload, dict):
        response.json.return_value = payload
        response.text = json.dumps(payload, ensure_ascii=False)
    else:
        response.json.return_value = {}
        response.text = payload
    return response


class UsuariosServiceTests(TestCase):
    """Testes do servico de autenticacao externo (CoreSSO)."""

    def test_deve_falhar_quando_base_url_nao_configurada(self):
        service = UsuariosService(base_url="", api_eol_key="dummy")

        with self.assertRaisesMessage(ValueError, "AUTH_API_BASE_URL não configurada"):
            service.autenticar("1234567", "123456")

    def test_deve_falhar_quando_api_key_nao_configurada(self):
        service = UsuariosService(base_url="https://auth.example.com", api_eol_key="")

        with self.assertRaisesMessage(ValueError, "AUTH_API_EOL_KEY não configurada"):
            service.autenticar("1234567", "123456")

    @patch("infrastructure.services.usuarios_service.requests.request")
    def test_deve_retornar_payload_padronizado_quando_login_sucesso(self, request_mock):
        request_mock.side_effect = [
            _resposta_json(
                200,
                {
                    "usuarioId": "5b2b9b98-7692-e211-b1fe-782bcb3d2d76",
                    "status": 1,
                    "nome": "VANIA FERREIRA DA SILVA CANEKI",
                    "codigoRf": "8080640",
                },
            ),
            _resposta_json(
                200,
                {
                    "rf": "8080640",
                    "cpf": "22712612876",
                    "email": "vania.montefusco@sme.prefeitura.sp.gov.br",
                    "cargos": [
                        {
                            "codigoCargo": 2640,
                            "descricaoCargo": "ASSISTENTE TECNICO DE EDUCACAO I",
                            "codigoUnidade": "121000",
                            "descricaoUnidade": "COORDENADORIA DOS CENTROS EDUCACIONAIS UNIFICADOS - COCEU",
                            "codigoDre": "121000",
                            "contratoExterno": False,
                        }
                    ],
                    "nome": "VANIA FERREIRA DA SILVA CANEKI",
                    "inexistenteEol": False,
                },
            ),
        ]
        service = UsuariosService(base_url="https://auth.example.com", api_eol_key="dummy")

        payload = service.autenticar("1234567", "123456")

        self.assertEqual(payload["rf"], "8080640")
        self.assertEqual(payload["cpf"], "22712612876")
        self.assertEqual(payload["email"], "vania.montefusco@sme.prefeitura.sp.gov.br")
        self.assertEqual(payload["nome"], "VANIA FERREIRA DA SILVA CANEKI")
        self.assertEqual(payload["inexistenteEol"], False)
        self.assertEqual(payload["cargos"][0]["descricaoCargo"], "ASSISTENTE TECNICO DE EDUCACAO I")
        self.assertEqual(payload["cargo"], "ASSISTENTE TECNICO DE EDUCACAO I")

    @patch("infrastructure.services.usuarios_service.requests.request")
    def test_deve_propagar_mensagem_do_coresso_em_401(self, request_mock):
        request_mock.return_value = _resposta_json(
            401, {"message": "Usuário ou senha incorretos."}
        )
        service = UsuariosService(base_url="https://auth.example.com", api_eol_key="dummy")

        with self.assertRaises(CoressoRespostaError) as ctx:
            service.autenticar("1234567", "errada")

        self.assertEqual(str(ctx.exception), "Usuário ou senha incorretos.")
        self.assertEqual(ctx.exception.status_http, 401)

    @patch("infrastructure.services.usuarios_service.requests.request")
    def test_deve_usar_mensagem_padrao_em_401_sem_corpo(self, request_mock):
        request_mock.return_value = _resposta_json(401, {})
        service = UsuariosService(base_url="https://auth.example.com", api_eol_key="dummy")

        with self.assertRaisesMessage(
            CoressoRespostaError, MENSAGEM_PADRAO_CREDENCIAIS_INCORRETAS
        ):
            service.autenticar("1234567", "errada")

    @patch("infrastructure.services.usuarios_service.requests.request")
    def test_deve_propagar_mensagem_do_coresso_em_dados_sigpae(self, request_mock):
        request_mock.side_effect = [
            _resposta_json(
                200,
                {
                    "usuarioId": "5b2b9b98-7692-e211-b1fe-782bcb3d2d76",
                    "status": 1,
                    "nome": "VANIA",
                    "codigoRf": "8080640",
                },
            ),
            _resposta_json(
                404,
                "Sem informações na base de dados para o Código Rf informado",
            ),
        ]
        service = UsuariosService(base_url="https://auth.example.com", api_eol_key="dummy")

        with self.assertRaises(CoressoRespostaError) as ctx:
            service.autenticar("1234567", "123456")

        self.assertEqual(
            str(ctx.exception),
            "Sem informações na base de dados para o Código Rf informado",
        )
        self.assertEqual(ctx.exception.status_http, 404)

    @patch("infrastructure.services.usuarios_service.requests.request")
    def test_deve_usar_mensagem_padrao_em_404_sem_corpo(self, request_mock):
        request_mock.side_effect = [
            _resposta_json(
                200,
                {
                    "usuarioId": "5b2b9b98-7692-e211-b1fe-782bcb3d2d76",
                    "status": 1,
                    "nome": "VANIA",
                    "codigoRf": "8080640",
                },
            ),
            _resposta_json(404, {}),
        ]
        service = UsuariosService(base_url="https://auth.example.com", api_eol_key="dummy")

        with self.assertRaisesMessage(CoressoRespostaError, MENSAGEM_PADRAO_RF_SEM_DADOS):
            service.autenticar("1234567", "123456")

    @patch("infrastructure.services.usuarios_service.requests.request")
    def test_deve_preencher_descricao_cargo_a_partir_de_nome_cargo(self, request_mock):
        request_mock.side_effect = [
            _resposta_json(
                200,
                {
                    "usuarioId": "5b2b9b98-7692-e211-b1fe-782bcb3d2d76",
                    "status": 1,
                    "nome": "USUARIO",
                    "codigoRf": "8080640",
                },
            ),
            _resposta_json(
                200,
                {
                    "rf": "8080640",
                    "cargos": [
                        {
                            "codigoCargo": 71,
                            "nomeCargo": "ASSESSOR I",
                            "codigoUnidade": "121000",
                        }
                    ],
                    "nome": "USUARIO",
                    "inexistenteEol": False,
                },
            ),
        ]
        service = UsuariosService(base_url="https://auth.example.com", api_eol_key="dummy")

        payload = service.autenticar("1234567", "123456")

        self.assertEqual(payload["cargos"][0]["descricaoCargo"], "ASSESSOR I")
        self.assertEqual(payload["cargo"], "ASSESSOR I")

    @patch("infrastructure.services.usuarios_service.requests.request")
    def test_deve_tratar_http_5xx_como_coresso_indisponivel(self, request_mock):
        request_mock.return_value = _resposta_json(503, {"message": "Service Unavailable"})
        service = UsuariosService(base_url="https://auth.example.com", api_eol_key="dummy")

        with self.assertRaisesMessage(CoressoIndisponivelError, ERRO_CORESSO_INDISPONIVEL):
            service.autenticar("1234567", "123456")

    @patch("infrastructure.services.usuarios_service.requests.request")
    def test_deve_tratar_timeout_como_coresso_indisponivel(self, request_mock):
        request_mock.side_effect = ReadTimeout("read timed out")
        service = UsuariosService(base_url="https://auth.example.com", api_eol_key="dummy")

        with self.assertRaisesMessage(CoressoIndisponivelError, ERRO_CORESSO_INDISPONIVEL):
            service.autenticar("1234567", "123456")

    @patch("infrastructure.services.usuarios_service.requests.request")
    def test_deve_tratar_erro_de_conexao_como_coresso_indisponivel(self, request_mock):
        request_mock.side_effect = ConnectionError("Connection refused")
        service = UsuariosService(base_url="https://auth.example.com", api_eol_key="dummy")

        with self.assertRaisesMessage(CoressoIndisponivelError, ERRO_CORESSO_INDISPONIVEL):
            service.autenticar("1234567", "123456")
