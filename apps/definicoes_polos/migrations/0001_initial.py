# Generated manually for the initial DefinicaoPolo domain.

import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("edicoes", "0001_initial"),
        ("polos", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="DefinicaoPolo",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "uuid",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        unique=True,
                    ),
                ),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                ("atualizado_em", models.DateTimeField(auto_now=True)),
                ("ativo", models.BooleanField(default=True)),
                (
                    "tipo",
                    models.CharField(
                        choices=[
                            ("pendente", "Pendente"),
                            ("oficial", "Polo oficial"),
                            ("reserva", "Polo reserva"),
                        ],
                        default="pendente",
                        max_length=20,
                        verbose_name="Tipo do polo na edição",
                    ),
                ),
                (
                    "projecao_inscritos",
                    models.PositiveIntegerField(
                        verbose_name="Projeção de inscritos"
                    ),
                ),
                (
                    "total_inscritos",
                    models.PositiveIntegerField(
                        editable=False,
                        verbose_name="Total de inscritos",
                    ),
                ),
                (
                    "ponto_focal_nome",
                    models.CharField(
                        blank=True,
                        default="",
                        max_length=255,
                        verbose_name="Nome do ponto focal",
                    ),
                ),
                (
                    "ponto_focal_telefone",
                    models.CharField(
                        blank=True,
                        default="",
                        max_length=30,
                        verbose_name="Telefone do ponto focal",
                    ),
                ),
                (
                    "ponto_focal_email",
                    models.EmailField(
                        blank=True,
                        default="",
                        max_length=254,
                        verbose_name="E-mail do ponto focal",
                    ),
                ),
                (
                    "edicao",
                    models.ForeignKey(
                        on_delete=models.deletion.PROTECT,
                        related_name="definicoes_polos",
                        to="edicoes.edicao",
                        verbose_name="Edição",
                    ),
                ),
                (
                    "polo",
                    models.ForeignKey(
                        on_delete=models.deletion.PROTECT,
                        related_name="definicoes",
                        to="polos.polo",
                        verbose_name="Polo",
                    ),
                ),
            ],
            options={
                "verbose_name": "Definição de Polo",
                "verbose_name_plural": "Definições de Polos",
                "ordering": ("edicao__data_inicio", "polo__nome_polo"),
                "constraints": [
                    models.UniqueConstraint(
                        fields=("polo", "edicao"),
                        name="unica_definicao_polo_edicao",
                    )
                ],
            },
        ),
    ]
