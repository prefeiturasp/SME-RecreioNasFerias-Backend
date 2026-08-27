"""Modelo persistido do domínio de polos."""

from __future__ import annotations

from django.db import models

from apps.core.models.modelo_base import ModeloAtualizavel
from django.core.validators import MinLengthValidator
from apps.polos.constants import GestaoPolo, StatusPolo, TipoPolo
from apps.polos.validators import validar_polo


class Polo(ModeloAtualizavel):
    """Unidade da Rede Municipal de Ensino que abriga uma edição."""

    codigo_eol = models.CharField(
        max_length=7,
        validators=[MinLengthValidator(6)],
        unique=True,
        verbose_name="Código EOL",
    )
    nome_polo = models.CharField(
        max_length=255, unique=True, verbose_name="Nome do polo"
    )
    nome_osc = models.CharField(max_length=255, verbose_name="Nome da OSC")
    dre_nome = models.CharField(max_length=255, verbose_name="Nome da DRE")
    dre_codigo_eol = models.CharField(
        max_length=50, db_index=True, verbose_name="Código EOL da DRE"
    )
    tipo = models.CharField(
        max_length=20,
        choices=TipoPolo.choices,
        default=TipoPolo.PENDENTE,
        verbose_name="Tipo",
    )
    status = models.CharField(
        max_length=20,
        choices=StatusPolo.choices,
        default=StatusPolo.ATIVO,
        verbose_name="Status",
    )
    gestao = models.CharField(
        max_length=20,
        choices=GestaoPolo.choices,
        default=GestaoPolo.PARCEIRA,
        verbose_name="Gestão",
    )
    tipo_ue = models.CharField(
        max_length=100, db_index=True, verbose_name="Tipo de UE"
    )
    quantidade_maxima_alunos = models.PositiveIntegerField(
        verbose_name="Quantidade máxima de alunos"
    )
    cep = models.CharField(
        max_length=9, verbose_name="CEP", blank=True, default=""
    )
    tipo_logradouro = models.CharField(
        max_length=100,
        verbose_name="Tipo de logradouro",
        blank=True,
        default="",
    )
    logradouro = models.CharField(
        max_length=255, verbose_name="Logradouro", blank=True, default=""
    )
    bairro = models.CharField(
        max_length=255, verbose_name="Bairro", blank=True, default=""
    )
    numero = models.CharField(
        max_length=20, verbose_name="Número", blank=True, default=""
    )
    complemento = models.CharField(
        max_length=255, verbose_name="Complemento", blank=True, default=""
    )
    nome_gestor = models.CharField(
        max_length=255, verbose_name="Nome do gestor", blank=True, default=""
    )
    email = models.EmailField(
        max_length=254, verbose_name="E-mail", blank=True, default=""
    )
    telefone = models.CharField(
        max_length=30, verbose_name="Telefone", blank=True, default=""
    )
    observacoes_gerais = models.TextField(
        blank=True,
        default="",
        verbose_name="Observações gerais",
    )

    class Meta:
        """Metadados e ordenação padrão dos polos."""

        app_label = "polos"
        ordering = ("nome_polo",)
        verbose_name = "Polo"
        verbose_name_plural = "Polos"

    def __str__(self) -> str:
        """Retorna o nome do polo."""
        return self.nome_polo

    def clean(self) -> None:
        """Executa as validações compartilhadas do domínio."""
        super().clean()
        validar_polo(self)

    def save(self, *args: object, **kwargs: object) -> None:
        """Valida o polo antes de persistir."""
        if not self.pk:
            self.tipo = TipoPolo.PENDENTE
            self.status = StatusPolo.ATIVO
        self.full_clean(validate_constraints=False)
        super().save(*args, **kwargs)
