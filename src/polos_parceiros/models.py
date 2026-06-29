"""
Modelos de dados do app de polos parceiros.

Armazena os polos parceiros cadastrados no programa, incluindo informações
gerais, endereço, contato e observações.
"""

import uuid

from common.models import ModeloBase
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from django.db import models

TIPO_POLO_PARCEIRO = "Parceiro"
STATUS_ATIVO = "ativo"
STATUS_INATIVO = "inativo"
STATUS_POLO_PARCEIRO_CHOICES = (
    (STATUS_ATIVO, "ativo"),
    (STATUS_INATIVO, "inativo"),
)


class PoloParceiro(ModeloBase):
    """Representa um polo parceiro vinculado a uma OSC.

    O modelo valida unicidade de nome do polo e campos obrigatórios para
    impedir cadastros duplicados ou incompletos.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tipo = models.CharField(
        "tipo",
        max_length=50,
        default=TIPO_POLO_PARCEIRO,
        editable=False,
    )
    nome_osc = models.CharField("nome da OSC", max_length=255)
    nome_polo = models.CharField("nome do polo", max_length=255, unique=True)
    dre = models.CharField("DRE", max_length=255)
    tipo_ue = models.CharField("tipo de UE", max_length=255)
    quantidade_maxima_alunos = models.PositiveIntegerField(
        "quantidade máxima de alunos",
    )
    cep = models.CharField("CEP", max_length=9)
    endereco = models.CharField("endereço", max_length=500)
    nome_gestor = models.CharField("nome do gestor", max_length=255)
    email_polo = models.EmailField("e-mail do polo", max_length=255)
    telefone_polo = models.CharField("telefone do polo", max_length=20)
    status = models.CharField(
        "status",
        max_length=10,
        choices=STATUS_POLO_PARCEIRO_CHOICES,
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
        """Mapeamento ORM para tabela ``polos_parceiros``."""

        db_table = "polos_parceiros"
        verbose_name = "polo parceiro"
        verbose_name_plural = "polos parceiros"

    def __str__(self) -> str:
        """Retorna representação textual amigável do polo parceiro.

        Returns:
            str: Nome do polo para exibição em listagens e logs.
        """
        return self.nome_polo

    def clean(self) -> None:
        """Valida regras de negócio antes da persistência do polo parceiro.

        Garante que não exista outro polo com o mesmo nome e valida campos
        obrigatórios e formato de e-mail.

        Args:
            Não recebe argumentos explícitos; usa os atributos da instância.

        Returns:
            None: Método de validação sem retorno explícito.

        Raises:
            ValidationError: Quando o nome já existe ou campos são inválidos.
        """
        super().clean()
        erros: dict[str, str] = {}

        self.tipo = TIPO_POLO_PARCEIRO

        if not self.pk:
            self.status = STATUS_ATIVO
        elif self.status not in {STATUS_ATIVO, STATUS_INATIVO}:
            erros["status"] = "Erro: o status deve ser ativo ou inativo"

        nome_polo_normalizado = (self.nome_polo or "").strip()
        if nome_polo_normalizado:
            consulta_nome = type(self).objects.filter(
                nome_polo__iexact=nome_polo_normalizado,
            )
            if self.pk:
                consulta_nome = consulta_nome.exclude(pk=self.pk)
            if consulta_nome.exists():
                erros["nome_polo"] = (
                    "Erro: já existe polo parceiro com o nome cadastrado"
                )

        campos_obrigatorios = {
            "nome_osc": "nome da OSC",
            "nome_polo": "nome do polo",
            "dre": "DRE",
            "tipo_ue": "tipo de UE",
            "cep": "CEP",
            "endereco": "endereço",
            "nome_gestor": "nome do gestor",
            "email_polo": "e-mail do polo",
            "telefone_polo": "telefone do polo",
        }
        for campo, rotulo in campos_obrigatorios.items():
            valor = getattr(self, campo, None)
            if not str(valor or "").strip():
                erros[campo] = f"Erro: o campo {rotulo} é obrigatório"

        if self.quantidade_maxima_alunos is None or self.quantidade_maxima_alunos <= 0:
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
        """Persistir o polo parceiro garantindo execução das validações de domínio.

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
