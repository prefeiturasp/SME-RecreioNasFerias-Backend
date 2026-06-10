"""Cria tabela de edições com regras de unicidade por nome e período."""

import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    """Migração inicial do app ``edicoes``."""

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Edicao",
            fields=[
                ("atualizado_em", models.DateTimeField(auto_now=True, verbose_name="atualizado em")),
                ("criado_em", models.DateTimeField(auto_now_add=True, verbose_name="criado em")),
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("nome", models.CharField(max_length=255, unique=True, verbose_name="nome da edição")),
                ("periodo_edicao_inicio", models.DateField(verbose_name="período da edição - início")),
                ("periodo_edicao_fim", models.DateField(verbose_name="período da edição - fim")),
                (
                    "periodo_inscricoes_inicio",
                    models.DateField(verbose_name="período das inscrições - início"),
                ),
                ("periodo_inscricoes_fim", models.DateField(verbose_name="período das inscrições - fim")),
                (
                    "quantidade_inscritos",
                    models.PositiveIntegerField(
                        blank=True,
                        editable=False,
                        null=True,
                        verbose_name="quantidade de inscritos",
                    ),
                ),
                (
                    "quantidade_atendimento_efetivo",
                    models.PositiveIntegerField(
                        blank=True,
                        editable=False,
                        null=True,
                        verbose_name="quantidade de atendimento efetivo",
                    ),
                ),
                (
                    "quantidade_passeios",
                    models.PositiveIntegerField(
                        blank=True,
                        editable=False,
                        null=True,
                        verbose_name="quantidade de passeios",
                    ),
                ),
                (
                    "quantidade_apresentacoes",
                    models.PositiveIntegerField(
                        blank=True,
                        editable=False,
                        null=True,
                        verbose_name="quantidade de apresentações",
                    ),
                ),
            ],
            options={
                "verbose_name": "edição",
                "verbose_name_plural": "edições",
                "db_table": "edicoes",
                "ordering": ("-criado_em",),
                "constraints": [
                    models.UniqueConstraint(
                        fields=("periodo_edicao_inicio", "periodo_edicao_fim"),
                        name="edicoes_periodo_unico",
                    )
                ],
            },
        ),
    ]
