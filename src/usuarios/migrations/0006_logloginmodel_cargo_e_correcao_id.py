"""Adiciona cargo ao log e corrige coluna ``id`` no PostgreSQL.

- Inclui ``codigo_cargo`` e ``descricao_cargo`` (primeiro cargo SIGPAE).
- Se ``id`` for inteiro (schema antigo), converte para UUID.
- Se ``id`` for UUID com nulos, preenche e torna NOT NULL.
"""

from django.db import migrations, models


def _nome_constraint_pk_postgres(cursor, tabela: str) -> str | None:
    """Retorna o nome da constraint PRIMARY KEY da tabela."""
    cursor.execute(
        """
        SELECT tc.constraint_name
        FROM information_schema.table_constraints AS tc
        WHERE tc.table_schema = 'public'
          AND tc.table_name = %s
          AND tc.constraint_type = 'PRIMARY KEY'
        """,
        [tabela],
    )
    row = cursor.fetchone()
    return row[0] if row else None


def corrigir_log_login_id_e_schema(_apps, schema_editor):
    """Ajusta tipo da PK e valores nulos em ``usuarios_logs_login`` (PostgreSQL)."""
    if schema_editor.connection.vendor != "postgresql":
        return
    tabela = "usuarios_logs_login"
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = %s
              AND column_name = 'id'
            """,
            [tabela],
        )
        row = cursor.fetchone()
        if not row:
            return
        data_type, is_nullable = row[0], row[1]

        if data_type in ("bigint", "integer", "smallint"):
            nome_pk = _nome_constraint_pk_postgres(cursor, tabela)
            if nome_pk:
                cursor.execute(
                    f'ALTER TABLE "{tabela}" DROP CONSTRAINT "{nome_pk}";'
                )
            cursor.execute(
                f'ALTER TABLE "{tabela}" ALTER COLUMN id DROP DEFAULT;'
            )
            cursor.execute(
                f"""
                ALTER TABLE "{tabela}"
                ALTER COLUMN id TYPE uuid USING gen_random_uuid();
                """
            )
            cursor.execute(
                f'ALTER TABLE "{tabela}" ADD PRIMARY KEY (id);'
            )
            cursor.execute(
                f"""
                ALTER TABLE "{tabela}"
                ALTER COLUMN id SET DEFAULT gen_random_uuid();
                """
            )
            return

        if data_type == "uuid":
            cursor.execute(
                f"""
                UPDATE "{tabela}" SET id = gen_random_uuid() WHERE id IS NULL;
                """
            )
            if is_nullable == "YES":
                cursor.execute(
                    f'ALTER TABLE "{tabela}" ALTER COLUMN id SET NOT NULL;'
                )
            cursor.execute(
                f"""
                ALTER TABLE "{tabela}"
                ALTER COLUMN id SET DEFAULT gen_random_uuid();
                """
            )


def reverter_correcao_id(_apps, _schema_editor):
    """Não reverte conversão de tipo de PK (operação destrutiva)."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("usuarios", "0005_logloginmodel_id_default_pg"),
    ]

    operations = [
        migrations.AddField(
            model_name="logloginmodel",
            name="codigo_cargo",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="logloginmodel",
            name="descricao_cargo",
            field=models.CharField(blank=True, default="", max_length=500),
        ),
        migrations.RunPython(corrigir_log_login_id_e_schema, reverter_correcao_id),
    ]
