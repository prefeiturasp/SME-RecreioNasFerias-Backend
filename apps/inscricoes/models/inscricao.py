"""Entidade persistida da inscrição de um participante."""

from __future__ import annotations

from django.db import models

from apps.core.models.modelo_base import ModeloAtualizavel
from apps.inscricoes.constants import (
    GrupoInscricao,
    StatusInscricao,
    TipoEstudante,
)
from apps.inscricoes.validators import validar_inscricao


class Inscricao(ModeloAtualizavel):
    """Cadastro completo, evolutivo, de um participante."""

    edicao = models.ForeignKey(
        "edicoes.Edicao",
        on_delete=models.PROTECT,
        related_name="inscricoes",
        null=True,
        blank=True,
        verbose_name="Edição",
    )
    polo = models.ForeignKey(
        "polos.Polo",
        on_delete=models.PROTECT,
        related_name="inscricoes",
        null=True,
        blank=True,
        verbose_name="Polo de inscrição",
    )
    tipo_estudante = models.CharField(
        max_length=30,
        choices=TipoEstudante.choices,
        blank=True,
        default="",
        verbose_name="Tipo de estudante",
    )
    grupo = models.CharField(
        max_length=30,
        choices=GrupoInscricao.choices,
        blank=True,
        default="",
        verbose_name="Grupo",
    )
    codigo_eol = models.CharField(
        max_length=50, blank=True, default="", verbose_name="Código EOL"
    )
    cpf = models.CharField(
        max_length=14, blank=True, default="", verbose_name="CPF"
    )
    nome_participante = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Nome do participante",
    )
    data_nascimento = models.DateField(
        null=True, blank=True, verbose_name="Data de nascimento"
    )
    responsavel_nome = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Nome do responsável",
    )
    responsavel_nome_social = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Nome social do responsável",
    )
    cep = models.CharField(
        max_length=9, blank=True, default="", verbose_name="CEP"
    )
    tipo_logradouro = models.CharField(
        max_length=100,
        verbose_name="Tipo de logradouro",
        blank=True,
        default="",
    )
    logradouro = models.CharField(
        max_length=255, blank=True, default="", verbose_name="Logradouro"
    )
    numero = models.CharField(
        max_length=20, blank=True, default="", verbose_name="Número"
    )
    complemento = models.CharField(
        max_length=255, blank=True, default="", verbose_name="Complemento"
    )
    bairro = models.CharField(
        max_length=255, blank=True, default="", verbose_name="Bairro"
    )
    cidade = models.CharField(
        max_length=255, blank=True, default="", verbose_name="Cidade"
    )
    telefone_contato_1 = models.CharField(
        max_length=30,
        blank=True,
        default="",
        verbose_name="Telefone de contato 1",
    )
    telefone_contato_2 = models.CharField(
        max_length=30,
        blank=True,
        default="",
        verbose_name="Telefone de contato 2",
    )
    email = models.EmailField(
        max_length=254, blank=True, default="", verbose_name="E-mail"
    )
    dre_codigo_eol = models.CharField(
        max_length=50, blank=True, default="", verbose_name="Código EOL da DRE"
    )
    dre_nome = models.CharField(
        max_length=255, blank=True, default="", verbose_name="Nome da DRE"
    )
    status = models.CharField(
        max_length=20,
        choices=StatusInscricao.choices,
        default=StatusInscricao.RASCUNHO,
        verbose_name="Status",
    )

    class Meta:
        """Metadados da inscrição."""

        app_label = "inscricoes"
        ordering = ("-criado_em",)
        verbose_name = "Inscrição"
        verbose_name_plural = "Inscrições"

    def __str__(self) -> str:
        """Retorna o nome do participante ou o identificador público."""
        return self.nome_participante or str(self.uuid)

    @property
    def pode_ser_completa(self) -> bool:
        """Indica se todos os campos exigidos da fase estão preenchidos."""
        from apps.inscricoes.validators import inscricao_eh_completa

        return inscricao_eh_completa(self)

    def clean(self) -> None:
        """Executa as validações compartilhadas do domínio."""
        super().clean()
        validar_inscricao(self)

    def save(self, *args: object, **kwargs: object) -> None:
        """Valida e deriva o status, preservando cancelamentos explícitos."""
        if self.status != StatusInscricao.CANCELADA:
            self.status = (
                StatusInscricao.COMPLETA
                if self.pode_ser_completa
                else StatusInscricao.RASCUNHO
            )
        self.full_clean(validate_constraints=False)
        super().save(*args, **kwargs)
