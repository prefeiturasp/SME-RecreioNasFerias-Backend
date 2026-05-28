"""
Comando Django para diagnosticar o fluxo de login sem passar pela API HTTP.

Executa validação local, autenticação no CoreSSO e caso de uso completo em
etapas separadas, exibindo a exceção exata no terminal.
"""

import traceback

from django.core.management.base import BaseCommand, CommandError

from application.dtos.login_input_dto import LoginInputDto
from application.services.usuarios_rbac import UsuariosRbac
from application.services.usuarios_validador import UsuariosValidador
from application.use_cases.login_user import LoginUserUseCase
from infrastructure.repositories.cargos_permitidos_repository import (
    CargosPermitidosRepository,
)
from infrastructure.repositories.usuarios_repository import UsuariosRepository
from infrastructure.services.usuarios_service import UsuariosService


class Command(BaseCommand):
    """Executa ``LoginUserUseCase`` passo a passo para diagnóstico de falhas."""

    help = "Executa o fluxo de login em etapas e exibe erros no terminal."

    def add_arguments(self, parser):
        """Registra argumentos do comando.

        Args:
            parser: Parser do Django management.
        """
        parser.add_argument("login", help="RF com 7 dígitos")
        parser.add_argument("--senha", required=True, help="Senha do usuário")

    def handle(self, *args, **options):
        """Executa as etapas de login e interrompe na primeira falha.

        Args:
            *args: Argumentos posicionais do Django (não utilizados).
            **options: Opções parseadas (``login``, ``senha``).

        Raises:
            CommandError: Quando alguma etapa falhar.
        """
        login = options["login"]
        senha = options["senha"]
        servico = UsuariosService()
        self.stdout.write(f"AUTH_API_BASE_URL={servico.base_url or '(vazio)'}")
        self.stdout.write(
            f"AUTH_API_EOL_KEY configurada={'sim' if servico.api_eol_key else 'não'}"
        )

        etapas = [
            ("validar entrada", self._validar, login, senha),
            ("autenticar CoreSSO", self._autenticar, servico, login, senha),
            ("caso de uso completo", self._caso_de_uso, login, senha),
        ]
        for nome, funcao, *argumentos in etapas:
            self.stdout.write(self.style.NOTICE(f"\n--- {nome} ---"))
            try:
                resultado = funcao(*argumentos)
                if isinstance(resultado, dict):
                    self.stdout.write(
                        self.style.SUCCESS(f"OK: rf={resultado.get('rf')}")
                    )
                else:
                    self.stdout.write(self.style.SUCCESS("OK"))
            except Exception as exc:
                self.stdout.write(
                    self.style.ERROR(f"FALHOU: {type(exc).__name__}: {exc}")
                )
                traceback.print_exc()
                raise CommandError(f"Parou em: {nome}") from exc

        self.stdout.write(
            self.style.SUCCESS("\nLogin concluído com sucesso (sem token HTTP).")
        )

    def _validar(self, login: str, senha: str) -> None:
        """Valida RF e senha localmente."""
        UsuariosValidador().validar_login(login=login, senha=senha)

    def _autenticar(self, servico: UsuariosService, login: str, senha: str) -> dict:
        """Chama apenas a integração HTTP com o CoreSSO."""
        return servico.autenticar(login=login, senha=senha)

    def _caso_de_uso(self, login: str, senha: str) -> dict:
        """Executa o caso de uso completo de login."""
        saida = LoginUserUseCase(
            coresso_port=UsuariosService(),
            usuarios_repository_port=UsuariosRepository(),
            usuarios_validador=UsuariosValidador(),
            usuarios_rbac=UsuariosRbac(),
            cargos_permitidos_port=CargosPermitidosRepository(),
        ).execute(LoginInputDto(login=login, senha=senha))
        return saida.to_dict()
