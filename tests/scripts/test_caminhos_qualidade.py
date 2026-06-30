"""Testes dos comandos montados para a suíte de qualidade."""

import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import caminhos_qualidade  # noqa: E402


@pytest.mark.parametrize(
    ("fabrica", "modulo"),
    [
        (caminhos_qualidade.comando_pydocstyle, "pydocstyle"),
        (caminhos_qualidade.comando_flake8, "flake8"),
        (caminhos_qualidade.comando_pytest, "pytest"),
    ],
)
def test_comandos_devem_iniciar_com_executavel_e_modulo(
    fabrica,
    modulo: str,
) -> None:
    """Garante estrutura base ``[python, -m, modulo, ...]`` dos comandos."""
    comando = fabrica("python")

    assert comando[:3] == ["python", "-m", modulo]


def test_comando_pydocstyle_deve_incluir_alvos_estaticos() -> None:
    """Garante inclusão dos diretórios verificados pelo pydocstyle."""
    comando = caminhos_qualidade.comando_pydocstyle("python")

    assert caminhos_qualidade.SRC_EDICOES in comando
    assert caminhos_qualidade.SRC_POLOS_PARCEIROS in comando
    assert caminhos_qualidade.COMMON_PAGINACAO in comando
    assert caminhos_qualidade.TESTES_COMMON in comando
    assert caminhos_qualidade.TESTES_POLOS_PARCEIROS in comando
    assert caminhos_qualidade.SCRIPTS in comando


def test_comando_flake8_deve_incluir_urls_de_usuarios() -> None:
    """Garante verificação de ``src/usuarios/urls.py`` no flake8."""
    comando = caminhos_qualidade.comando_flake8("python")

    assert caminhos_qualidade.SRC_USUARIOS_URLS in comando
    assert caminhos_qualidade.TESTES_COMMON in comando


def test_comando_pytest_deve_incluir_cobertura_minima() -> None:
    """Garante parâmetros de cobertura exigidos pelo projeto."""
    comando = caminhos_qualidade.comando_pytest("python")

    assert caminhos_qualidade.TESTES_EDICOES_VIEWS in comando
    assert caminhos_qualidade.TESTES_EDICOES_MODELS in comando
    assert caminhos_qualidade.TESTES_POLOS_PARCEIROS_VIEWS in comando
    assert caminhos_qualidade.TESTES_POLOS_PARCEIROS_MODELS in comando
    assert caminhos_qualidade.TESTES_SCRIPTS in comando
    assert "--cov=edicoes.views" in comando
    assert "--cov=polos_parceiros.views" in comando
    assert "--cov=polos_parceiros.models" in comando
    assert "--cov=common.respostas_http" in comando
    assert "--cov=caminhos_qualidade" in comando
    assert "--cov=verificar_qualidade" in comando
    assert "--cov-fail-under=90" in comando
