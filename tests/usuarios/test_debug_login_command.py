from unittest.mock import Mock, patch

import pytest
from django.core.management.base import CommandError

from usuarios.management.commands.debug_login import Command


def test_add_arguments_registra_login_e_senha():
    command = Command()
    parser = Mock()

    command.add_arguments(parser)

    assert parser.add_argument.call_count == 2
    parser.add_argument.assert_any_call("login", help="RF com 7 dígitos")
    parser.add_argument.assert_any_call("--senha", required=True, help="Senha do usuário")


def test_handle_executa_todas_as_etapas_com_sucesso():
    command = Command()
    command.stdout = Mock()
    command.style = Mock(
        NOTICE=lambda mensagem: mensagem,
        SUCCESS=lambda mensagem: mensagem,
        ERROR=lambda mensagem: mensagem,
    )

    with patch("usuarios.management.commands.debug_login.UsuariosService") as service_cls:
        service_inst = Mock()
        service_inst.base_url = "http://fake"
        service_inst.api_eol_key = "eol"
        service_cls.return_value = service_inst

        with patch.object(command, "_validar", return_value=None) as validar_mock:
            with patch.object(
                command, "_autenticar", return_value={"rf": "1234567"}
            ) as autenticar_mock:
                with patch.object(
                    command, "_caso_de_uso", return_value={"rf": "1234567"}
                ) as caso_mock:
                    command.handle(login="1234567", senha="senha123")

    validar_mock.assert_called_once_with("1234567", "senha123")
    autenticar_mock.assert_called_once()
    caso_mock.assert_called_once_with("1234567", "senha123")


def test_handle_interrompe_na_primeira_falha():
    command = Command()
    command.stdout = Mock()
    command.style = Mock(
        NOTICE=lambda mensagem: mensagem,
        SUCCESS=lambda mensagem: mensagem,
        ERROR=lambda mensagem: mensagem,
    )

    with patch("usuarios.management.commands.debug_login.UsuariosService") as service_cls:
        service_inst = Mock()
        service_inst.base_url = ""
        service_inst.api_eol_key = ""
        service_cls.return_value = service_inst

        with patch.object(command, "_validar", side_effect=ValueError("erro de validacao")):
            with pytest.raises(CommandError, match="Parou em: validar entrada"):
                command.handle(login="1234567", senha="senha123")


def test_metodos_auxiliares_usam_servicos_esperados():
    command = Command()
    servico = Mock()
    servico.autenticar.return_value = {"rf": "1234567"}

    with patch(
        "usuarios.management.commands.debug_login.UsuariosValidador"
    ) as validador_cls:
        validador_cls.return_value.validar_login.return_value = None
        command._validar("1234567", "senha123")
        validador_cls.return_value.validar_login.assert_called_once_with(
            login="1234567", senha="senha123"
        )

    assert command._autenticar(servico, "1234567", "senha123") == {"rf": "1234567"}
    servico.autenticar.assert_called_once_with(login="1234567", senha="senha123")

    dto = Mock()
    dto.to_dict.return_value = {"rf": "1234567"}
    with patch("usuarios.management.commands.debug_login.LoginUserUseCase") as use_case_cls:
        use_case_cls.return_value.execute.return_value = dto
        with patch("usuarios.management.commands.debug_login.LoginInputDto") as dto_cls:
            dto_cls.return_value = "dto-login"
            resultado = command._caso_de_uso("1234567", "senha123")

    assert resultado == {"rf": "1234567"}
    dto_cls.assert_called_once_with(login="1234567", senha="senha123")
    use_case_cls.return_value.execute.assert_called_once_with("dto-login")
