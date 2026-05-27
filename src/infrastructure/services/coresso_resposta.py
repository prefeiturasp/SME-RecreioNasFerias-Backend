"""
Extração de mensagens de erro das respostas HTTP do CoreSSO.

Interpreta corpos JSON (campos ``message``, ``mensagem``, etc.) ou texto plano
retornados pelos endpoints de autenticação e DadosSigpae.
"""

import json
from typing import Any, Protocol


class _RespostaHttpComTexto(Protocol):
    """Contrato mínimo de ``requests.Response`` usado neste módulo.

    Attributes:
        text (str): Corpo bruto da resposta HTTP.
    """

    text: str


_CHAVES_MENSAGEM = (
    "message",
    "mensagem",
    "Message",
    "Mensagem",
    "error",
    "erro",
    "title",
    "detail",
    "Description",
    "description",
)


def _mensagem_em_valor(valor: Any) -> str:
    """Extrai texto legível de um valor JSON (string, lista ou dict aninhado).

    Args:
        valor (Any): Fragmento do JSON de erro do CoreSSO.

    Returns:
        str: Mensagem encontrada ou string vazia.
    """
    if isinstance(valor, str) and valor.strip():
        return valor.strip()
    if isinstance(valor, list) and valor:
        return _mensagem_em_valor(valor[0])
    if isinstance(valor, dict):
        for chave in _CHAVES_MENSAGEM:
            texto = _mensagem_em_valor(valor.get(chave))
            if texto:
                return texto
    return ""


def _mensagem_em_dict(data: dict) -> str:
    """Busca mensagem de erro em um objeto JSON de primeiro nível.

    Args:
        data (dict): Objeto JSON decodificado da resposta HTTP.

    Returns:
        str: Mensagem encontrada ou string vazia.
    """
    for chave in _CHAVES_MENSAGEM:
        texto = _mensagem_em_valor(data.get(chave))
        if texto:
            return texto
    for chave in ("errors", "Errors", "messages", "Messages"):
        texto = _mensagem_em_valor(data.get(chave))
        if texto:
            return texto
    return ""


def extrair_mensagem_coresso(resposta: _RespostaHttpComTexto) -> str:
    """Lê a mensagem de erro do corpo da resposta do CoreSSO.

    Args:
        resposta (_RespostaHttpComTexto): Resposta HTTP com atributo ``text``.

    Returns:
        str: Texto do erro para repasse ao frontend; vazio se o corpo estiver
            ausente ou sem campo reconhecido.
    """
    texto = (resposta.text or "").strip()
    if not texto:
        return ""
    try:
        dados = json.loads(texto)
    except json.JSONDecodeError:
        return texto
    if isinstance(dados, str):
        return dados.strip()
    if isinstance(dados, dict):
        return _mensagem_em_dict(dados)
    return ""
