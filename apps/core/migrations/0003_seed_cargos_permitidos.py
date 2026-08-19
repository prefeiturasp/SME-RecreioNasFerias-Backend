"""Seed inicial dos cargos permitidos usados na autorizacao do login."""

from django.db import migrations

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


def seed_cargos_permitidos(apps, schema_editor) -> None:
    cargo_permitido_model = apps.get_model("core", "CargoPermitido")
    for codigo, descricao in CARGOS_SEED:
        cargo_permitido_model.objects.update_or_create(
            codigo_cargo=codigo,
            defaults={
                "descricao_cargo": descricao[:512],
            },
        )


def unseed_cargos_permitidos(apps, schema_editor) -> None:
    cargo_permitido_model = apps.get_model("core", "CargoPermitido")
    codigos = [codigo for codigo, _descricao in CARGOS_SEED]
    cargo_permitido_model.objects.filter(codigo_cargo__in=codigos).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0002_alter_identidade_models"),
    ]

    operations = [
        migrations.RunPython(
            seed_cargos_permitidos,
            unseed_cargos_permitidos,
        ),
    ]
