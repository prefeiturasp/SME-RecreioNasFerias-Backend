"""Altera chave primária de LogLoginModel para UUID.

Recria a tabela ``usuarios_logs_login`` (registros anteriores são descartados).
"""

import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("usuarios", "0003_logloginmodel"),
    ]

    operations = [
        migrations.DeleteModel(name="LogLoginModel"),
        migrations.CreateModel(
            name="LogLoginModel",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        primary_key=True,
                        default=uuid.uuid4,
                        editable=False,
                        serialize=False,
                    ),
                ),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                ("sucesso", models.BooleanField()),
                (
                    "login_tentativa",
                    models.CharField(blank=True, default="", max_length=32),
                ),
                ("codigo_http", models.PositiveSmallIntegerField()),
                ("mensagem", models.TextField(blank=True, default="")),
                (
                    "endereco_ip",
                    models.CharField(blank=True, default="", max_length=45),
                ),
                ("user_agent", models.TextField(blank=True, default="")),
            ],
            options={
                "db_table": "usuarios_logs_login",
                "ordering": ("-criado_em",),
            },
        ),
    ]
