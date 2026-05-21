# Generated manually for cargos permitidos no login.

import uuid

from django.db import migrations, models

# Códigos e descrições conforme retorno da API (nomeCargo).
# Itens da política sem correspondência na lista de referência da API não foram incluídos
# (ex.: "SERVIÇOS TÉCNICOS EDUCACIONAIS - STE"; "ASSISTENTE TECNICO DE EDUCACAO II/III"
# não constavam no catálogo fornecido — incluir quando houver codigoCargo oficial).
CARGOS_SEED = [
    (6106, "AGENTE DE APOIO - NIVEL I"),
    (6114, "AGENTE DE APOIO - NIVEL II"),
    (5720, "AGENTE ESCOLAR"),
    (2653, "ANALISTA DE INF.CULT. E DESP.- BIBLIOTECA"),
    (2654, "ANALISTA DE INF.CULT.E DESP.- ED.FISICA"),
    (3010, "ANALISTA DE INF.CULT.E DESP.- ED. FISICA - NIV.II"),
    (3011, "ANALISTA DE INF.CULT.E DESP.- ED. FISICA - NIV.III"),
    (3012, "ANALISTA DE INF.CULT.E DESP.- BIBLIOTECA - NIV. II"),
    (3013, "ANALISTA DE INF.CULT.E DESP.- BIBLIOTECA - NIV.III"),
    (71, "ASSESSOR I"),
    (72, "ASSESSOR II"),
    (73, "ASSESSOR III"),
    (74, "ASSESSOR IV"),
    (4909, "ASSIST.ADM. DE GESTAO"),
    (3166, "ASSIST. DE ATIVIDADES ARTISTICAS"),
    (4923, "ASSIST. DE SUPORTE OPERACIONAL"),
    (3085, "ASSISTENTE DE DIRETOR DE ESCOLA"),
    (2640, "ASSISTENTE TECNICO DE EDUCACAO I"),
    (3042, "ASSISTENTE TECNICO EDUCACIONAL"),
    (4510, "AUXILIAR DE SECRETARIA"),
    (4906, "AUXILIAR TECNICO DE EDUCACAO"),
    (445, "CHEFE DE NUCLEO DE ACAO CULTURAL"),
    (447, "CHEFE DE NUCLEO DE ACAO EDUCACIONAL"),
    (446, "CHEFE DE NUCLEO DE ESPORTES E LAZER"),
    (444, "CHEFE DE NUCLEO II"),
    (3379, "COORDENADOR PEDAGOGICO"),
    (3360, "DIRETOR DE ESCOLA"),
    (109, "DIRETOR I"),
    (3000, "DIRETOR REGIONAL DE EDUCAÇÃO"),
    (515, "GESTOR DE EQUIPAMENTO PUBLICO II"),
    (4529, "INSPETOR DE ALUNOS"),
    (3182, "SECRETARIO DE ESCOLA"),
]


def seed_cargos_permitidos(apps, schema_editor):
    CargoPermitido = apps.get_model("usuarios", "CargoPermitidoModel")
    for codigo, descricao in CARGOS_SEED:
        CargoPermitido.objects.update_or_create(
            codigo_cargo=codigo,
            defaults={"descricao_cargo": descricao[:512]},
        )


def unseed_cargos_permitidos(apps, schema_editor):
    CargoPermitido = apps.get_model("usuarios", "CargoPermitidoModel")
    codigos = [c for c, _ in CARGOS_SEED]
    CargoPermitido.objects.filter(codigo_cargo__in=codigos).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("usuarios", "0007_logloginmodel_id_sequencial"),
    ]

    operations = [
        migrations.CreateModel(
            name="CargoPermitidoModel",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        default=uuid.uuid4,
                    ),
                ),
                ("codigo_cargo", models.IntegerField(unique=True)),
                ("descricao_cargo", models.CharField(max_length=512)),
            ],
            options={
                "db_table": "usuarios_cargos_permitidos",
            },
        ),
        migrations.RunPython(seed_cargos_permitidos, unseed_cargos_permitidos),
    ]
