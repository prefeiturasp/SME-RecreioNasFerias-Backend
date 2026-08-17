from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="usuario",
            name="ativo",
        ),
        migrations.AddField(
            model_name="usuario",
            name="cargos_snapshot",
            field=models.JSONField(default=list),
        ),
        migrations.AddField(
            model_name="usuario",
            name="cpf",
            field=models.CharField(blank=True, default="", max_length=11),
        ),
        migrations.AddField(
            model_name="usuario",
            name="nome_completo",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="usuario",
            name="rf",
            field=models.CharField(
                blank=True,
                max_length=32,
                null=True,
                unique=True,
                verbose_name="RF",
            ),
        ),
        migrations.AddField(
            model_name="cargopermitido",
            name="codigo_cargo",
            field=models.IntegerField(default=0, unique=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="cargopermitido",
            name="descricao_cargo",
            field=models.CharField(blank=True, default="", max_length=512),
        ),
        migrations.AddField(
            model_name="loglogin",
            name="codigo_cargo",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="loglogin",
            name="codigo_http",
            field=models.PositiveSmallIntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="loglogin",
            name="descricao_cargo",
            field=models.CharField(blank=True, default="", max_length=500),
        ),
        migrations.AddField(
            model_name="loglogin",
            name="endereco_ip",
            field=models.CharField(blank=True, default="", max_length=45),
        ),
        migrations.AddField(
            model_name="loglogin",
            name="login_tentativa",
            field=models.CharField(blank=True, default="", max_length=32),
        ),
        migrations.AddField(
            model_name="loglogin",
            name="mensagem",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="loglogin",
            name="sucesso",
            field=models.BooleanField(default=False),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="loglogin",
            name="user_agent",
            field=models.TextField(blank=True, default=""),
        ),
    ]
