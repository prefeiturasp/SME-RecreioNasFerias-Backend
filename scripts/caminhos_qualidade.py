"""
Caminhos e comandos reutilizados pela suíte de qualidade do projeto.

Centraliza literais verificados por mypy, pydocstyle, flake8 e pytest para
evitar duplicação entre scripts e configurações.
"""

from __future__ import annotations

TESTES_COMMON = "tests/common"
TESTES_EDICOES = "tests/edicoes"
TESTES_POLOS = "tests/polos"
TESTES_SCRIPTS = "tests/scripts"
TESTES_EDICOES_VIEWS = "tests/edicoes/test_views.py"
TESTES_EDICOES_MODELS = "tests/edicoes/test_models.py"
TESTES_POLOS_VIEWS = "tests/polos/test_views.py"
TESTES_POLOS_MODELS = "tests/polos/test_models.py"
TESTES_PEP440 = "tests/scripts/test_pep440_versions.py"
COMMON_PAGINACAO = "src/common/paginacao.py"
COMMON_RESPOSTAS_HTTP = "src/common/respostas_http.py"
SRC_EDICOES = "src/edicoes"
SRC_POLOS = "src/polos"
SRC_USUARIOS_URLS = "src/usuarios/urls.py"
SCRIPTS = "scripts"


def comando_pydocstyle(executavel: str) -> list[str]:
    """Montar comando ``pydocstyle`` com os alvos estáticos do projeto.

    Args:
        executavel (str): Interpretador Python (``sys.executable``).

    Returns:
        list[str]: Comando completo para execução via ``subprocess``.
    """
    return [
        executavel,
        "-m",
        "pydocstyle",
        SRC_EDICOES,
        SRC_POLOS,
        COMMON_PAGINACAO,
        COMMON_RESPOSTAS_HTTP,
        TESTES_EDICOES,
        TESTES_POLOS,
        TESTES_COMMON,
        TESTES_PEP440,
        SCRIPTS,
    ]


def comando_flake8(executavel: str) -> list[str]:
    """Montar comando ``flake8`` com os alvos estáticos do projeto.

    Args:
        executavel (str): Interpretador Python (``sys.executable``).

    Returns:
        list[str]: Comando completo para execução via ``subprocess``.
    """
    return [
        executavel,
        "-m",
        "flake8",
        SRC_EDICOES,
        SRC_POLOS,
        SRC_USUARIOS_URLS,
        COMMON_PAGINACAO,
        COMMON_RESPOSTAS_HTTP,
        TESTES_EDICOES,
        TESTES_POLOS,
        TESTES_COMMON,
    ]


def comando_pytest(executavel: str) -> list[str]:
    """Montar comando ``pytest`` com cobertura mínima exigida pelo projeto.

    Args:
        executavel (str): Interpretador Python (``sys.executable``).

    Returns:
        list[str]: Comando completo para execução via ``subprocess``.
    """
    return [
        executavel,
        "-m",
        "pytest",
        TESTES_EDICOES_VIEWS,
        TESTES_EDICOES_MODELS,
        TESTES_POLOS_VIEWS,
        TESTES_POLOS_MODELS,
        TESTES_COMMON,
        TESTES_SCRIPTS,
        "--cov=edicoes.views",
        "--cov=polos.views",
        "--cov=polos.models",
        "--cov=common.paginacao",
        "--cov=common.respostas_http",
        "--cov=caminhos_qualidade",
        "--cov=verificar_qualidade",
        "--cov-report=term-missing",
        "--cov-fail-under=90",
    ]
