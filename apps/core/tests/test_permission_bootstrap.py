"""Testes do bootstrap e do primeiro login do Administrador COCEU."""

from importlib import import_module

import pytest
from django.apps import apps
from django.contrib.auth.models import Group
from django.test import override_settings

from apps.core.models import CargoPermitido, Usuario
from apps.core.services.auth_service import AuthService
from apps.integracoes.coresso.port import CargoCoresso, CoressoIdentity

pytestmark = pytest.mark.django_db

migration_rbac = import_module(
    "apps.core.migrations.0005_permissionamento_customizado"
)


def aplicar_migration_com_rf(rf: str) -> None:
    """Executa a função de dados da migration com o RF indicado."""
    with override_settings(PRIMEIRO_ADMIN_COCEU_RF=rf):
        migration_rbac.aplicar_permissionamento(apps, schema_editor=None)


def test_migration_exige_rf_configurado() -> None:
    """Interrompe o bootstrap com mensagem clara se não houver RF."""
    with (
        override_settings(PRIMEIRO_ADMIN_COCEU_RF=""),
        pytest.raises(RuntimeError, match="PRIMEIRO_ADMIN_COCEU_RF"),
    ):
        migration_rbac.aplicar_permissionamento(apps, schema_editor=None)


def test_migration_cria_administrador_com_senha_inutilizavel_e_e_idempotente(
) -> None:
    """Cria o usuário de bootstrap e mantém o resultado ao repetir a carga."""
    rf = "RF_BOOTSTRAP_NOVO_001"

    aplicar_migration_com_rf(rf)
    aplicar_migration_com_rf(rf)

    usuario = Usuario.objects.get(rf=rf)
    assert usuario.username == rf
    assert usuario.is_active is True
    assert usuario.has_usable_password() is False
    assert usuario.groups.filter(name="ADMINISTRADOR_COCEU").exists()
    assert Usuario.objects.filter(rf=rf).count() == 1


def test_migration_reutiliza_usuario_encontrado_pelo_username() -> None:
    """Vincula o RF e o perfil a um usuário local já existente."""
    rf = "RF_BOOTSTRAP_USERNAME_002"
    usuario = Usuario.objects.create_user(
        username=rf,
        password="senha-local",
        rf=None,
    )
    senha_hash = usuario.password

    aplicar_migration_com_rf(rf)

    usuario.refresh_from_db()
    assert usuario.rf == rf
    assert usuario.password == senha_hash
    assert usuario.groups.filter(name="ADMINISTRADOR_COCEU").exists()


def test_migration_rejeita_rf_que_identifica_mais_de_um_usuario() -> None:
    """Evita escolher arbitrariamente entre RF e username duplicados."""
    rf = "RF_BOOTSTRAP_AMBIGUO_003"
    Usuario.objects.create_user(
        username="usuario-por-rf",
        password="senha",
        rf=rf,
    )
    Usuario.objects.create_user(
        username=rf,
        password="senha",
        rf="RF_DIFERENTE_003",
    )

    with (
        override_settings(PRIMEIRO_ADMIN_COCEU_RF=rf),
        pytest.raises(RuntimeError, match="mais de um usuário local"),
    ):
        migration_rbac.aplicar_permissionamento(apps, schema_editor=None)


def test_migration_rejeita_username_vinculado_a_outro_rf() -> None:
    """Não troca o RF de uma conta com outro registro funcional."""
    rf = "RF_BOOTSTRAP_DIVERGENTE_004"
    Usuario.objects.create_user(
        username=rf,
        password="senha",
        rf="RF_DIFERENTE_004",
    )

    with (
        override_settings(PRIMEIRO_ADMIN_COCEU_RF=rf),
        pytest.raises(RuntimeError, match="outro RF vinculado"),
    ):
        migration_rbac.aplicar_permissionamento(apps, schema_editor=None)


def test_migration_rejeita_usuario_administrador_inativo() -> None:
    """Não atribui o perfil inicial a uma conta local desativada."""
    rf = "RF_BOOTSTRAP_INATIVO_005"
    Usuario.objects.create_user(
        username=rf,
        password="senha",
        rf=rf,
        is_active=False,
    )

    with (
        override_settings(PRIMEIRO_ADMIN_COCEU_RF=rf),
        pytest.raises(RuntimeError, match="usuário indicado.*inativo"),
    ):
        migration_rbac.aplicar_permissionamento(apps, schema_editor=None)


def test_administrador_criado_pela_migration_pode_entrar_via_coresso() -> None:
    """O login mantém o perfil administrador do usuário provisionado."""
    rf = "RF_BOOTSTRAP_LOGIN_006"
    aplicar_migration_com_rf(rf)
    usuario_inicial = Usuario.objects.get(rf=rf)

    cargo, _ = CargoPermitido.objects.update_or_create(
        codigo_cargo=98231,
        defaults={"descricao_cargo": "Cargo de acesso administrativo"},
    )
    identidade = CoressoIdentity(
        usuario_id_externo="id-admin-bootstrap",
        rf=rf,
        nome="Administrador de Teste",
        email="admin.teste@example.test",
        cpf="12345678901",
        cargos=(CargoCoresso(98231, "Cargo de acesso administrativo"),),
        cargos_sobrepostos=(),
        cargos_efetivos=(
            CargoCoresso(98231, "Cargo de acesso administrativo"),
        ),
        perfis=(),
        unidades_lotacao=(),
        unidade_exercicio=None,
        payload_bruto={},
    )

    class FakeCoresso:
        def autenticar(self, login: str, senha: str) -> CoressoIdentity:
            assert login == rf
            assert senha == "senha-validada-no-coresso"
            return identidade

    sessao = AuthService(coresso=FakeCoresso()).login(
        rf,
        "senha-validada-no-coresso",
    )

    usuario = Usuario.objects.get(rf=rf)
    assert sessao.usuario.pk == usuario_inicial.pk
    assert usuario.cargo_permitido == cargo
    assert usuario.has_usable_password() is False
    assert usuario.groups.filter(name="ADMINISTRADOR_COCEU").exists()
    assert not usuario.groups.filter(name="USUARIO_UE").exists()
    assert usuario.has_perm("core.criar_usuarios")


def test_migration_vincula_usuarios_com_cargo_ao_perfil_ue() -> None:
    """Atribui Usuário UE aos usuários locais com cargo autorizado."""
    rf_admin = "RF_BOOTSTRAP_GRUPOS_007"
    usuario_com_cargo_rf = "RF_BOOTSTRAP_CARGO_008"
    cargo, _ = CargoPermitido.objects.update_or_create(
        codigo_cargo=98232,
        defaults={"descricao_cargo": "Cargo de teste UE"},
    )
    usuario_com_cargo = Usuario.objects.create_user(
        username=usuario_com_cargo_rf,
        rf=usuario_com_cargo_rf,
        password="senha",
        cargo_permitido=cargo,
    )

    aplicar_migration_com_rf(rf_admin)

    perfil_ue = Group.objects.get(name="USUARIO_UE")
    assert usuario_com_cargo.groups.filter(pk=perfil_ue.pk).exists()
