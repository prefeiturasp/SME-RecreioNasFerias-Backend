"""Modelo da participação de um polo em uma edição."""

from __future__ import annotations

from django.db import models

from apps.core.models.modelo_base import ModeloAtualizavel
from apps.definicoes_polos.constants import (
    PERCENTUAL_ACRESCIMO_CAPACIDADE_REAL,
    TipoPolo,
)
from apps.definicoes_polos.validators import validar_definicao_polo


class DefinicaoPolo(ModeloAtualizavel):
    """Dados específicos de um polo participante de uma edição."""

    polo = models.ForeignKey(
        "polos.Polo",
        on_delete=models.PROTECT,
        related_name="definicoes",
        verbose_name="Polo",
    )
    edicao = models.ForeignKey(
        "edicoes.Edicao",
        on_delete=models.PROTECT,
        related_name="definicoes_polos",
        verbose_name="Edição",
    )
    tipo = models.CharField(
        max_length=20,
        choices=TipoPolo.choices,
        default=TipoPolo.PENDENTE,
        verbose_name="Tipo do polo na edição",
    )
    projecao_inscritos = models.PositiveIntegerField(
        verbose_name="Projeção de inscritos"
    )
    total_inscritos = models.PositiveIntegerField(
        editable=False,
        verbose_name="Total de inscritos",
    )
    ponto_focal_nome = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Nome do ponto focal",
    )
    ponto_focal_telefone = models.CharField(
        max_length=30,
        blank=True,
        default="",
        verbose_name="Telefone do ponto focal",
    )
    ponto_focal_email = models.EmailField(
        max_length=254,
        blank=True,
        default="",
        verbose_name="E-mail do ponto focal",
    )

    class Meta:
        """Metadados e restrições da participação."""

        app_label = "definicoes_polos"
        ordering = ("edicao__data_inicio", "polo__nome_polo")
        verbose_name = "Definição de Polo"
        verbose_name_plural = "Definições de Polos"
        constraints = (
            models.UniqueConstraint(
                fields=("polo", "edicao"),
                name="unica_definicao_polo_edicao",
            ),
        )

    def __str__(self) -> str:
        """Retorna uma descrição da participação."""
        return f"{self.polo} - {self.edicao}"

    def _calcular_total_inscritos(self) -> int:
        """Calcula o total com acréscimo de 30%, arredondando para baixo."""
        percentual = 100 + PERCENTUAL_ACRESCIMO_CAPACIDADE_REAL
        return (self.projecao_inscritos * percentual) // 100

    def clean(self) -> None:
        """Executa as validações compartilhadas do domínio."""
        super().clean()
        validar_definicao_polo(self)

    def save(self, *args: object, **kwargs: object) -> None:
        """Recalcula o total antes de validar e persistir."""
        self.total_inscritos = self._calcular_total_inscritos()
        self.full_clean(validate_constraints=False)
        super().save(*args, **kwargs)
