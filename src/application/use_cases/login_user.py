"""
Caso de uso para autenticação de usuário via CoreSSO.

Coordena validação de entrada, autenticação externa, verificação de cargos
permitidos na base local, normalização de permissões RBAC e sincronização da
conta Django usada para emissão do token Bearer nas requisições subsequentes.
"""

from application.dtos.login_input_dto import LoginInputDto
from application.dtos.login_output_dto import LoginOutputDto
from application.exceptions import CargoNaoAutorizadoError
from application.services.usuarios_rbac import UsuariosRbac
from application.services.usuarios_validador import UsuariosValidador
from config.login_debug import login_debug
from domain.ports.cargos_permitidos_port import CargosPermitidosPort
from domain.ports.coresso_port import CoressoPort
from domain.ports.usuarios_repository_port import UsuariosRepositoryPort


def _extrair_codigos_cargos(cargos: object) -> list[int]:
    """Coleta ``codigoCargo`` inteiro de cada item da lista SIGPAE.

    Args:
        cargos (object): Valor bruto do campo ``cargos`` retornado pela integração.

    Returns:
        list[int]: Códigos numéricos de cargo válidos; lista vazia se o formato
            não for uma lista de dicionários compatível.
    """
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
    """Orquestra validação, CoreSSO, RBAC de cargos e persistência local.

    É o núcleo do fluxo ``POST /api/auth/login/``. Não gera token; a view
    complementa a resposta após ``execute`` com ``gerar_token_acesso``.

    Attributes:
        coresso_port (CoressoPort): Integração HTTP com autenticação e SIGPAE.
        usuarios_repository_port (UsuariosRepositoryPort): Persistência da conta
            Django sincronizada.
        usuarios_validador (UsuariosValidador): Validação síncrona de credenciais.
        usuarios_rbac (UsuariosRbac): Normalização de permissões.
        cargos_permitidos_port (CargosPermitidosPort): Autorização por código de cargo.
    """

    def __init__(
        self,
        coresso_port: CoressoPort,
        usuarios_repository_port: UsuariosRepositoryPort,
        usuarios_validador: UsuariosValidador,
        usuarios_rbac: UsuariosRbac,
        cargos_permitidos_port: CargosPermitidosPort,
    ):
        """Injeta dependências do fluxo completo de login.

        Args:
            coresso_port (CoressoPort): Integração HTTP com CoreSSO.
            usuarios_repository_port (UsuariosRepositoryPort): Persistência da conta
                Django sincronizada.
            usuarios_validador (UsuariosValidador): Validação de credenciais de entrada.
            usuarios_rbac (UsuariosRbac): Normalização de permissões RBAC.
            cargos_permitidos_port (CargosPermitidosPort): Verificação de cargos
                autorizados na base local.
        """
        self.coresso_port = coresso_port
        self.usuarios_repository_port = usuarios_repository_port
        self.usuarios_validador = usuarios_validador
        self.usuarios_rbac = usuarios_rbac
        self.cargos_permitidos_port = cargos_permitidos_port

    def execute(self, login_input: LoginInputDto) -> LoginOutputDto:
        """Processa login, aplica RBAC de cargos e persiste contexto local.

        Args:
            login_input (LoginInputDto): Credenciais validadas de entrada.

        Returns:
            LoginOutputDto: Dados funcionais para resposta HTTP (sem token Bearer).

        Raises:
            ValueError: Propagada pelo validador de entrada local.
            CoressoRespostaError: Propagada pelo serviço CoreSSO (401, 404, etc.).
            CoressoIndisponivelError: Quando o CoreSSO está indisponível.
            CargoNaoAutorizadoError: Se nenhum cargo permitido for identificado.
        """
        self.usuarios_validador.validar_login(
            login=login_input.login,
            senha=login_input.senha,
        )

        autenticacao = self.coresso_port.autenticar(
            login=login_input.login,
            senha=login_input.senha,
        )
        codigos_cargo = _extrair_codigos_cargos(autenticacao.get("cargos"))
        login_debug("use_case.cargos", codigos=codigos_cargo)
        if not codigos_cargo:
            raise CargoNaoAutorizadoError(
                "Não foi possível identificar o cargo do usuário para autorização."
            )
        autorizado = self.cargos_permitidos_port.algum_codigo_autorizado(codigos_cargo)
        login_debug("use_case.cargos_permitidos", autorizado=autorizado)
        if not autorizado:
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
            nome=autenticacao["nome"],
            email=autenticacao.get("email"),
            cpf=autenticacao.get("cpf"),
            inexistente_eol=bool(autenticacao.get("inexistenteEol", False)),
        )

        return LoginOutputDto(
            rf=autenticacao["rf"],
            cpf=autenticacao.get("cpf"),
            email=autenticacao.get("email"),
            cargos=autenticacao.get("cargos", []),
            nome=autenticacao["nome"],
            inexistente_eol=autenticacao.get("inexistenteEol", False),
        )
