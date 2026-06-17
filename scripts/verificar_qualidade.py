"""
Executa verificações de qualidade em um único comando.

Roda checagem de tipagem (PEP 484), docstrings (PEP 257) e testes,
interrompendo ao primeiro erro e retornando código de saída adequado.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from caminhos_qualidade import comando_flake8, comando_pydocstyle, comando_pytest


def executar_comando(comando: list[str], diretorio_raiz: Path) -> None:
    """Executa um comando de validação e falha se houver erro.

    Args:
        comando (list[str]): Comando e argumentos a serem executados.
        diretorio_raiz (Path): Diretório raiz do projeto.

    Returns:
        None: Apenas escreve logs no terminal.

    Raises:
        subprocess.CalledProcessError: Se o comando finalizar com erro.
    """
    print(f"\n>>> Executando: {' '.join(comando)}")
    subprocess.run(comando, check=True, cwd=diretorio_raiz)


def main() -> int:
    """Orquestra a suíte de qualidade do projeto em sequência.

    Args:
        Não recebe argumentos explícitos.

    Returns:
        int: ``0`` quando todas as validações passam; ``1`` em falha.

    Raises:
        Não propaga exceções; converte falhas em código de saída ``1``.
    """
    raiz_projeto = Path(__file__).resolve().parents[1]
    executavel = sys.executable
    comandos = [
        [executavel, "-m", "mypy"],
        comando_pydocstyle(executavel),
        comando_flake8(executavel),
        comando_pytest(executavel),
    ]

    try:
        for comando in comandos:
            executar_comando(comando, raiz_projeto)
    except subprocess.CalledProcessError as erro:
        print("\nFalha na suíte de qualidade.")
        print(f"Comando com erro: {' '.join(erro.cmd)}")
        return 1

    print("\nSuíte de qualidade concluída com sucesso.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
