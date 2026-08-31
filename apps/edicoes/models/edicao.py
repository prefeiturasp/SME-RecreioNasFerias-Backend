"""Modelo persistido do domínio de edições."""

from __future__ import annotations

from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.core.models.modelo_base import ModeloAtualizavel
from apps.edicoes.constants import StatusEdicao
from apps.edicoes.validators import validar_edicao


class Edicao(ModeloAtualizavel):
    """Representa uma edição do programa Recreio nas Férias.

    A entidade armazena os períodos da edição e das inscrições, indicadores
    consolidados de outros domínios e o status do seu ciclo de vida.
    """

    nome = models.CharField(
        max_length=255,
        unique=True,
        verbose_name="Nome da edição",
        help_text=(
            "Nome que identifica a edição. Não pode se repetir entre edições."
        ),
    )

    data_inicio = models.DateField(
        verbose_name="Início do período da edição"
    )
    data_fim = models.DateField(verbose_name="Fim do período da edição")

    inscricoes_inicio = models.DateField(
        verbose_name="Início do período de inscrições"
    )
    inscricoes_fim = models.DateField(
        verbose_name="Fim do período de inscrições"
    )

    # Os quatro campos abaixo são consolidações somente-leitura vindas de
    # outros domínios (inscrições, aferições/atendimento e atividades).
    # Por ora ficam com valor 0 por padrão; a atualização automática desses
    # valores será implementada quando os domínios correspondentes existirem
    quantidade_inscritos = models.PositiveIntegerField(
        default=0,
        editable=False,
        verbose_name="Quantidade de inscritos",
        help_text="Consolidação das inscrições realizadas no sistema.",
    )
    quantidade_atendimento_efetivo = models.PositiveIntegerField(
        default=0,
        editable=False,
        verbose_name="Quantidade de atendimento efetivo",
        help_text="Consolidação das aferições cadastradas no sistema.",
    )
    quantidade_passeios = models.PositiveIntegerField(
        default=0,
        editable=False,
        verbose_name="Quantidade de passeios",
        help_text='Quantidade de atividades com a categoria "Passeio".',
    )
    quantidade_apresentacoes = models.PositiveIntegerField(
        default=0,
        editable=False,
        verbose_name="Quantidade de apresentações",
        help_text='Quantidade de atividades com a categoria "Apresentação".',
    )
    status = models.CharField(
        max_length=20,
        choices=StatusEdicao.choices,
        default=StatusEdicao.PLANEJADA,
        verbose_name="Status",
    )

    class Meta:
        """Metadados e ordenação padrão das edições."""

        app_label = "edicoes"
        ordering = ("data_inicio", "nome")
        verbose_name = "Edição"
        verbose_name_plural = "Edições"
        constraints = (
            models.UniqueConstraint(
                fields=("status",),
                condition=Q(status=StatusEdicao.ATIVA),
                name="unica_edicao_ativa",
            ),
        )

    def __str__(self) -> str:
        """Retorna o nome da edição."""
        return self.nome

    def atualizar_status_automatico(self) -> None:
        """Calcula o status com base no período inclusivo da edição."""
        hoje = timezone.localdate()
        if hoje < self.data_inicio:
            self.status = StatusEdicao.PLANEJADA
        elif hoje <= self.data_fim:
            self.status = StatusEdicao.ATIVA
        else:
            self.status = StatusEdicao.ENCERRADA

    def clean(self) -> None:
        """Executa as validações compartilhadas do domínio."""
        super().clean()
        validar_edicao(self)

    def save(self, *args: object, **kwargs: object) -> None:
        """Atualiza o status e valida a edição antes de persistir."""
        self.atualizar_status_automatico()
        # As regras de negócio são executadas em `validators.py`. As
        # constraints do banco continuam protegendo concorrência, mas não
        # devem substituir as mensagens amigáveis do domínio na API.
        self.full_clean(validate_constraints=False)
        super().save(*args, **kwargs)
