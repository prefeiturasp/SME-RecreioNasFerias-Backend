import json
from unittest.mock import Mock, patch
from urllib import error

from django.test import TestCase

from infrastructure.services.usuarios_service import UsuariosService


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

    @patch("infrastructure.services.usuarios_service.request.urlopen")
    def test_deve_retornar_payload_padronizado_quando_login_sucesso(self, urlopen_mock):
        response_auth = Mock()
        response_auth.read.return_value = json.dumps(
            {
                "usuarioId": "5b2b9b98-7692-e211-b1fe-782bcb3d2d76",
                "status": 1,
                "nome": "VANIA FERREIRA DA SILVA CANEKI",
                "codigoRf": "8080640",
            }
        ).encode("utf-8")
        response_dados = Mock()
        response_dados.read.return_value = json.dumps(
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
            }
        ).encode("utf-8")

        cm_auth = Mock()
        cm_auth.__enter__ = Mock(return_value=response_auth)
        cm_auth.__exit__ = Mock(return_value=False)
        cm_dados = Mock()
        cm_dados.__enter__ = Mock(return_value=response_dados)
        cm_dados.__exit__ = Mock(return_value=False)
        urlopen_mock.side_effect = [cm_auth, cm_dados]
        service = UsuariosService(base_url="https://auth.example.com", api_eol_key="dummy")

        payload = service.autenticar("1234567", "123456")

        self.assertEqual(payload["rf"], "8080640")
        self.assertEqual(payload["cpf"], "22712612876")
        self.assertEqual(payload["email"], "vania.montefusco@sme.prefeitura.sp.gov.br")
        self.assertEqual(payload["nome"], "VANIA FERREIRA DA SILVA CANEKI")
        self.assertEqual(payload["inexistenteEol"], False)
        self.assertEqual(payload["cargos"][0]["descricaoCargo"], "ASSISTENTE TECNICO DE EDUCACAO I")
        self.assertEqual(payload["cargo"], "ASSISTENTE TECNICO DE EDUCACAO I")

    @patch("infrastructure.services.usuarios_service.request.urlopen")
    def test_deve_preencher_descricao_cargo_a_partir_de_nome_cargo(self, urlopen_mock):
        response_auth = Mock()
        response_auth.read.return_value = json.dumps(
            {
                "usuarioId": "5b2b9b98-7692-e211-b1fe-782bcb3d2d76",
                "status": 1,
                "nome": "USUARIO",
                "codigoRf": "8080640",
            }
        ).encode("utf-8")
        response_dados = Mock()
        response_dados.read.return_value = json.dumps(
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
            }
        ).encode("utf-8")

        cm_auth = Mock()
        cm_auth.__enter__ = Mock(return_value=response_auth)
        cm_auth.__exit__ = Mock(return_value=False)
        cm_dados = Mock()
        cm_dados.__enter__ = Mock(return_value=response_dados)
        cm_dados.__exit__ = Mock(return_value=False)
        urlopen_mock.side_effect = [cm_auth, cm_dados]
        service = UsuariosService(base_url="https://auth.example.com", api_eol_key="dummy")

        payload = service.autenticar("1234567", "123456")

        self.assertEqual(payload["cargos"][0]["descricaoCargo"], "ASSESSOR I")
        self.assertEqual(payload["cargo"], "ASSESSOR I")
        self.assertEqual(payload["contexto"], "")
        self.assertEqual(payload["permissoes"], [])

    @patch("infrastructure.services.usuarios_service.request.urlopen")
    def test_deve_tratar_401_como_credenciais_invalidas(self, urlopen_mock):
        urlopen_mock.side_effect = error.HTTPError(
            url="https://auth.example.com/api/v1/autenticacao",
            code=401,
            msg="unauthorized",
            hdrs=None,
            fp=None,
        )
        service = UsuariosService(base_url="https://auth.example.com", api_eol_key="dummy")

        with self.assertRaisesMessage(ValueError, "Credenciais inválidas"):
            service.autenticar("1234567", "errada")

    @patch("infrastructure.services.usuarios_service.request.urlopen")
    def test_deve_tratar_404_do_dados_sigpae_como_nao_autorizado(self, urlopen_mock):
        response_auth = Mock()
        response_auth.read.return_value = json.dumps(
            {
                "usuarioId": "5b2b9b98-7692-e211-b1fe-782bcb3d2d76",
                "status": 1,
                "nome": "VANIA FERREIRA DA SILVA CANEKI",
                "codigoRf": "8080640",
            }
        ).encode("utf-8")
        cm_auth = Mock()
        cm_auth.__enter__ = Mock(return_value=response_auth)
        cm_auth.__exit__ = Mock(return_value=False)
        erro_dados = error.HTTPError(
            url="https://auth.example.com/api/funcionarios/DadosSigpae/8080640",
            code=404,
            msg="not found",
            hdrs=None,
            fp=None,
        )
        urlopen_mock.side_effect = [cm_auth, erro_dados]
        service = UsuariosService(base_url="https://auth.example.com", api_eol_key="dummy")

        with self.assertRaisesMessage(ValueError, "Usuário não autorizado"):
            service.autenticar("1234567", "123456")
