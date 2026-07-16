"""Testes das migrações Django do app ``polos`` (novo e legado)."""

from django.core.management import call_command
from django.db import connection
from django.test import TransactionTestCase


class MigracaoPolosTests(TransactionTestCase):
    """Valida migrate puro e fluxo legado com ``--fake``."""

    reset_sequences = True

    def _limpar_estado_polos(self) -> None:
        """Remove tabelas e histórico do app polos para simular cenários."""
        with connection.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS polos CASCADE")
            cursor.execute("DROP TABLE IF EXISTS polos_parceiros CASCADE")
            cursor.execute(
                "DROP TABLE IF EXISTS polos_controle_sincronizacao CASCADE",
            )
            cursor.execute(
                "DELETE FROM django_migrations WHERE app IN (%s, %s)",
                ["polos", "polos_parceiros"],
            )

    def _criar_tabela_legada_polos_parceiros(self) -> None:
        """Simula o estado pós ``polos_parceiros.0001`` + ``0002``."""
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE polos_parceiros (
                    id uuid PRIMARY KEY,
                    atualizado_em timestamptz NOT NULL,
                    criado_em timestamptz NOT NULL,
                    tipo varchar(50) NOT NULL,
                    nome_osc varchar(255) NOT NULL,
                    nome_polo varchar(255) NOT NULL UNIQUE,
                    dre varchar(255) NOT NULL,
                    tipo_ue varchar(255) NOT NULL,
                    quantidade_maxima_alunos integer
                        NOT NULL CHECK (quantidade_maxima_alunos >= 0),
                    cep varchar(9) NOT NULL,
                    endereco varchar(500) NOT NULL,
                    nome_gestor varchar(255) NOT NULL,
                    email_polo varchar(255) NOT NULL,
                    telefone_polo varchar(20) NOT NULL,
                    observacoes_gerais text NOT NULL,
                    status varchar(10) NOT NULL DEFAULT 'ativo'
                )
                """,
            )
            cursor.execute(
                "INSERT INTO django_migrations (app, name, applied) VALUES "
                "(%s, %s, NOW()), (%s, %s, NOW())",
                [
                    "polos_parceiros",
                    "0001_initial",
                    "polos_parceiros",
                    "0002_poloparceiro_status",
                ],
            )

    def test_migrate_em_banco_novo_cria_polos(self) -> None:
        """Garante criação completa das migrações em ambiente limpo."""
        self._limpar_estado_polos()

        call_command("migrate", "polos", verbosity=0)

        with connection.cursor() as cursor:
            cursor.execute("SELECT to_regclass('public.polos')")
            self.assertIsNotNone(cursor.fetchone()[0])
            cursor.execute(
                """
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = current_schema()
                  AND table_name = 'polos'
                  AND column_name = 'gestao'
                """,
            )
            self.assertIsNotNone(cursor.fetchone())

    def test_legado_com_preparar_migracao_aplica_restante(self) -> None:
        """Garante fake de 0001/0002 e migrate das demais no banco legado."""
        self._limpar_estado_polos()
        self._criar_tabela_legada_polos_parceiros()

        call_command("preparar_migracao_polos_legado", verbosity=0)

        with connection.cursor() as cursor:
            cursor.execute("SELECT to_regclass('public.polos')")
            self.assertIsNotNone(cursor.fetchone()[0])
            cursor.execute("SELECT to_regclass('public.polos_parceiros')")
            self.assertIsNone(cursor.fetchone()[0])
            cursor.execute(
                "SELECT COUNT(*) FROM django_migrations WHERE app = %s",
                ["polos_parceiros"],
            )
            self.assertEqual(cursor.fetchone()[0], 0)
            cursor.execute(
                "SELECT COUNT(*) FROM django_migrations WHERE app = %s",
                ["polos"],
            )
            self.assertGreaterEqual(cursor.fetchone()[0], 8)
