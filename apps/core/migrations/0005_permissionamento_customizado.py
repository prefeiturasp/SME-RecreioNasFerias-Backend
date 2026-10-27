"""Cria perfis RBAC, permissões e o primeiro Administrador COCEU."""

from django.conf import settings
from django.db import migrations
from django.db.models import Q

ACOES = {
    "usuarios": {
        "view": "visualizar_usuarios",
        "add": "criar_usuarios",
        "change": "editar_usuarios",
        "delete": "excluir_usuarios",
    },
    "polos": {
        "view": "visualizar_polos",
        "consultar_dres": "visualizar_dres",
        "add": "criar_polos",
        "change": "editar_polos",
        "delete": "excluir_polos",
    },
    "edicoes": {
        "view": "visualizar_edicoes",
        "add": "criar_edicoes",
        "change": "editar_edicoes",
        "delete": "excluir_edicoes",
    },
    "inscricoes_participantes": {
        "view": "visualizar_inscricoes_participantes",
        "add": "criar_inscricoes_participantes",
        "change": "editar_inscricoes_participantes",
        "delete": "excluir_inscricoes_participantes",
    },
    "definicoes_polos": {
        "view": "visualizar_definicoes_polos",
        "add": "criar_definicoes_polos",
        "change": "editar_definicoes_polos",
        "delete": "excluir_definicoes_polos",
    },
}

NOMES_RECURSOS = {
    "usuarios": "Usuários",
    "polos": "Polos",
    "edicoes": "Edições do Programa",
    "inscricoes_participantes": "Inscrições de Participantes",
    "definicoes_polos": "Definições de Polos",
}

NOMES_ACOES = {
    "view": "visualizar",
    "add": "criar",
    "change": "editar",
    "delete": "excluir",
}

def descricao_permissao(recurso, acao):
    """Gera a descrição histórica de uma permissão customizada."""
    if acao == "consultar_dres":
        return "Pode consultar as DREs disponíveis"
    return f"Pode {NOMES_ACOES[acao]} {NOMES_RECURSOS[recurso].lower()}"


PERMISSOES_PERSONALIZADAS = tuple(
    (codename, descricao_permissao(recurso, acao))
    for recurso, permissoes_recurso in ACOES.items()
    for acao, codename in permissoes_recurso.items()
)


def permissoes(*itens):
    """Expande pares recurso/ação para codenames Django."""
    return [ACOES[recurso][acao] for recurso, acao in itens]


PERMISSOES_PERFIL = {
    "ADMINISTRADOR_COCEU": permissoes(
        ("usuarios", "view"),
        ("usuarios", "add"),
        ("usuarios", "change"),
        ("usuarios", "delete"),
        ("polos", "view"),
        ("polos", "consultar_dres"),
        ("polos", "add"),
        ("polos", "change"),
        ("polos", "delete"),
        ("edicoes", "view"),
        ("edicoes", "add"),
        ("edicoes", "change"),
        ("edicoes", "delete"),
        ("inscricoes_participantes", "view"),
        ("inscricoes_participantes", "add"),
        ("inscricoes_participantes", "change"),
        ("inscricoes_participantes", "delete"),
        ("definicoes_polos", "view"),
        ("definicoes_polos", "add"),
        ("definicoes_polos", "change"),
        ("definicoes_polos", "delete"),
    ),
    "GESTOR_DICEU": permissoes(
        ("usuarios", "view"),
        ("polos", "view"),
        ("polos", "consultar_dres"),
        ("polos", "add"),
        ("polos", "change"),
        ("polos", "delete"),
        ("edicoes", "view"),
        ("inscricoes_participantes", "view"),
        ("definicoes_polos", "view"),
        ("definicoes_polos", "add"),
        ("definicoes_polos", "change"),
        ("definicoes_polos", "delete"),
    ),
    "GESTOR_CODAE": permissoes(
        ("polos", "view"),
        ("polos", "consultar_dres"),
        ("edicoes", "view"),
        ("inscricoes_participantes", "view"),
    ),
    "GESTOR_ASCOM": permissoes(
        ("polos", "view"),
        ("polos", "consultar_dres"),
        ("edicoes", "view"),
    ),
    "GESTOR_COGED": permissoes(
        ("edicoes", "view"),
    ),
    "GESTOR_POLO": permissoes(
        ("polos", "view"),
        ("polos", "consultar_dres"),
        ("edicoes", "view"),
        ("inscricoes_participantes", "view"),
        ("definicoes_polos", "view"),
        ("definicoes_polos", "add"),
        ("definicoes_polos", "change"),
        ("definicoes_polos", "delete"),
    ),
    "USUARIO_UE": permissoes(
        ("polos", "consultar_dres"),
        ("inscricoes_participantes", "view"),
        ("inscricoes_participantes", "add"),
        ("inscricoes_participantes", "change"),
    ),
}


def aplicar_permissionamento(apps, schema_editor):
    """Cria grupos/permissões e associa o RF inicial ao grupo COCEU."""
    rf = (getattr(settings, "PRIMEIRO_ADMIN_COCEU_RF", "") or "").strip()
    if not rf:
        raise RuntimeError(
            "Configure PRIMEIRO_ADMIN_COCEU_RF antes de aplicar a "
            "migration de permissionamento."
        )

    usuario_model = apps.get_model("core", "Usuario")
    group_model = apps.get_model("auth", "Group")
    permission_model = apps.get_model("auth", "Permission")
    content_type_model = apps.get_model("contenttypes", "ContentType")

    content_type, _ = content_type_model.objects.get_or_create(
        app_label="core", model="usuario"
    )
    codename_nome = dict(usuario_model._meta.permissions)
    codename_nome.update(
        {
            "add_usuario": "Can add user",
            "change_usuario": "Can change user",
            "delete_usuario": "Can delete user",
            "view_usuario": "Can view user",
        }
    )
    permissoes_db = {}
    for codename, nome in codename_nome.items():
        permissao, _ = permission_model.objects.get_or_create(
            content_type=content_type,
            codename=codename,
            defaults={"name": nome},
        )
        permissoes_db[codename] = permissao

    grupos = {}
    for codigo, codenames in PERMISSOES_PERFIL.items():
        grupo, _ = group_model.objects.get_or_create(name=codigo)
        grupo.permissions.set(
            [permissoes_db[codename] for codename in codenames]
        )
        grupos[codigo] = grupo

    for usuario_com_cargo in (
        usuario_model.objects
        .filter(cargo_permitido__isnull=False)
        .iterator()
    ):
        usuario_com_cargo.groups.add(grupos["USUARIO_UE"])

    usuarios = list(
        usuario_model.objects
        .filter(Q(rf=rf) | Q(username=rf))
        .order_by("pk")[:2]
    )
    if len(usuarios) > 1:
        raise RuntimeError(
            "PRIMEIRO_ADMIN_COCEU_RF corresponde a mais de um usuário local."
        )

    if usuarios:
        usuario = usuarios[0]
        if usuario.rf not in (None, "", rf):
            raise RuntimeError(
                "O username encontrado para PRIMEIRO_ADMIN_COCEU_RF possui "
                "outro RF vinculado."
            )
        if not usuario.rf:
            usuario.rf = rf
            usuario.save(update_fields=["rf"])
    else:
        usuario = usuario_model.objects.create(
            username=rf,
            rf=rf,
            password="!",
            is_active=True,
        )

    if not usuario.is_active:
        raise RuntimeError(
            "O usuário indicado por PRIMEIRO_ADMIN_COCEU_RF está inativo."
        )
    usuario.groups.add(grupos["ADMINISTRADOR_COCEU"])


class Migration(migrations.Migration):
    """Define as permissões RBAC iniciais e o usuário administrador."""

    dependencies = [
        ("core", "0004_remove_usuario_cargos_snapshot_and_more"),
        ("auth", "0012_alter_user_first_name_max_length"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="usuario",
            options={
                "verbose_name": "user",
                "verbose_name_plural": "users",
                "swappable": "AUTH_USER_MODEL",
                "permissions": PERMISSOES_PERSONALIZADAS,
            },
        ),
        migrations.RunPython(
            aplicar_permissionamento,
            migrations.RunPython.noop,
        ),
    ]
