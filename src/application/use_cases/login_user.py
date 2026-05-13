"""Caso de uso para autenticacao de usuario."""

from application.dtos.login_input_dto import LoginInputDto
from application.dtos.login_output_dto import LoginOutputDto
from application.services.usuarios_rbac import UsuariosRbac
from application.services.usuarios_validador import UsuariosValidador
from domain.ports.coresso_port import CoressoPort
from domain.ports.usuarios_repository_port import UsuariosRepositoryPort


class LoginUserUseCase:
    """Orquestra o fluxo completo de login conforme história."""

    def __init__(
        self,
        coresso_port: CoressoPort,
        usuarios_repository_port: UsuariosRepositoryPort,
        usuarios_validador: UsuariosValidador,
        usuarios_rbac: UsuariosRbac,
    ):
        """Recebe dependências do fluxo de autenticação e persistência."""
        self.coresso_port = coresso_port
        self.usuarios_repository_port = usuarios_repository_port
        self.usuarios_validador = usuarios_validador
        self.usuarios_rbac = usuarios_rbac

    def execute(self, login_input: LoginInputDto) -> LoginOutputDto:
        """Processa login, aplica RBAC e persiste contexto local."""
        self.usuarios_validador.validar_login(
            login=login_input.login,
            senha=login_input.senha,
        )

        autenticacao = self.coresso_port.autenticar(
            login=login_input.login,
            senha=login_input.senha,
        )
        contexto = autenticacao.get("contexto") or autenticacao.get("cargo", "")
        permissoes = self.usuarios_rbac.aplicar(autenticacao.get("permissoes", []))
        codigo_rf = autenticacao["codigoRf"]

        if self.usuarios_repository_port.existe_por_rf(codigo_rf):
            self.usuarios_repository_port.vincular_contexto_permissoes(
                rf=codigo_rf,
                contexto=contexto,
                permissoes=permissoes,
            )
        else:
            self.usuarios_repository_port.registrar_localmente(
                rf=codigo_rf,
                contexto=contexto,
                permissoes=permissoes,
            )

        self.usuarios_repository_port.persistir_acesso(
            rf=codigo_rf,
            contexto=contexto,
            permissoes=permissoes,
        )

        return LoginOutputDto(
            rf=autenticacao["rf"],
            cpf=autenticacao.get("cpf"),
            email=autenticacao.get("email"),
            cargos=autenticacao.get("cargos", []),
            nome=autenticacao["nome"],
            inexistente_eol=autenticacao.get("inexistenteEol", False),
        )
