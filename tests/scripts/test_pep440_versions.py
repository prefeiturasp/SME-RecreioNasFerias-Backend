"""Valida conformidade PEP 440 dos arquivos de requisitos."""

from pathlib import Path

from packaging.version import InvalidVersion, Version


def _iterar_especificacoes_requisitos(caminho_arquivo: Path) -> list[tuple[int, str]]:
    """Extrai linhas versionadas de um arquivo de requisitos.

    Args:
        caminho_arquivo (Path): Caminho para o arquivo ``requirements``.

    Returns:
        list[tuple[int, str]]: Lista de tuplas com número da linha e texto.

    Raises:
        OSError: Se ocorrer erro de leitura do arquivo.
    """
    especificacoes: list[tuple[int, str]] = []
    for indice, conteudo in enumerate(caminho_arquivo.read_text().splitlines(), start=1):
        linha = conteudo.strip()
        if not linha or linha.startswith("#") or "==" not in linha:
            continue
        especificacoes.append((indice, linha))
    return especificacoes


def _validar_versao_pep440(especificacao: str) -> None:
    """Valida se a versão de uma dependência segue PEP 440.

    Args:
        especificacao (str): Linha no formato ``pacote==versao``.

    Returns:
        None: Não retorna valor quando a versão é válida.

    Raises:
        AssertionError: Quando a versão não está em conformidade com PEP 440.
    """
    _, versao = especificacao.split("==", maxsplit=1)
    try:
        Version(versao.strip())
    except InvalidVersion as erro:
        raise AssertionError(f"Versão inválida para PEP 440: {especificacao}") from erro


def test_requisitos_sao_pep440_validos() -> None:
    """Assegura conformidade de versionamento nos requirements versionados.

    Args:
        Não recebe argumentos explícitos.

    Returns:
        None: Usa asserções para validação.

    Raises:
        AssertionError: Se alguma versão não for parseável pela PEP 440.
    """
    raiz_projeto = Path(__file__).resolve().parents[2]
    arquivos_requisitos = [
        raiz_projeto / "requirements.txt",
        raiz_projeto / "src" / "requirements.txt",
        raiz_projeto / "docs" / "requirements.txt",
    ]

    for arquivo in arquivos_requisitos:
        for numero_linha, especificacao in _iterar_especificacoes_requisitos(arquivo):
            try:
                _validar_versao_pep440(especificacao)
            except AssertionError as erro:
                raise AssertionError(
                    f"{arquivo.as_posix()}:{numero_linha} -> {erro}"
                ) from erro
