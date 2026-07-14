"""Adiciona ``nome_edicao`` aos polos para vínculo com edições do programa."""

from django.db import migrations, models


class Migration(migrations.Migration):
    """Inclui nome da edição com padrão ``-`` (sem vínculo)."""

    dependencies = [
        ("polos", "0005_polo_codigo_eol_campos_direta"),
    ]

    operations = [
        migrations.AddField(
            model_name="polo",
            name="nome_edicao",
            field=models.CharField(
                blank=True,
                default="-",
                max_length=255,
                verbose_name="nome da edição",
            ),
        ),
    ]
