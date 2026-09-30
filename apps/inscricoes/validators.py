"""Regras de negócio compartilhadas do domínio de inscrições."""

from __future__ import annotations

from django.core.exceptions import ValidationError

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
)


def _preenchido(valor: object) -> bool:
    """Trata strings vazias e valores nulos como não preenchidos."""
    return valor is not None and (
        not isinstance(valor, str) or bool(valor.strip())
    )


def inscricao_eh_completa(inscricao: object) -> bool:
    """Aplica a regra de completude da primeira fase."""
    if any(
        not _preenchido(getattr(inscricao, campo, None))
        for campo in CAMPOS_COMPLETUDE
    ):
        return False
    tipo = getattr(inscricao, "tipo_estudante", "")
    campo_condicional = (
        "codigo_eol" if tipo == TipoEstudante.ESTUDANTE_DA_REDE else "cpf"
    )
    return _preenchido(getattr(inscricao, campo_condicional, None))


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


def validar_inscricao(inscricao: object) -> None:
    """Executa todas as validações de domínio da inscrição."""
    erros: dict[str, list[str]] = {}
    for validador in (
        validar_tipo_e_grupo,
        validar_polo_e_dre,
        validar_unicidade,
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
