from unittest.mock import Mock

from django.test import TestCase

from application.dtos.login_input_dto import LoginInputDto
from application.services.usuarios_rbac import UsuariosRbac
from application.services.usuarios_validador import UsuariosValidador
from application.use_cases.login_user import LoginUserUseCase


class LoginUserUseCaseTests(TestCase):
    """Testes do caso de uso de login com fluxo completo."""

    def test_deve_autenticar_usuario_existente_e_vincular_contexto(self):
        coresso_port = Mock()
        coresso_port.autenticar.return_value = {
            "usuarioId": "5b2b9b98-7692-e211-b1fe-782bcb3d2d76",
            "status": 1,
            "nome": "VANIA FERREIRA DA SILVA CANEKI",
            "codigoRf": "8080640",
            "rf": "8080640",
            "cpf": "22712612876",
            "email": "vania.montefusco@sme.prefeitura.sp.gov.br",
            "cargos": [{"descricaoCargo": "ASSISTENTE TECNICO DE EDUCACAO I"}],
            "inexistenteEol": False,
            "contexto": "DRE",
            "permissoes": ["usuarios:listar", "usuarios:listar", "usuarios:editar"],
        }
        repository_port = Mock()
        repository_port.existe_por_rf.return_value = True
        use_case = LoginUserUseCase(
            coresso_port=coresso_port,
            usuarios_repository_port=repository_port,
            usuarios_validador=UsuariosValidador(),
            usuarios_rbac=UsuariosRbac(),
        )
        input_dto = LoginInputDto(login="1234567", senha="123456")

        output = use_case.execute(input_dto)

        coresso_port.autenticar.assert_called_once_with(login="1234567", senha="123456")
        repository_port.existe_por_rf.assert_called_once_with("8080640")
        repository_port.vincular_contexto_permissoes.assert_called_once_with(
            rf="8080640",
            contexto="DRE",
            permissoes=["usuarios:listar", "usuarios:editar"],
        )
        repository_port.registrar_localmente.assert_not_called()
        repository_port.persistir_acesso.assert_called_once_with(
            rf="8080640",
            contexto="DRE",
            permissoes=["usuarios:listar", "usuarios:editar"],
        )
        self.assertEqual(output.rf, "8080640")
        self.assertEqual(output.cpf, "22712612876")
        self.assertEqual(output.email, "vania.montefusco@sme.prefeitura.sp.gov.br")
        self.assertEqual(output.cargos, [{"descricaoCargo": "ASSISTENTE TECNICO DE EDUCACAO I"}])
        self.assertEqual(output.nome, "VANIA FERREIRA DA SILVA CANEKI")
        self.assertFalse(output.inexistente_eol)

    def test_deve_autenticar_usuario_novo_e_registrar_localmente(self):
        coresso_port = Mock()
        coresso_port.autenticar.return_value = {
            "usuarioId": "12345678-1234-1234-1234-123456789abc",
            "status": 1,
            "nome": "USUARIO TESTE",
            "codigoRf": "7654321",
            "rf": "7654321",
            "cpf": None,
            "email": None,
            "cargos": [],
            "inexistenteEol": False,
            "contexto": "SME",
            "permissoes": ["usuarios:listar"],
        }
        repository_port = Mock()
        repository_port.existe_por_rf.return_value = False
        use_case = LoginUserUseCase(
            coresso_port=coresso_port,
            usuarios_repository_port=repository_port,
            usuarios_validador=UsuariosValidador(),
            usuarios_rbac=UsuariosRbac(),
        )
        input_dto = LoginInputDto(login="7654321", senha="abc123")

        output = use_case.execute(input_dto)

        repository_port.existe_por_rf.assert_called_once_with("7654321")
        repository_port.registrar_localmente.assert_called_once_with(
            rf="7654321",
            contexto="SME",
            permissoes=["usuarios:listar"],
        )
        repository_port.vincular_contexto_permissoes.assert_not_called()
        repository_port.persistir_acesso.assert_called_once_with(
            rf="7654321",
            contexto="SME",
            permissoes=["usuarios:listar"],
        )
        self.assertEqual(output.rf, "7654321")
        self.assertIsNone(output.cpf)
        self.assertIsNone(output.email)
        self.assertEqual(output.cargos, [])
        self.assertEqual(output.nome, "USUARIO TESTE")
        self.assertFalse(output.inexistente_eol)
