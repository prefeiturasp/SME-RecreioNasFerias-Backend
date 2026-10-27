"""Catálogo de recursos, ações e perfis ativos do sistema."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RecursoPermissoes:
    """Permissões disponíveis para um recurso da aplicação."""

    nome: str
    permissoes: dict[str, str]


RECURSOS: dict[str, RecursoPermissoes] = {
    "usuarios": RecursoPermissoes(
        "Usuários",
        {
            "view": "visualizar_usuarios",
            "add": "criar_usuarios",
            "change": "editar_usuarios",
            "delete": "excluir_usuarios",
        },
    ),
    "polos": RecursoPermissoes(
        "Polos",
        {
            "view": "visualizar_polos",
            "consultar_dres": "visualizar_dres",
            "add": "criar_polos",
            "change": "editar_polos",
            "delete": "excluir_polos",
        },
    ),
    "edicoes": RecursoPermissoes(
        "Edições do Programa",
        {
            "view": "visualizar_edicoes",
            "add": "criar_edicoes",
            "change": "editar_edicoes",
            "delete": "excluir_edicoes",
        },
    ),
    "inscricoes_participantes": RecursoPermissoes(
        "Inscrições de Participantes",
        {
            "view": "visualizar_inscricoes_participantes",
            "add": "criar_inscricoes_participantes",
            "change": "editar_inscricoes_participantes",
            "delete": "excluir_inscricoes_participantes",
        },
    ),
    "definicoes_polos": RecursoPermissoes(
        "Definições de Polos",
        {
            "view": "visualizar_definicoes_polos",
            "add": "criar_definicoes_polos",
            "change": "editar_definicoes_polos",
            "delete": "excluir_definicoes_polos",
        },
    ),
}


def _permissoes(recurso: str, *acoes: str) -> tuple[str, ...]:
    """Retorna os codenames de um conjunto de ações de um recurso."""
    return tuple(RECURSOS[recurso].permissoes[acao] for acao in acoes)


PERFIS: tuple[dict[str, object], ...] = (
    {
        "codigo": "ADMINISTRADOR_COCEU",
        "nome": "Administrador COCEU",
        "descricao": "Permissões de acordo com a matriz institucional.",
        "permissoes": (
            *_permissoes("usuarios", "view", "add", "change", "delete"),
            *_permissoes(
                "polos", "view", "consultar_dres", "add", "change", "delete"
            ),
            *_permissoes("edicoes", "view", "add", "change", "delete"),
            *_permissoes(
                "inscricoes_participantes", "view", "add", "change", "delete"
            ),
            *_permissoes(
                "definicoes_polos", "view", "add", "change", "delete"
            ),
        ),
    },
    {
        "codigo": "GESTOR_DICEU",
        "nome": "Gestor DICEU",
        "descricao": "Gestão dos recursos centrais definidos para a DICEU.",
        "permissoes": (
            *_permissoes("usuarios", "view"),
            *_permissoes(
                "polos", "view", "consultar_dres", "add", "change", "delete"
            ),
            *_permissoes("edicoes", "view"),
            *_permissoes("inscricoes_participantes", "view"),
            *_permissoes(
                "definicoes_polos", "view", "add", "change", "delete"
            ),
        ),
    },
    {
        "codigo": "GESTOR_CODAE",
        "nome": "Gestor CODAE",
        "descricao": "Consulta dos recursos definidos para a CODAE.",
        "permissoes": (
            *_permissoes("polos", "view", "consultar_dres"),
            *_permissoes("edicoes", "view"),
            *_permissoes("inscricoes_participantes", "view"),
        ),
    },
    {
        "codigo": "GESTOR_ASCOM",
        "nome": "Gestor ASCOM",
        "descricao": "Consulta de polos e edições do programa.",
        "permissoes": (
            *_permissoes("polos", "view", "consultar_dres"),
            *_permissoes("edicoes", "view"),
        ),
    },
    {
        "codigo": "GESTOR_COGED",
        "nome": "Gestor COGED",
        "descricao": "Consulta das edições do programa.",
        "permissoes": _permissoes("edicoes", "view"),
    },
    {
        "codigo": "GESTOR_POLO",
        "nome": "Gestor de Polo",
        "descricao": "Gestão das definições e consulta dos recursos do polo.",
        "permissoes": (
            *_permissoes("polos", "view", "consultar_dres"),
            *_permissoes("edicoes", "view"),
            *_permissoes("inscricoes_participantes", "view"),
            *_permissoes(
                "definicoes_polos", "view", "add", "change", "delete"
            ),
        ),
    },
    {
        "codigo": "USUARIO_UE",
        "nome": "Usuário UE",
        "descricao": (
            "Acesso concedido pelo cargo institucional para consultar, "
            "criar e editar inscrições de participantes."
        ),
        "permissoes": (
            *_permissoes("polos", "consultar_dres"),
            *_permissoes(
                "inscricoes_participantes", "view", "add", "change"
            ),
        ),
    },
)


PERMISSOES_PERSONALIZADAS_USUARIO = tuple(
    (
        codename,
        "Pode consultar as DREs disponíveis"
        if acao == "consultar_dres"
        else f"Pode {nome_acao} {recurso.nome.lower()}",
    )
    for recurso in RECURSOS.values()
    for acao, nome_acao, codename in (
        ("view", "visualizar", recurso.permissoes.get("view")),
        ("add", "criar", recurso.permissoes.get("add")),
        ("change", "editar", recurso.permissoes.get("change")),
        ("delete", "excluir", recurso.permissoes.get("delete")),
        (
            "consultar_dres",
            "consultar DREs",
            recurso.permissoes.get("consultar_dres"),
        ),
    )
    if codename is not None
)


ACOES_POR_METODO = {
    "GET": "view",
    "HEAD": "view",
    "OPTIONS": "view",
    "POST": "add",
    "PUT": "change",
    "PATCH": "change",
    "DELETE": "delete",
}

ROTULOS_ACOES = {
    "view": "Visualizar",
    "add": "Criar",
    "change": "Editar",
    "delete": "Excluir",
    "consultar_dres": "Consultar DREs",
}


def detalhar_permissoes(codenames: tuple[str, ...]) -> list[dict[str, str]]:
    """Converte codenames em itens legíveis para o contrato da API."""
    permitidas = set(codenames)
    return [
        {
            "codigo": f"core.{codename}",
            "recurso": recurso_key,
            "nome_recurso": recurso.nome,
            "acao": ROTULOS_ACOES[acao],
        }
        for recurso_key, recurso in RECURSOS.items()
        for acao, codename in recurso.permissoes.items()
        if codename in permitidas
    ]
