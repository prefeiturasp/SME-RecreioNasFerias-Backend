"""Configuração do domínio no Django Admin."""

from django.contrib import admin
from django import forms

from apps.inscricoes.constants import Deficiencias, ProblemasSaude
from apps.inscricoes.models import Inscricao


class InscricaoAdminForm(forms.ModelForm):
    deficiencias = forms.MultipleChoiceField(
        choices=Deficiencias.choices,
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )
    problemas_saude = forms.MultipleChoiceField(
        choices=ProblemasSaude.choices,
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    class Meta:
        model = Inscricao
        fields = [
            "edicao",
            "polo",
            "tipo_estudante",
            "grupo",
            "codigo_eol",
            "cpf",
            "nome_participante",
            "data_nascimento",
            "responsavel_nome",
            "responsavel_nome_social",
            "cep",
            "tipo_logradouro",
            "logradouro",
            "numero",
            "complemento",
            "bairro",
            "cidade",
            "telefone_contato_1",
            "telefone_contato_2",
            "email",
            "dre_codigo_eol",
            "dre_nome",
            "status",
            "possui_deficiencia",
            "deficiencias",
            "outra_deficiencia",
            "possui_problema_saude",
            "problemas_saude",
            "outro_problema_saude",
            "usuario_medicacao_ou_tratamento_continuo",
            "medicacao_ou_tratamento_continuo",
            "possui_restricao_medicamento_pronto_atendimento",
            "restricao_medicamento_pronto_atendimento",
            "possui_convenio_medico",
            "convenio_medico",
            "unidade_educacional",
            "unidade_educacional_codigo_eol",
            "unidade_educacional_tipo",
            "nome_turma",
            "ano",
            "pode_ir_embora_sozinho",
            "responsavel_retirada",
            "autoriza_uso_piscina",
        ]


@admin.register(Inscricao)
class InscricaoAdmin(admin.ModelAdmin):
    """Apresenta e filtra inscrições."""

    form = InscricaoAdminForm
    list_display = (
        "nome_participante",
        "tipo_estudante",
        "grupo",
        "polo",
        "codigo_eol",
        "cpf",
        "status",
        "ativo",
    )
    list_filter = ("tipo_estudante", "grupo", "status", "ativo")
    search_fields = (
        "nome_participante",
        "codigo_eol",
        "cpf",
        "polo__nome_polo",
    )
    raw_id_fields = ("polo", "edicao")
    readonly_fields = ("uuid", "criado_em", "atualizado_em")
