"""Adiciona controle da última sincronização de unidades diretas."""

from django.db import migrations, models


class Migration(migrations.Migration):
    """Cria tabela para registrar a última sync de unidades diretas."""

    dependencies = [
        ("polos", "0007_polo_tipo_definicao"),
    ]

    operations = [
        migrations.CreateModel(
            name="ControleSincronizacaoPolos",
            fields=[
                (
                    "chave",
                    models.CharField(
                        max_length=64,
                        primary_key=True,
                        serialize=False,
                        verbose_name="chave",
                    ),
                ),
                (
                    "ultima_execucao_em",
                    models.DateTimeField(verbose_name="última execução"),
                ),
            ],
            options={
                "verbose_name": "controle de sincronização de polos",
                "verbose_name_plural": "controles de sincronização de polos",
                "db_table": "polos_controle_sincronizacao",
            },
        ),
    ]
