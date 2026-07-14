"""Adiciona campo ``gestao`` aos polos."""

from django.db import migrations, models


class Migration(migrations.Migration):
    """Inclui gestão ``Parceira``/``Direta`` com padrão ``Parceira``."""

    dependencies = [
        ("polos", "0002_poloparceiro_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="poloparceiro",
            name="gestao",
            field=models.CharField(
                choices=[("Parceira", "Parceira"), ("Direta", "Direta")],
                default="Parceira",
                error_messages={
                    "invalid_choice": "Erro: a gestão deve ser Parceira ou Direta",
                },
                max_length=20,
                verbose_name="gestão",
            ),
        ),
    ]
