"""Adiciona campo ``status`` aos polos parceiros."""

from django.db import migrations, models


class Migration(migrations.Migration):
    """Inclui status ``ativo``/``inativo`` com padrão ``ativo``."""

    dependencies = [
        ("polos_parceiros", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="poloparceiro",
            name="status",
            field=models.CharField(
                choices=[("ativo", "ativo"), ("inativo", "inativo")],
                default="ativo",
                max_length=10,
                verbose_name="status",
            ),
        ),
    ]
