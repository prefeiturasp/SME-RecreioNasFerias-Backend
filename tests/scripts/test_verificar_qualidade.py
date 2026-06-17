"""Testes do orquestrador da suíte de qualidade."""

import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import verificar_qualidade  # noqa: E402


def test_executar_comando_deve_invocar_subprocess() -> None:
    """Garante delegação da execução para ``subprocess.run``."""
    with patch("verificar_qualidade.subprocess.run") as run_mock:
        verificar_qualidade.executar_comando(
            ["python", "-m", "pytest"],
            Path("/tmp"),
        )

    run_mock.assert_called_once_with(
        ["python", "-m", "pytest"],
        check=True,
        cwd=Path("/tmp"),
    )


def test_main_deve_retornar_zero_quando_comandos_passam() -> None:
    """Garante código de saída ``0`` quando todos os comandos concluem."""
    with patch.object(verificar_qualidade, "executar_comando"):
        resultado = verificar_qualidade.main()

    assert resultado == 0


def test_main_deve_retornar_um_quando_comando_falha() -> None:
    """Garante código de saída ``1`` quando algum comando falha."""
    with patch.object(
        verificar_qualidade,
        "executar_comando",
        side_effect=subprocess.CalledProcessError(1, ["python", "-m", "mypy"]),
    ):
        resultado = verificar_qualidade.main()

    assert resultado == 1


def test_main_deve_montar_quatro_comandos() -> None:
    """Garante execução de mypy, pydocstyle, flake8 e pytest."""
    comandos_executados: list[list[str]] = []

    def registrar(comando: list[str], _: Path) -> None:
        comandos_executados.append(comando)

    with patch.object(verificar_qualidade, "executar_comando", side_effect=registrar):
        verificar_qualidade.main()

    assert len(comandos_executados) == 4
    assert comandos_executados[0][1:3] == ["-m", "mypy"]
    assert comandos_executados[1][1:3] == ["-m", "pydocstyle"]
    assert comandos_executados[2][1:3] == ["-m", "flake8"]
    assert comandos_executados[3][1:3] == ["-m", "pytest"]


def test_modulo_principal_deve_encerrar_com_codigo_de_saida() -> None:
    """Garante que o guard ``__main__`` propaga o retorno de ``main``."""
    with patch.object(verificar_qualidade, "main", return_value=7):
        with pytest.raises(SystemExit) as excinfo:
            exec(
                compile("raise SystemExit(main())", "verificar_qualidade", "exec"),
                verificar_qualidade.__dict__,
            )

    assert excinfo.value.code == 7
