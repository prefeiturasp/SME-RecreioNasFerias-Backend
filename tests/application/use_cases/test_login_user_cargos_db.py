"""Integração do login com verificação real de cargo no banco."""

from unittest.mock import Mock

from django.test import TestCase

from application.dtos.login_input_dto import LoginInputDto
from application.exceptions import CargoNaoAutorizadoError
from application.services.usuarios_rbac import UsuariosRbac
from application.services.usuarios_validador import UsuariosValidador
from application.use_cases.login_user import LoginUserUseCase
from infrastructure.repositories.cargos_permitidos_repository import (
    CargosPermitidosRepository,
)
from usuarios.models import CargoPermitidoModel


class LoginUserUseCaseCargosDbTests(TestCase):
    """Login com ``CargosPermitidosRepository`` real e linhas explícitas em ``CargoPermitidoModel``."""

    def setUp(self):
        self.codigo_permitido = 8800201
        CargoPermitidoModel.objects.create(
            codigo_cargo=self.codigo_permitido,
            descricao_cargo="CARGO INTEGRACAO LOGIN",
        )
        self.cargos_repo = CargosPermitidosRepository()

    def _use_case(self, coresso: Mock, repository_port: Mock) -> LoginUserUseCase:
        return LoginUserUseCase(
            coresso_port=coresso,
            usuarios_repository_port=repository_port,
            usuarios_validador=UsuariosValidador(),
            usuarios_rbac=UsuariosRbac(),
            cargos_permitidos_port=self.cargos_repo,
        )

    def _payload_autenticacao(self, cargos: list) -> dict:
        return {
            "usuarioId": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            "status": 1,
            "nome": "USUARIO INTEGRACAO",
            "codigoRf": "1234567",
            "rf": "1234567",
            "cpf": None,
            "email": None,
            "cargos": cargos,
            "inexistenteEol": False,
            "contexto": "SME",
            "permissoes": [],
        }

    def test_deve_concluir_login_quando_codigo_esta_na_tabela(self):
        coresso = Mock()
        coresso.autenticar.return_value = self._payload_autenticacao(
            [
                {
                    "codigoCargo": self.codigo_permitido,
                    "descricaoCargo": "CARGO INTEGRACAO LOGIN",
                }
            ]
        )
        repository_port = Mock()
        repository_port.existe_por_rf.return_value = False
        use_case = self._use_case(coresso, repository_port)

        output = use_case.execute(LoginInputDto(login="1234567", senha="abcdef"))

        self.assertEqual(output.rf, "1234567")
        repository_port.persistir_acesso.assert_called_once()

    def test_deve_autorizar_se_algum_dos_cargos_estiver_na_tabela(self):
        coresso = Mock()
        coresso.autenticar.return_value = self._payload_autenticacao(
            [
                {"codigoCargo": 8800299, "descricaoCargo": "NAO CADASTRADO"},
                {"codigoCargo": self.codigo_permitido, "descricaoCargo": "PERMITIDO"},
            ]
        )
        repository_port = Mock()
        repository_port.existe_por_rf.return_value = True
        use_case = self._use_case(coresso, repository_port)

        output = use_case.execute(LoginInputDto(login="1234567", senha="abcdef"))

        self.assertEqual(output.rf, "1234567")

    def test_deve_falhar_quando_codigo_nao_consta_na_tabela(self):
        coresso = Mock()
        coresso.autenticar.return_value = self._payload_autenticacao(
            [{"codigoCargo": 8800298, "descricaoCargo": "SEM LINHA NO BANCO"}]
        )
        repository_port = Mock()
        use_case = self._use_case(coresso, repository_port)

        with self.assertRaises(CargoNaoAutorizadoError):
            use_case.execute(LoginInputDto(login="1234567", senha="abcdef"))

        repository_port.persistir_acesso.assert_not_called()

    def test_deve_falhar_quando_resposta_sem_codigo_cargo(self):
        coresso = Mock()
        coresso.autenticar.return_value = self._payload_autenticacao(
            [{"descricaoCargo": "SEM codigoCargo"}]
        )
        repository_port = Mock()
        use_case = self._use_case(coresso, repository_port)

        with self.assertRaises(CargoNaoAutorizadoError) as ctx:
            use_case.execute(LoginInputDto(login="1234567", senha="abcdef"))

        self.assertIn("identificar", str(ctx.exception).lower())
        repository_port.persistir_acesso.assert_not_called()
