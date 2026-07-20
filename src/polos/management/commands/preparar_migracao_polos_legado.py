"""
Prepara ambientes legados antes de ``migrate`` do app ``polos``.

Quando a tabela ``polos_parceiros`` já existe (app antigo) e as migrações
``polos.0001``/``0002`` ainda não constam no histórico, marca-as como
aplicadas com ``--fake`` e remove o histórico residual de ``polos_parceiros``.
Deve ser executado antes de ``migrate`` no startup do container.
"""

from __future__ import annotations

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    """Compatibiliza banco legado com migrações Django do app ``polos``."""

    help = (
        "Faz fake de polos.0001/0002 quando a tabela polos_parceiros "
        "já existe, para permitir migrate normal em bancos legados."
    )

    def handle(self, *args: object, **options: object) -> None:
        """Detecta legado e aplica ``--fake`` quando necessário.

        Args:
            *args: Argumentos posicionais do Django.
            **options: Opções do comando.
        """
        if self._precisa_fake_legado():
            self.stdout.write(
                "Tabela polos_parceiros detectada sem histórico polos.0001/0002.",
            )
            self._limpar_historico_polos_parceiros()
            call_command("migrate", "polos", "0002", fake=True, verbosity=1)
            self.stdout.write(
                self.style.SUCCESS(
                    "polos.0001 e polos.0002 marcadas como aplicadas (--fake).",
                ),
            )
        else:
            self.stdout.write(
                "Nenhum ajuste de legado necessário para polos.0001/0002.",
            )

        self.stdout.write(self.style.SUCCESS("Preparação de polos concluída."))

    def _precisa_fake_legado(self) -> bool:
        """Indica se o banco exige ``--fake`` das migrações iniciais.

        Returns:
            bool: ``True`` quando a tabela legada existe e ``0001`` não
            está registrada para o app ``polos``.
        """
        with connection.cursor() as cursor:
            cursor.execute("SELECT to_regclass('public.polos_parceiros')")
            tabela_existe = cursor.fetchone()[0] is not None
            if not tabela_existe:
                return False

            cursor.execute(
                "SELECT 1 FROM django_migrations WHERE app = %s AND name = %s",
                ["polos", "0001_initial"],
            )
            return cursor.fetchone() is None

    def _limpar_historico_polos_parceiros(self) -> None:
        """Remove registros do app antigo ``polos_parceiros`` do histórico."""
        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM django_migrations WHERE app = %s",
                ["polos_parceiros"],
            )
            if cursor.rowcount:
                self.stdout.write(
                    f"Removidos {cursor.rowcount} registro(s) de "
                    "django_migrations do app polos_parceiros.",
                )
