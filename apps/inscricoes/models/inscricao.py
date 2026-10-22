"""Entidade persistida da inscrição de um participante."""

from __future__ import annotations

from django.contrib.postgres.fields import ArrayField
from django.db import models

from apps.core.models.modelo_base import ModeloAtualizavel
from apps.inscricoes.constants import (
    Deficiencias,
    GrupoInscricao,
    ProblemasSaude,
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

    ## Informações de saúde

    possui_deficiencia = models.BooleanField(
        default=False,
        verbose_name="Possui deficiência?"
    )

    # Tipos de deficiências, caso possui_deficiencia seja True
    deficiencias = ArrayField(
        base_field=models.CharField(
            max_length=50,
            choices=Deficiencias.choices,
        ),
        blank=True,
        default=list,
        verbose_name="Possui deficiência(s)?",
    )

    # Campo de texto livre que só será preenchido se "Outra" for selecionada
    outra_deficiencia = models.CharField(
        max_length=300,
        blank=True,
        verbose_name="Especifique a outra deficiência"
    )

    possui_problema_saude = models.BooleanField(
        default=False,
        verbose_name="Possui problema de saúde?"
    )

    # Tipo de problema de saúde, caso possui_problema_saude seja True
    problemas_saude = ArrayField(
        base_field=models.CharField(
            max_length=50,
            choices=ProblemasSaude.choices,
        ),
        blank=True,
        default=list,
        verbose_name="Possui problema(s) de saúde?",
    )

    # Campo de texto livre que só será preenchido se "Outro" for selecionada
    outro_problema_saude = models.CharField(
        max_length=300,
        blank=True,
        verbose_name="Especifique o outro problema de saúde"
    )

    usuario_medicacao_ou_tratamento_continuo = models.BooleanField(
        default=False,
        verbose_name="Usuário de medicação ou tratamento contínuo?"
    )

    # Campo de texto livre que só será preenchido se "Usuário de medicação ou tratamento contínuo" for marcado
    medicacao_ou_tratamento_continuo = models.CharField(
        max_length=300,
        blank=True,
        verbose_name="Medicação ou tratamento contínuo"
    )

    possui_restricao_medicamento_pronto_atendimento = models.BooleanField(
        default=False,
        verbose_name="Possui restrição de medicamento em pronto atendimento?"
    )

    # Campo de texto livre que só será preenchido se "Possui restrição de medicamento em pronto atendimento" for marcado
    restricao_medicamento_pronto_atendimento = models.CharField(
        max_length=300,
        blank=True,
        verbose_name="Especifique a restrição de medicamento em pronto atendimento"
    )

    possui_convenio_medico = models.BooleanField(
        default=False,
        verbose_name="Possui convênio médico?"
    )

    # Campo de texto livre que só será preenchido se "Possui convênio médico" for marcado
    convenio_medico = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Especifique o convênio médico"
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
