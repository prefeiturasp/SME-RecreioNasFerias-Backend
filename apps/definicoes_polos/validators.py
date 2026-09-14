"""Validações do domínio de definições de polos."""

from __future__ import annotations

from django.core.exceptions import ValidationError

MENSAGEM_PARTICIPACAO_DUPLICADA = (
    "Erro: o polo já está vinculado à edição informada."
)
MENSAGEM_PROJECAO_INVALIDA = (
    "Erro: a projeção de inscritos deve ser maior ou igual a zero."
)


def validar_unicidade_polo_edicao(definicao: object) -> None:
    """Impede mais de uma definição para o mesmo polo e edição."""
    consulta = type(definicao).objects.filter(
        polo=getattr(definicao, "polo_id", None),
        edicao=getattr(definicao, "edicao_id", None),
    )
    if getattr(definicao, "pk", None):
        consulta = consulta.exclude(pk=definicao.pk)
    if consulta.exists():
        raise ValidationError({"__all__": MENSAGEM_PARTICIPACAO_DUPLICADA})


def validar_projecao_inscritos(definicao: object) -> None:
    """Valida a projeção antes da validação do campo PositiveIntegerField."""
    valor = getattr(definicao, "projecao_inscritos", None)
    if valor is not None and valor < 0:
        raise ValidationError(
            {"projecao_inscritos": MENSAGEM_PROJECAO_INVALIDA}
        )


def validar_definicao_polo(definicao: object) -> None:
    """Executa as validações compartilhadas do domínio."""
    erros: dict[str, list[str]] = {}
    for validador in (
        validar_unicidade_polo_edicao,
        validar_projecao_inscritos,
    ):
        try:
            validador(definicao)
        except ValidationError as exc:
            mensagens = getattr(exc, "message_dict", {"__all__": exc.messages})
            for campo, valores in mensagens.items():
                erros.setdefault(campo, []).extend(
                    str(valor) for valor in valores
                )
    if erros:
        raise ValidationError(erros)
