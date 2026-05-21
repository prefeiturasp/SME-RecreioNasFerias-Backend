"""Adiciona campos de auditoria temporal herdados de ``ModeloBase``."""

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("usuarios", "0009_migrar_acesso_para_conta"),
    ]

    operations = [
        migrations.AddField(
            model_name="usermodel",
            name="atualizado_em",
            field=models.DateTimeField(
                auto_now=True,
                default=django.utils.timezone.now,
                verbose_name="atualizado em",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="usermodel",
            name="criado_em",
            field=models.DateTimeField(
                auto_now_add=True,
                default=django.utils.timezone.now,
                verbose_name="criado em",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="cargopermitidomodel",
            name="atualizado_em",
            field=models.DateTimeField(
                auto_now=True,
                default=django.utils.timezone.now,
                verbose_name="atualizado em",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="cargopermitidomodel",
            name="criado_em",
            field=models.DateTimeField(
                auto_now_add=True,
                default=django.utils.timezone.now,
                verbose_name="criado em",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="logloginmodel",
            name="atualizado_em",
            field=models.DateTimeField(
                auto_now=True,
                default=django.utils.timezone.now,
                verbose_name="atualizado em",
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="logloginmodel",
            name="criado_em",
            field=models.DateTimeField(
                auto_now_add=True, verbose_name="criado em"
            ),
        ),
    ]
