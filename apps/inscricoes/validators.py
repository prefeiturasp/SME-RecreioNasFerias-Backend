"""Regras de negócio compartilhadas do domínio de inscrições."""

from __future__ import annotations

from datetime import date

from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.definicoes_polos.constants import TipoPolo
from apps.definicoes_polos.models import DefinicaoPolo
from apps.inscricoes.constants import GrupoInscricao, TipoEstudante
from apps.polos.constants import StatusPolo

MENSAGEM_DUPLICIDADE = (
    "Já existe inscrição com o identificador informado neste polo."
)
MENSAGEM_GRUPO_REDE = "Berçário e Mini Grupo exigem estudante da rede."
MENSAGEM_POLO_INVALIDO = (
    "O polo deve estar ativo e ter sido oficial ao menos uma vez."
)
MENSAGEM_DRE_POLO = "O polo selecionado não pertence à DRE informada."
MENSAGEM_CODIGO_EOL_OBRIGATORIO = "Informe o código EOL."
MENSAGEM_EOL_NAO_ENCONTRADO = (
    "Código EOL não encontrado. Verifique o número digitado e tente novamente."
)
MENSAGEM_CPF_OBRIGATORIO = "Informe o CPF do responsável."
MENSAGEM_CPF_NAO_ENCONTRADO = (
    "CPF não encontrado. Verifique o número digitado e tente novamente."
)

CAMPOS_COMPLETUDE = (
    "tipo_estudante",
    "grupo",
    "nome_participante",
    "data_nascimento",
    "responsavel_nome",
    "cep",
    "tipo_logradouro",
    "logradouro",
    "numero",
    "bairro",
    "cidade",
    "telefone_contato_1",
    "email",
    "dre_codigo_eol",
    "dre_nome",
    "polo_id",
    "possui_deficiencia",
    "possui_problema_saude",
    "usuario_medicacao_ou_tratamento_continuo",
    "possui_restricao_medicamento_pronto_atendimento",
    "possui_convenio_medico"
)

CAMPOS_GRUPO_REDE = (
    "unidade_educacional",
    "unidade_educacional_codigo_eol",
    "unidade_educacional_tipo",
    "pode_ir_embora_sozinho",
    "autoriza_uso_piscina",
    "responsavel_retirada",
)


def _preenchido(valor: object) -> bool:
    """Trata strings vazias e valores nulos como não preenchidos."""
    return valor is not None and (
        not isinstance(valor, str) or bool(valor.strip())
    )


def inscricao_eh_completa(inscricao: object) -> bool:
    """Aplica a régua da fase e, na rede, unidade, saída e piscina."""
    if any(
        not _preenchido(getattr(inscricao, campo, None))
        for campo in CAMPOS_COMPLETUDE
    ):
        return False
    tipo = getattr(inscricao, "tipo_estudante", "")
    campo_condicional = (
        "codigo_eol" if tipo == TipoEstudante.ESTUDANTE_DA_REDE else "cpf"
    )
    if not _preenchido(getattr(inscricao, campo_condicional, None)):
        return False
    if tipo != TipoEstudante.ESTUDANTE_DA_REDE:
        return True
    return all(
        _preenchido(getattr(inscricao, campo, None))
        for campo in CAMPOS_GRUPO_REDE
    )


def calcular_idade_cheia(data_nascimento: date | None) -> int | None:
    """Devolve a idade em anos completos na data local de hoje.

    Sem data de nascimento, devolve ``None``. Em 29 de fevereiro, num
    ano que não é bissexto, o aniversário vale 1º de março.
    """
    if data_nascimento is None:
        return None
    hoje = timezone.localdate()
    idade = hoje.year - data_nascimento.year
    if hoje < _aniversario(data_nascimento, hoje.year):
        idade -= 1
    return idade


def _aniversario(nascimento: date, ano: int) -> date:
    """Monta o aniversário no ano pedido, tratando 29 de fevereiro."""
    try:
        return date(ano, nascimento.month, nascimento.day)
    except ValueError:
        return date(ano, 3, 1)


def validar_tipo_e_grupo(inscricao: object) -> None:
    """Impede grupos de educação infantil para estudantes externos."""
    grupo = getattr(inscricao, "grupo", "")
    tipo = getattr(inscricao, "tipo_estudante", "")
    grupos_rede = {
        GrupoInscricao.BERCARIO_I,
        GrupoInscricao.BERCARIO_II,
        GrupoInscricao.MINI_GRUPO_I,
        GrupoInscricao.MINI_GRUPO_II,
    }
    if (
        grupo in grupos_rede
        and tipo
        and tipo != TipoEstudante.ESTUDANTE_DA_REDE
    ):
        raise ValidationError({"tipo_estudante": MENSAGEM_GRUPO_REDE})


def validar_polo_e_dre(inscricao: object) -> None:
    """Valida elegibilidade atual do polo e a coerência com a DRE."""
    polo = getattr(inscricao, "polo", None)
    if polo is None:
        return
    if (
        polo.status != StatusPolo.ATIVO
        or not DefinicaoPolo.objects.filter(
            polo_id=polo.pk, tipo=TipoPolo.OFICIAL
        ).exists()
    ):
        raise ValidationError({"polo": MENSAGEM_POLO_INVALIDO})
    dre = getattr(inscricao, "dre_codigo_eol", "")
    if dre and dre.strip() != polo.dre_codigo_eol.strip():
        raise ValidationError({"dre_codigo_eol": MENSAGEM_DRE_POLO})


def validar_unicidade(inscricao: object) -> None:
    """Evita duplicidade por CPF e Código EOL dentro do mesmo polo."""
    polo_id = getattr(inscricao, "polo_id", None)
    if not polo_id:
        return
    consulta = type(inscricao).objects.filter(polo_id=polo_id)
    if getattr(inscricao, "pk", None):
        consulta = consulta.exclude(pk=inscricao.pk)
    erros: dict[str, str] = {}
    for campo in ("cpf", "codigo_eol"):
        valor = (getattr(inscricao, campo, "") or "").strip()
        if valor and consulta.filter(**{campo: valor}).exists():
            erros[campo] = MENSAGEM_DUPLICIDADE
    if erros:
        raise ValidationError(erros)


def validar_informacoes_de_saude(inscricao: object) -> None:
    """Valida as informações de saúde do participante."""
    possui_deficiencia = getattr(inscricao, "possui_deficiencia", True)
    detalhes_deficiencia = getattr(inscricao, "deficiencias", [])
    outra_deficiencia = getattr(inscricao, "outra_deficiencia", "")
    if possui_deficiencia and not detalhes_deficiencia:
        raise ValidationError({"deficiencias": "Informe a(s) deficiência(s)."})
    if "OUTRA" in detalhes_deficiencia and not outra_deficiencia:
        raise ValidationError({"outra_deficiencia": "É obrigatório informar a outra deficiência."})

    # Se o participante tiver algum problema de saúde, deve fornecer detalhes.
    possui_problema_saude = getattr(inscricao, "possui_problema_saude", True)
    detalhes_problema_saude = getattr(inscricao, "problemas_saude", [])
    outro_problema_saude = getattr(inscricao, "outro_problema_saude", "")
    if possui_problema_saude and not detalhes_problema_saude:
        raise ValidationError({"problemas_saude": "Informe o(s) problema(s) de saúde."})
    if "OUTRO" in detalhes_problema_saude and not outro_problema_saude:
        raise ValidationError({"outro_problema_saude": "É obrigatório informar o outro problema de saúde."})

    usuario_medicacao_ou_tratamento = getattr(inscricao, "usuario_medicacao_ou_tratamento_continuo", True)
    detalhe_medicacao_ou_tratamento = getattr(inscricao, "medicacao_ou_tratamento_continuo", "")
    if usuario_medicacao_ou_tratamento and not detalhe_medicacao_ou_tratamento:
        raise ValidationError({"medicacao_ou_tratamento_continuo": "Detalhe da medicação ou tratamento contínuo é obrigatório."})

    possui_restricao_medicamento_pronto_atendimento = getattr(inscricao, "possui_restricao_medicamento_pronto_atendimento", True)
    detalhe_restricao_medicamento_pronto_atendimento = getattr(inscricao, "restricao_medicamento_pronto_atendimento", "")
    if possui_restricao_medicamento_pronto_atendimento and not detalhe_restricao_medicamento_pronto_atendimento:
        raise ValidationError({"restricao_medicamento_pronto_atendimento": "Detalhe da restrição de medicamento no pronto atendimento é obrigatório."})

    possui_convenio_medico = getattr(inscricao, "possui_convenio_medico", True)
    detalhe_convenio_medico = getattr(inscricao, "convenio_medico", "")
    if possui_convenio_medico and not detalhe_convenio_medico:
        raise ValidationError({"convenio_medico": "Detalhe do convênio médico é obrigatório."})




def validar_inscricao(inscricao: object) -> None:
    """Executa todas as validações de domínio da inscrição."""
    erros: dict[str, list[str]] = {}
    for validador in (
        validar_tipo_e_grupo,
        validar_polo_e_dre,
        validar_unicidade,
        validar_informacoes_de_saude,
    ):
        try:
            validador(inscricao)
        except ValidationError as exc:
            mensagens = getattr(exc, "message_dict", {"__all__": exc.messages})
            for campo, valores in mensagens.items():
                erros.setdefault(campo, []).extend(
                    str(valor) for valor in valores
                )
    if erros:
        raise ValidationError(erros)
