import importlib.util
from pathlib import Path
from unittest.mock import Mock, patch


def _load_module():
    script_path = (
        Path(__file__).resolve().parents[2] / "scripts" / "fix_migration_history.py"
    )
    spec = importlib.util.spec_from_file_location("fix_migration_history_for_test", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_split_sql_remove_comentarios_e_begin_commit():
    with patch("django.setup"):
        module = _load_module()

    sql = """-- comentario
BEGIN;
CREATE TABLE teste (id int);
COMMIT;
ALTER TABLE teste ADD COLUMN nome text;
"""
    partes = module._split_sql(sql)

    assert partes == [
        "CREATE TABLE teste (id int);",
        "ALTER TABLE teste ADD COLUMN nome text;",
    ]


def test_main_registra_migracao_e_cria_tabela_quando_faltam():
    with patch("django.setup"):
        module = _load_module()

    cursor = Mock()
    cursor.fetchone.side_effect = [None, (None,)]
    cursor.rowcount = 2
    context_manager = Mock()
    context_manager.__enter__ = Mock(return_value=cursor)
    context_manager.__exit__ = Mock(return_value=False)
    fake_connection = Mock(cursor=Mock(return_value=context_manager))

    with patch.object(module, "connection", fake_connection):
        with patch.object(
            module,
            "call_command",
            side_effect=lambda *args, **kwargs: kwargs["stdout"].write(
                "CREATE TABLE usuarios_conta (id int);\n"
            )
            if args[:3] == ("sqlmigrate", "usuarios", "0000_usuario")
            else None,
        ) as call_command_mock:
            with patch("builtins.print") as print_mock:
                module.main()

    assert call_command_mock.call_args_list[-1].args == ("migrate",)
    assert any(
        "Registrada migração usuarios.0000_usuario no histórico." in str(args)
        for args, _ in print_mock.call_args_list
    )
    cursor.execute.assert_any_call(
        "INSERT INTO django_migrations (app, name, applied) VALUES (%s, %s, NOW())",
        ["usuarios", "0000_usuario"],
    )


def test_main_nao_recria_migracao_quando_ja_existe():
    with patch("django.setup"):
        module = _load_module()

    cursor = Mock()
    cursor.fetchone.side_effect = [(1,), ("public.usuarios_conta",)]
    cursor.rowcount = 0
    context_manager = Mock()
    context_manager.__enter__ = Mock(return_value=cursor)
    context_manager.__exit__ = Mock(return_value=False)
    fake_connection = Mock(cursor=Mock(return_value=context_manager))

    with patch.object(module, "connection", fake_connection):
        with patch.object(module, "call_command") as call_command_mock:
            with patch("builtins.print") as print_mock:
                module.main()

    insert_calls = [call for call in cursor.execute.call_args_list if "INSERT INTO django_migrations" in call.args[0]]
    assert not insert_calls
    assert any(
        "usuarios.0000_usuario já consta no histórico." in str(args)
        for args, _ in print_mock.call_args_list
    )
    call_command_mock.assert_called_once_with("migrate", verbosity=1)
