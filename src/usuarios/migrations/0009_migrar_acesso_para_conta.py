"""Migra ``usuarios_acessos`` para ``usuarios_conta`` (AUTH_USER_MODEL) e remove tabela legada."""

from django.contrib.auth.hashers import make_password
from django.db import migrations


def migrar_acesso_para_conta(apps, schema_editor):
    Acesso = apps.get_model("usuarios", "UsuarioAcessoModel")
    Usuario = apps.get_model("usuarios", "Usuario")
    for acesso in Acesso.objects.all():
        usuario, _ = Usuario.objects.update_or_create(
            rf=acesso.rf,
            defaults={
                "email": f"{acesso.rf}@recreionasferias.local",
                "contexto": acesso.contexto,
                "permissoes_rbac": acesso.permissoes,
                "is_active": True,
                "password": make_password(None),
            },
        )
        if not usuario.password:
            usuario.password = make_password(None)
            usuario.save(update_fields=["password"])


class Migration(migrations.Migration):

    dependencies = [
        ("usuarios", "0000_usuario"),
        ("usuarios", "0008_cargopermitidomodel"),
    ]

    operations = [
        migrations.RunPython(migrar_acesso_para_conta, migrations.RunPython.noop),
        migrations.DeleteModel(
            name="UsuarioAcessoModel",
        ),
    ]
