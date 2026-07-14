"""Adiciona ``codigo_eol`` e flexibiliza campos para polos de gestão Direta."""

from django.db import migrations, models


class Migration(migrations.Migration):
    """Inclui código EOL e permite campos opcionais na integração direta."""

    dependencies = [
        ("polos", "0004_rename_poloparceiro_polo"),
    ]

    operations = [
        migrations.AddField(
            model_name="polo",
            name="codigo_eol",
            field=models.CharField(
                blank=True,
                max_length=20,
                null=True,
                unique=True,
                verbose_name="código EOL",
            ),
        ),
        migrations.AlterField(
            model_name="polo",
            name="cep",
            field=models.CharField(
                blank=True,
                default="",
                max_length=9,
                verbose_name="CEP",
            ),
        ),
        migrations.AlterField(
            model_name="polo",
            name="email_polo",
            field=models.EmailField(
                blank=True,
                default="",
                max_length=255,
                verbose_name="e-mail do polo",
            ),
        ),
        migrations.AlterField(
            model_name="polo",
            name="endereco",
            field=models.CharField(
                blank=True,
                default="",
                max_length=500,
                verbose_name="endereço",
            ),
        ),
        migrations.AlterField(
            model_name="polo",
            name="nome_gestor",
            field=models.CharField(
                blank=True,
                default="",
                max_length=255,
                verbose_name="nome do gestor",
            ),
        ),
        migrations.AlterField(
            model_name="polo",
            name="nome_osc",
            field=models.CharField(
                blank=True,
                default="",
                max_length=255,
                verbose_name="nome da OSC",
            ),
        ),
        migrations.AlterField(
            model_name="polo",
            name="telefone_polo",
            field=models.CharField(
                blank=True,
                default="",
                max_length=20,
                verbose_name="telefone do polo",
            ),
        ),
        migrations.AlterField(
            model_name="polo",
            name="status",
            field=models.CharField(
                choices=[("ativo", "ativo"), ("inativo", "inativo")],
                default="ativo",
                error_messages={
                    "invalid_choice": "Erro: o status deve ser ativo ou inativo",
                },
                max_length=10,
                verbose_name="status",
            ),
        ),
    ]
