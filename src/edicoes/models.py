"""
Modelos de dados do app de edições.

Armazena as edições do programa com períodos de execução e de inscrição,
além de indicadores consolidados de participação e atividades.
"""

import uuid

from common.models import ModeloBase
from django.core.exceptions import ValidationError
from django.db import models


class Edicao(ModeloBase):
    """Representa uma edição do programa com seus períodos oficiais.

    O modelo valida unicidade de nome e período da edição para impedir
    cadastros duplicados e inconsistências operacionais.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField("nome da edição", max_length=255, unique=True)
    periodo_edicao_inicio = models.DateField("período da edição - início")
    periodo_edicao_fim = models.DateField("período da edição - fim")
    periodo_inscricoes_inicio = models.DateField("período das inscrições - início")
    periodo_inscricoes_fim = models.DateField("período das inscrições - fim")
    quantidade_inscritos = models.PositiveIntegerField(
        "quantidade de inscritos",
        blank=True,
        null=True,
        editable=False,
    )
    quantidade_atendimento_efetivo = models.PositiveIntegerField(
        "quantidade de atendimento efetivo",
        blank=True,
        null=True,
        editable=False,
    )
    quantidade_passeios = models.PositiveIntegerField(
        "quantidade de passeios",
        blank=True,
        null=True,
        editable=False,
    )
    quantidade_apresentacoes = models.PositiveIntegerField(
        "quantidade de apresentações",
        blank=True,
        null=True,
        editable=False,
    )

    class Meta(ModeloBase.Meta):
        """Mapeamento ORM para tabela ``edicoes`` e restrições de período.

        A combinação ``(periodo_edicao_inicio, periodo_edicao_fim)`` é única
        para impedir dois registros no mesmo período.
        """

        db_table = "edicoes"
        verbose_name = "edição"
        verbose_name_plural = "edições"
        constraints = [
            models.UniqueConstraint(
                fields=("periodo_edicao_inicio", "periodo_edicao_fim"),
                name="edicoes_periodo_unico",
            )
        ]

    def __str__(self) -> str:
        """Retorna representação textual amigável da edição.

        Returns:
            str: Nome da edição para exibição em listagens e logs.
        """
        return self.nome

    def clean(self) -> None:
        """Valida regras de negócio antes da persistência da edição.

        Garante que não exista outra edição com mesmo nome ou com o mesmo
        período de execução e valida a coerência das faixas de datas.

        Args:
            Não recebe argumentos explícitos; usa os atributos da instância.

        Returns:
            None: Método de validação sem retorno explícito.

        Raises:
            ValidationError: Quando o nome já existe, quando o período já existe
                ou quando a data inicial é maior que a data final.
        """
        super().clean()
        erros: dict[str, str] = {}

        nome_normalizado = (self.nome or "").strip()
        if nome_normalizado:
            consulta_nome = type(self).objects.filter(nome__iexact=nome_normalizado)
            if self.pk:
                consulta_nome = consulta_nome.exclude(pk=self.pk)
            if consulta_nome.exists():
                erros["nome"] = "Erro: já existe edição com o nome cadastrado"

        if self.periodo_edicao_inicio and self.periodo_edicao_fim:
            if self.periodo_edicao_inicio > self.periodo_edicao_fim:
                erros["periodo_edicao"] = (
                    "Erro: a data inicial do período da edição deve ser menor ou "
                    "igual à data final"
                )
            consulta_periodo = type(self).objects.filter(
                periodo_edicao_inicio=self.periodo_edicao_inicio,
                periodo_edicao_fim=self.periodo_edicao_fim,
            )
            if self.pk:
                consulta_periodo = consulta_periodo.exclude(pk=self.pk)
            if consulta_periodo.exists():
                erros["periodo_edicao"] = "Erro: já existe edição no período cadastrado"

        if self.periodo_inscricoes_inicio and self.periodo_inscricoes_fim:
            if self.periodo_inscricoes_inicio > self.periodo_inscricoes_fim:
                erros["periodo_inscricoes"] = (
                    "Erro: a data inicial do período das inscrições deve ser menor "
                    "ou igual à data final"
                )

        if erros:
            raise ValidationError(erros)

    def save(self, *args: object, **kwargs: object) -> None:
        """Persistir a edição garantindo execução das validações de domínio.

        Args:
            *args: Argumentos posicionais aceitos por ``models.Model.save``.
            **kwargs: Argumentos nomeados aceitos por ``models.Model.save``.

        Returns:
            None: Salva a instância no banco sem retorno explícito.

        Raises:
            ValidationError: Propagada quando ``full_clean`` detecta dados inválidos.
        """
        self.full_clean()
        super().save(*args, **kwargs)
