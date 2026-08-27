"""Validações centralizadas do domínio de polos."""

from __future__ import annotations

from django.core.exceptions import ValidationError


MENSAGEM_NOME_DUPLICADO = "Erro: já existe polo com o nome cadastrado."
MENSAGEM_CODIGO_DUPLICADO = (
    "Erro: já existe polo com o código EOL cadastrado."
)
def validar_nome_unico(polo: object) -> None:
    """Impede dois polos com o mesmo nome, sem diferenciar maiúsculas."""
    nome = getattr(polo, "nome_polo", "")
    consulta = type(polo).objects.filter(nome_polo__iexact=nome)
    if getattr(polo, "pk", None):
        consulta = consulta.exclude(pk=polo.pk)
    if consulta.exists():
        raise ValidationError({"nome_polo": MENSAGEM_NOME_DUPLICADO})


def validar_codigo_eol_unico(polo: object) -> None:
    """Impede dois polos com o mesmo código EOL."""
    codigo_eol = getattr(polo, "codigo_eol", "")
    consulta = type(polo).objects.filter(codigo_eol__iexact=codigo_eol)
    if getattr(polo, "pk", None):
        consulta = consulta.exclude(pk=polo.pk)
    if consulta.exists():
        raise ValidationError({"codigo_eol": MENSAGEM_CODIGO_DUPLICADO})


def validar_polo(polo: object) -> None:
    """Executa todas as validações compartilhadas do polo."""
    erros: dict[str, list[str]] = {}
    for validador in (validar_nome_unico, validar_codigo_eol_unico):
        try:
            validador(polo)
        except ValidationError as exc:
            mensagens = getattr(
                exc, "message_dict", {"__all__": exc.messages}
            )
            for campo, valores in mensagens.items():
                erros.setdefault(campo, []).extend(
                    str(valor) for valor in valores
                )
    if erros:
        raise ValidationError(erros)
