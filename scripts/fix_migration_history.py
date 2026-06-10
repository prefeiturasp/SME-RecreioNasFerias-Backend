"""
Corrige histórico após introdução de usuarios.0000_usuario em banco já migrado.

Uso (com venv ativo, na raiz do projeto):
    python scripts/fix_migration_history.py
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from django.core.management import call_command
from django.db import connection
from io import StringIO


def main() -> None:
    """Corrige histórico de migração e sincroniza o estado do banco.

    Args:
        Não recebe argumentos explícitos.

    Returns:
        None: Executa operações no banco e imprime o progresso no terminal.

    Raises:
        Exception: Propaga erros de conexão/execução de SQL e comandos Django.
    """
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT 1 FROM django_migrations WHERE app = %s AND name = %s",
            ["usuarios", "0000_usuario"],
        )
        if cursor.fetchone() is None:
            cursor.execute(
                "INSERT INTO django_migrations (app, name, applied) "
                "VALUES (%s, %s, NOW())",
                ["usuarios", "0000_usuario"],
            )
            print("Registrada migração usuarios.0000_usuario no histórico.")
        else:
            print("usuarios.0000_usuario já consta no histórico.")

        cursor.execute("SELECT to_regclass('public.usuarios_conta')")
        if cursor.fetchone()[0] is None:
            print("Criando tabela usuarios_conta e relações...")
            out = StringIO()
            call_command("sqlmigrate", "usuarios", "0000_usuario", stdout=out)
            sql = out.getvalue()
            for statement in _split_sql(sql):
                if statement.strip():
                    cursor.execute(statement)
            print("Tabela usuarios_conta criada.")
        else:
            print("Tabela usuarios_conta já existe.")

        cursor.execute(
            "DELETE FROM django_migrations WHERE app = %s",
            ["contas"],
        )
        if cursor.rowcount:
            print(f"Removidos {cursor.rowcount} registro(s) do app 'contas'.")

    print("Executando migrate...")
    call_command("migrate", verbosity=1)
    print("Concluído.")


def _split_sql(sql: str) -> list[str]:
    parts: list[str] = []
    buffer: list[str] = []
    for line in sql.splitlines():
        stripped = line.strip()
        if stripped.startswith("--") or stripped in ("BEGIN;", "COMMIT;"):
            continue
        buffer.append(line)
        if stripped.endswith(";"):
            parts.append("\n".join(buffer))
            buffer = []
    return parts


if __name__ == "__main__":
    main()
