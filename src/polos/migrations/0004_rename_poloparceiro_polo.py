"""Renomeia modelo e tabela de polos parceiros para polos."""

from django.db import migrations


class Migration(migrations.Migration):
    """Alinha nomenclatura ao domínio de polos (parceiros e diretos)."""

    dependencies = [
        ("polos", "0003_poloparceiro_gestao"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="PoloParceiro",
            new_name="Polo",
        ),
        migrations.AlterModelTable(
            name="polo",
            table="polos",
        ),
        migrations.AlterModelOptions(
            name="polo",
            options={
                "ordering": ("-criado_em",),
                "verbose_name": "polo",
                "verbose_name_plural": "polos",
            },
        ),
    ]
