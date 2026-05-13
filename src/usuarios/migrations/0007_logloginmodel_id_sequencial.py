"""Recria log de login com ``id`` sequencial (BigAutoField).

Remove o uso de UUID na tabela ``usuarios_logs_login``; os registros
existentes são descartados (tabela recriada).
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("usuarios", "0006_logloginmodel_cargo_e_correcao_id"),
    ]

    operations = [
        migrations.DeleteModel(name="LogLoginModel"),
        migrations.CreateModel(
            name="LogLoginModel",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
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
                ("codigo_cargo", models.IntegerField(blank=True, null=True)),
                (
                    "descricao_cargo",
                    models.CharField(blank=True, default="", max_length=500),
                ),
            ],
            options={
                "db_table": "usuarios_logs_login",
                "ordering": ("-criado_em",),
            },
        ),
    ]
