"""Cria tabela de log de tentativas de login."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("usuarios", "0002_usuarioacessomodel"),
    ]

    operations = [
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
            ],
            options={
                "db_table": "usuarios_logs_login",
                "ordering": ("-criado_em",),
            },
        ),
    ]
