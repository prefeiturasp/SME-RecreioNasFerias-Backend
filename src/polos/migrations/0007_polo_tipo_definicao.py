"""Redefine ``tipo`` para Pendente, Polo oficial e Polo reserva."""

from django.db import migrations, models


def migrar_tipos_antigos(apps, _schema_editor):
    """Converte valores legados de ``tipo`` para ``Pendente``."""
    Polo = apps.get_model("polos", "Polo")
    Polo.objects.exclude(
        tipo__in=["Pendente", "Polo oficial", "Polo reserva"],
    ).update(tipo="Pendente")
    Polo.objects.filter(tipo="").update(tipo="Pendente")


class Migration(migrations.Migration):
    """Atualiza choices/default de ``tipo`` e normaliza registros existentes."""

    dependencies = [
        ("polos", "0006_polo_nome_edicao"),
    ]

    operations = [
        migrations.RunPython(migrar_tipos_antigos, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="polo",
            name="tipo",
            field=models.CharField(
                choices=[
                    ("Pendente", "Pendente"),
                    ("Polo oficial", "Polo oficial"),
                    ("Polo reserva", "Polo reserva"),
                ],
                default="Pendente",
                error_messages={
                    "invalid_choice": (
                        "Erro: o tipo deve ser Pendente, Polo oficial ou Polo reserva"
                    ),
                },
                max_length=50,
                verbose_name="tipo",
            ),
        ),
    ]
