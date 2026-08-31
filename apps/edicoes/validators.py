"""Validações centralizadas do domínio de edições.

As funções deste módulo são utilizadas pelo modelo e pelo serviço. O Django
ModelForm/Admin também executa ``model.full_clean()``, reaproveitando as
mesmas regras da API.
"""

from __future__ import annotations

from datetime import date

from django.core.exceptions import ValidationError

from apps.edicoes.constants import StatusEdicao

MENSAGEM_NOME_DUPLICADO = (
    "Erro: já existe edição com o nome cadastrado."
)
MENSAGEM_PERIODO_DUPLICADO = (
    "Erro: já existe edição no período cadastrado."
)
MENSAGEM_EDICAO_ENCERRADA = "Erro: edição encerrada não pode ser alterada."
MENSAGEM_EDICAO_ATIVA_DUPLICADA = "Erro: já existe edição ativa cadastrada."


def _periodos_sobrepostos(
    inicio: date,
    fim: date,
    outro_inicio: date,
    outro_fim: date,
) -> bool:
    """Verifica sobreposição considerando os limites dos períodos."""
    return inicio <= outro_fim and fim >= outro_inicio


def validar_nome_unico(edicao: object) -> None:
    """Impede duas edições com o mesmo nome, independentemente das datas."""
    nome = getattr(edicao, "nome", "")
    consulta = type(edicao).objects.filter(nome__iexact=nome)
    if getattr(edicao, "pk", None):
        consulta = consulta.exclude(pk=edicao.pk)
    if consulta.exists():
        raise ValidationError({"nome": MENSAGEM_NOME_DUPLICADO})


def validar_periodos(edicao: object) -> None:
    """Valida ordem, limite e sobreposição dos períodos da edição."""
    data_inicio = getattr(edicao, "data_inicio", None)
    data_fim = getattr(edicao, "data_fim", None)
    inscricoes_inicio = getattr(edicao, "inscricoes_inicio", None)
    inscricoes_fim = getattr(edicao, "inscricoes_fim", None)
    erros: dict[str, str] = {}

    if data_inicio and data_fim and data_fim < data_inicio:
        erros["data_fim"] = (
            "A data final da edição deve ser posterior à inicial."
        )
    if (
        inscricoes_inicio
        and inscricoes_fim
        and inscricoes_fim < inscricoes_inicio
    ):
        erros["inscricoes_fim"] = (
            "A data final das inscrições deve ser posterior à inicial."
        )
    if data_fim and inscricoes_fim and inscricoes_fim > data_fim:
        erros["inscricoes_fim"] = (
            "As inscrições devem terminar até o último dia da edição."
        )
    if erros:
        raise ValidationError(erros)

    if not all(
        valor is not None
        for valor in (
            data_inicio,
            data_fim,
            inscricoes_inicio,
            inscricoes_fim,
        )
    ):
        return

    consulta = type(edicao).objects.all()
    if getattr(edicao, "pk", None):
        consulta = consulta.exclude(pk=edicao.pk)

    for existente in consulta.only(
        "data_inicio",
        "data_fim",
        "inscricoes_inicio",
        "inscricoes_fim",
    ):
        if _periodos_sobrepostos(
            data_inicio,
            data_fim,
            existente.data_inicio,
            existente.data_fim,
        ) or _periodos_sobrepostos(
            inscricoes_inicio,
            inscricoes_fim,
            existente.inscricoes_inicio,
            existente.inscricoes_fim,
        ):
            raise ValidationError({"__all__": MENSAGEM_PERIODO_DUPLICADO})


def validar_edicao_encerrada(edicao: object) -> None:
    """Impede alterações em registros já encerrados."""
    if not getattr(edicao, "pk", None):
        return

    modelo = type(edicao)
    existente = modelo.objects.filter(pk=edicao.pk).only(
        "nome",
        "data_inicio",
        "data_fim",
        "inscricoes_inicio",
        "inscricoes_fim",
        "quantidade_inscritos",
        "quantidade_atendimento_efetivo",
        "quantidade_passeios",
        "quantidade_apresentacoes",
        "status",
    ).first()
    if existente is None or existente.status != StatusEdicao.ENCERRADA:
        return

    campos = (
        "nome",
        "data_inicio",
        "data_fim",
        "inscricoes_inicio",
        "inscricoes_fim",
        "quantidade_inscritos",
        "quantidade_atendimento_efetivo",
        "quantidade_passeios",
        "quantidade_apresentacoes",
    )
    if any(
        getattr(existente, campo) != getattr(edicao, campo)
        for campo in campos
    ):
        raise ValidationError({"__all__": MENSAGEM_EDICAO_ENCERRADA})


def validar_unicidade_ativa(edicao: object) -> None:
    """Garante que somente uma edição esteja ativa."""
    if getattr(edicao, "status", None) != StatusEdicao.ATIVA:
        return
    consulta = type(edicao).objects.filter(status=StatusEdicao.ATIVA)
    if getattr(edicao, "pk", None):
        consulta = consulta.exclude(pk=edicao.pk)
    if consulta.exists():
        raise ValidationError({"__all__": MENSAGEM_EDICAO_ATIVA_DUPLICADA})


def validar_edicao(edicao: object) -> None:
    """Executa todas as validações de criação e alteração."""
    erros: dict[str, list[str]] = {}
    validadores = (
        validar_edicao_encerrada,
        validar_nome_unico,
        validar_periodos,
        validar_unicidade_ativa,
    )

    for validador in validadores:
        try:
            validador(edicao)
        except ValidationError as exc:
            if hasattr(exc, "message_dict"):
                mensagens = exc.message_dict
            else:
                mensagens = {"__all__": exc.messages}

            for campo, valores in mensagens.items():
                erros.setdefault(campo, []).extend(
                    str(valor) for valor in valores
                )

    if erros:
        raise ValidationError(erros)
