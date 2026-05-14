"""Caso de uso para autenticacao de usuario."""

from application.dtos.login_input_dto import LoginInputDto
from application.dtos.login_output_dto import LoginOutputDto
from application.exceptions import CargoNaoAutorizadoError
from application.services.usuarios_rbac import UsuariosRbac
from application.services.usuarios_validador import UsuariosValidador
from domain.ports.cargos_permitidos_port import CargosPermitidosPort
from domain.ports.coresso_port import CoressoPort
from domain.ports.usuarios_repository_port import UsuariosRepositoryPort


def _extrair_codigos_cargos(cargos: object) -> list[int]:
    """Coleta ``codigoCargo`` inteiro de cada item da lista retornada pela integração."""
    if not isinstance(cargos, list):
        return []
    codigos: list[int] = []
    for item in cargos:
        if not isinstance(item, dict):
            continue
        bruto = item.get("codigoCargo")
        if bruto is None or bruto == "":
            continue
        try:
            codigos.append(int(bruto))
        except (TypeError, ValueError):
            continue
    return codigos


class LoginUserUseCase:
    """Orquestra o fluxo completo de login conforme história."""

    def __init__(
        self,
        coresso_port: CoressoPort,
        usuarios_repository_port: UsuariosRepositoryPort,
        usuarios_validador: UsuariosValidador,
        usuarios_rbac: UsuariosRbac,
        cargos_permitidos_port: CargosPermitidosPort,
    ):
        """Recebe dependências do fluxo de autenticação e persistência."""
        self.coresso_port = coresso_port
        self.usuarios_repository_port = usuarios_repository_port
        self.usuarios_validador = usuarios_validador
        self.usuarios_rbac = usuarios_rbac
        self.cargos_permitidos_port = cargos_permitidos_port

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
        codigos_cargo = _extrair_codigos_cargos(autenticacao.get("cargos"))
        if not codigos_cargo:
            raise CargoNaoAutorizadoError(
                "Não foi possível identificar o cargo do usuário para autorização."
            )
        if not self.cargos_permitidos_port.algum_codigo_autorizado(codigos_cargo):
            raise CargoNaoAutorizadoError()

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
