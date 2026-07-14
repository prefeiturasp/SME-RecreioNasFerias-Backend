"""
Modelos de dados do app de polos.

Armazena polos cadastrados manualmente (gestão Parceira) e polos obtidos por
integração (gestão Direta), incluindo informações gerais, endereço, contato
e observações.
"""

import uuid

from common.models import ModeloBase
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from django.db import models

TIPO_POLO_PENDENTE = "Pendente"
TIPO_POLO_OFICIAL = "Polo oficial"
TIPO_POLO_RESERVA = "Polo reserva"
TIPO_POLO_CHOICES = (
    (TIPO_POLO_PENDENTE, "Pendente"),
    (TIPO_POLO_OFICIAL, "Polo oficial"),
    (TIPO_POLO_RESERVA, "Polo reserva"),
)
# Alias mantido para compatibilidade com imports existentes.
TIPO_POLO_PARCEIRO = TIPO_POLO_PENDENTE
TIPO_POLO_DIRETO = TIPO_POLO_PENDENTE
GESTAO_PARCEIRA = "Parceira"
GESTAO_DIRETA = "Direta"
GESTAO_POLO_CHOICES = (
    (GESTAO_PARCEIRA, "Parceira"),
    (GESTAO_DIRETA, "Direta"),
)
STATUS_ATIVO = "ativo"
STATUS_INATIVO = "inativo"
STATUS_POLO_CHOICES = (
    (STATUS_ATIVO, "ativo"),
    (STATUS_INATIVO, "inativo"),
)
# Alias mantido para compatibilidade com imports existentes.
STATUS_POLO_PARCEIRO_CHOICES = STATUS_POLO_CHOICES

QUANTIDADE_MAXIMA_ALUNOS_PADRAO_DIRETA = 1
NOME_EDICAO_SEM_VINCULO = "-"
CHAVE_SINCRONIZACAO_UNIDADES_DIRETAS = "unidades_diretas"


class Polo(ModeloBase):
    """Representa um polo cadastrado manualmente ou obtido por integração.

    O modelo valida unicidade de nome do polo e campos obrigatórios para
    impedir cadastros duplicados ou incompletos. O campo ``gestao`` distingue
    a origem: ``Parceira`` (cadastro manual) ou ``Direta`` (integração).
    Polos de gestão Direta são identificados pelo ``codigo_eol``.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tipo = models.CharField(
        "tipo",
        max_length=50,
        choices=TIPO_POLO_CHOICES,
        default=TIPO_POLO_PENDENTE,
        error_messages={
            "invalid_choice": (
                "Erro: o tipo deve ser Pendente, Polo oficial ou Polo reserva"
            ),
        },
    )
    gestao = models.CharField(
        "gestão",
        max_length=20,
        choices=GESTAO_POLO_CHOICES,
        default=GESTAO_PARCEIRA,
        error_messages={
            "invalid_choice": "Erro: a gestão deve ser Parceira ou Direta",
        },
    )
    codigo_eol = models.CharField(
        "código EOL",
        max_length=20,
        unique=True,
        null=True,
        blank=True,
    )
    nome_osc = models.CharField("nome da OSC", max_length=255, blank=True, default="")
    nome_polo = models.CharField("nome do polo", max_length=255, unique=True)
    dre = models.CharField("DRE", max_length=255)
    tipo_ue = models.CharField("tipo de UE", max_length=255)
    quantidade_maxima_alunos = models.PositiveIntegerField(
        "quantidade máxima de alunos",
    )
    cep = models.CharField("CEP", max_length=9, blank=True, default="")
    endereco = models.CharField("endereço", max_length=500, blank=True, default="")
    nome_gestor = models.CharField(
        "nome do gestor",
        max_length=255,
        blank=True,
        default="",
    )
    email_polo = models.EmailField(
        "e-mail do polo",
        max_length=255,
        blank=True,
        default="",
    )
    telefone_polo = models.CharField(
        "telefone do polo",
        max_length=20,
        blank=True,
        default="",
    )
    nome_edicao = models.CharField(
        "nome da edição",
        max_length=255,
        blank=True,
        default=NOME_EDICAO_SEM_VINCULO,
    )
    status = models.CharField(
        "status",
        max_length=10,
        choices=STATUS_POLO_CHOICES,
        default=STATUS_ATIVO,
        error_messages={
            "invalid_choice": "Erro: o status deve ser ativo ou inativo",
        },
    )
    observacoes_gerais = models.TextField(
        "observações gerais",
        blank=True,
        default="",
    )

    class Meta(ModeloBase.Meta):
        """Mapeamento ORM para tabela ``polos``."""

        db_table = "polos"
        verbose_name = "polo"
        verbose_name_plural = "polos"

    def __str__(self) -> str:
        """Retorna representação textual amigável do polo.

        Returns:
            str: Nome do polo para exibição em listagens e logs.
        """
        return self.nome_polo

    def clean(self) -> None:
        """Valida regras de negócio antes da persistência do polo.

        Garante unicidade de nome e código EOL, e aplica obrigatoriedade
        conforme a gestão (Parceira exige mais campos que Direta).

        Raises:
            ValidationError: Quando o nome/EOL já existe ou campos são inválidos.
        """
        super().clean()
        erros: dict[str, str] = {}

        tipo_normalizado = (self.tipo or "").strip()
        if not tipo_normalizado:
            self.tipo = TIPO_POLO_PENDENTE
        elif tipo_normalizado not in {
            TIPO_POLO_PENDENTE,
            TIPO_POLO_OFICIAL,
            TIPO_POLO_RESERVA,
        }:
            erros["tipo"] = (
                "Erro: o tipo deve ser Pendente, Polo oficial ou Polo reserva"
            )
        else:
            self.tipo = tipo_normalizado

        if self.gestao not in {GESTAO_PARCEIRA, GESTAO_DIRETA}:
            erros["gestao"] = "Erro: a gestão deve ser Parceira ou Direta"

        if not self.pk:
            self.status = STATUS_ATIVO
        elif self.status not in {STATUS_ATIVO, STATUS_INATIVO}:
            erros["status"] = "Erro: o status deve ser ativo ou inativo"

        codigo_eol_normalizado = (self.codigo_eol or "").strip()
        self.codigo_eol = codigo_eol_normalizado or None

        if self.gestao == GESTAO_DIRETA and not self.codigo_eol:
            erros["codigo_eol"] = (
                "Erro: o código EOL é obrigatório para polos de gestão Direta"
            )
        elif self.codigo_eol:
            consulta_eol = type(self).objects.filter(codigo_eol=self.codigo_eol)
            if self.pk:
                consulta_eol = consulta_eol.exclude(pk=self.pk)
            if consulta_eol.exists():
                erros["codigo_eol"] = (
                    "Erro: já existe polo com o código EOL cadastrado"
                )

        nome_polo_normalizado = (self.nome_polo or "").strip()
        if nome_polo_normalizado:
            consulta_nome = type(self).objects.filter(
                nome_polo__iexact=nome_polo_normalizado,
            )
            if self.pk:
                consulta_nome = consulta_nome.exclude(pk=self.pk)
            if consulta_nome.exists():
                erros["nome_polo"] = "Erro: já existe polo com o nome cadastrado"

        campos_obrigatorios = {
            "nome_polo": "nome do polo",
            "dre": "DRE",
            "tipo_ue": "tipo de UE",
        }
        if self.gestao == GESTAO_PARCEIRA:
            campos_obrigatorios.update(
                {
                    "nome_osc": "nome da OSC",
                    "cep": "CEP",
                    "endereco": "endereço",
                    "nome_gestor": "nome do gestor",
                    "email_polo": "e-mail do polo",
                    "telefone_polo": "telefone do polo",
                },
            )

        for campo, rotulo in campos_obrigatorios.items():
            valor = getattr(self, campo, None)
            if not str(valor or "").strip():
                erros[campo] = f"Erro: o campo {rotulo} é obrigatório"

        if self.gestao == GESTAO_DIRETA:
            if self.quantidade_maxima_alunos is None:
                self.quantidade_maxima_alunos = QUANTIDADE_MAXIMA_ALUNOS_PADRAO_DIRETA
            elif self.quantidade_maxima_alunos <= 0:
                erros["quantidade_maxima_alunos"] = (
                    "Erro: a quantidade máxima de alunos deve ser maior que zero"
                )
        elif (
            self.quantidade_maxima_alunos is None
            or self.quantidade_maxima_alunos <= 0
        ):
            erros["quantidade_maxima_alunos"] = (
                "Erro: a quantidade máxima de alunos deve ser maior que zero"
            )

        email = (self.email_polo or "").strip()
        if email:
            validador_email = EmailValidator(
                message="Erro: informe um e-mail válido para o polo",
            )
            try:
                validador_email(email)
            except ValidationError:
                erros["email_polo"] = "Erro: informe um e-mail válido para o polo"

        if erros:
            raise ValidationError(erros)

    def save(self, *args: object, **kwargs: object) -> None:
        """Persistir o polo garantindo execução das validações de domínio.

        Args:
            *args: Argumentos posicionais aceitos por ``models.Model.save``.
            **kwargs: Argumentos nomeados aceitos por ``models.Model.save``.

        Raises:
            ValidationError: Propagada quando ``full_clean`` detecta dados inválidos.
        """
        self.full_clean()
        super().save(*args, **kwargs)


class ControleSincronizacaoPolos(models.Model):
    """Registra a última execução bem-sucedida de sincronizações de polos.

    Usado para limitar a frequência (ex.: uma vez por dia) sem reconsultar a
    SME Integração quando a carga do dia já ocorreu.
    """

    chave = models.CharField(
        "chave",
        max_length=64,
        primary_key=True,
    )
    ultima_execucao_em = models.DateTimeField("última execução")

    class Meta:
        """Mapeamento ORM para tabela de controle de sincronização."""

        db_table = "polos_controle_sincronizacao"
        verbose_name = "controle de sincronização de polos"
        verbose_name_plural = "controles de sincronização de polos"

    def __str__(self) -> str:
        """Retorna a chave e o instante da última execução."""
        return f"{self.chave} @ {self.ultima_execucao_em.isoformat()}"
