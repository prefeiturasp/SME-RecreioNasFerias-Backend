from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("usuarios", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="UsuarioAcessoModel",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("rf", models.CharField(max_length=7, unique=True)),
                ("contexto", models.CharField(blank=True, default="", max_length=100)),
                ("permissoes", models.JSONField(default=list)),
                ("atualizado_em", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "usuarios_acessos"},
        ),
    ]
