"""Cria tabela de polos parceiros com regras de unicidade por nome do polo."""

import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    """Migração inicial do app ``polos``."""

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="PoloParceiro",
            fields=[
                (
                    "atualizado_em",
                    models.DateTimeField(
                        auto_now=True,
                        verbose_name="atualizado em",
                    ),
                ),
                (
                    "criado_em",
                    models.DateTimeField(
                        auto_now_add=True,
                        verbose_name="criado em",
                    ),
                ),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "tipo",
                    models.CharField(
                        default="Parceiro",
                        editable=False,
                        max_length=50,
                        verbose_name="tipo",
                    ),
                ),
                (
                    "nome_osc",
                    models.CharField(
                        max_length=255,
                        verbose_name="nome da OSC",
                    ),
                ),
                (
                    "nome_polo",
                    models.CharField(
                        max_length=255,
                        unique=True,
                        verbose_name="nome do polo",
                    ),
                ),
                (
                    "dre",
                    models.CharField(max_length=255, verbose_name="DRE"),
                ),
                (
                    "tipo_ue",
                    models.CharField(
                        max_length=255,
                        verbose_name="tipo de UE",
                    ),
                ),
                (
                    "quantidade_maxima_alunos",
                    models.PositiveIntegerField(
                        verbose_name="quantidade máxima de alunos",
                    ),
                ),
                (
                    "cep",
                    models.CharField(max_length=9, verbose_name="CEP"),
                ),
                (
                    "endereco",
                    models.CharField(
                        max_length=500,
                        verbose_name="endereço",
                    ),
                ),
                (
                    "nome_gestor",
                    models.CharField(
                        max_length=255,
                        verbose_name="nome do gestor",
                    ),
                ),
                (
                    "email_polo",
                    models.EmailField(
                        max_length=255,
                        verbose_name="e-mail do polo",
                    ),
                ),
                (
                    "telefone_polo",
                    models.CharField(
                        max_length=20,
                        verbose_name="telefone do polo",
                    ),
                ),
                (
                    "observacoes_gerais",
                    models.TextField(
                        blank=True,
                        default="",
                        verbose_name="observações gerais",
                    ),
                ),
            ],
            options={
                "verbose_name": "polo parceiro",
                "verbose_name_plural": "polos parceiros",
                "db_table": "polos_parceiros",
                "ordering": ("-criado_em",),
            },
        ),
    ]
