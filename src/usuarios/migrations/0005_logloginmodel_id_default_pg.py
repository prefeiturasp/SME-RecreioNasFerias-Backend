"""Garante default de UUID na coluna id (apenas PostgreSQL).

Corrige linhas com ``id`` nulo, torna a coluna NOT NULL e define
``DEFAULT gen_random_uuid()`` para inserts que omitam o campo.
Em outros backends a aplicação define ``id`` no código (``log_login.py``).
"""


from django.db import migrations


def aplicar_default_uuid_id(apps, schema_editor):
    """Aplica correção de UUID na PK apenas no PostgreSQL."""
    if schema_editor.connection.vendor != "postgresql":
        return
    sql = """
        UPDATE usuarios_logs_login
        SET id = gen_random_uuid()
        WHERE id IS NULL;
        ALTER TABLE usuarios_logs_login
        ALTER COLUMN id SET NOT NULL;
        ALTER TABLE usuarios_logs_login
        ALTER COLUMN id SET DEFAULT gen_random_uuid();
    """
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(sql)


def reverter_default_uuid_id(apps, schema_editor):
    """Remove default de UUID no PostgreSQL."""
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            "ALTER TABLE usuarios_logs_login ALTER COLUMN id DROP DEFAULT;"
        )


class Migration(migrations.Migration):

    dependencies = [
        ("usuarios", "0004_logloginmodel_uuid_pk"),
    ]

    operations = [
        migrations.RunPython(aplicar_default_uuid_id, reverter_default_uuid_id),
    ]
