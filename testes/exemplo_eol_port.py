"""Exemplo de consumo da integração EOL pela porta (arquitetura hexagonal).

Demonstra como um domínio/serviço deve consumir a integração de escolas:
dependendo apenas do contrato ``EolPort`` e recebendo o adaptador pronto por
injeção. O adapter concreto (``EolAdapter``) aparece uma única vez, no ponto
de composição.

Uso:
    python testes/exemplo_eol_port.py [limite]

    docker compose -f docker-compose-dev.yml run --rm --no-deps api \
        python testes/exemplo_eol_port.py [limite]
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import django

# Garante que a raiz do projeto esteja no path para importar `config`/`apps`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.integracoes.eol.adapter import EolAdapter  # noqa: E402
from apps.integracoes.eol.port import (  # noqa: E402
    EolPort,
    UnidadeRecreioEol,
)


class ConsumidorDeUnidades:
    """Consumidor de unidades que depende apenas do contrato ``EolPort``."""

    def __init__(self, eol: EolPort) -> None:
        """Recebe o contrato ``EolPort`` já resolvido pela camada externa."""
        self.eol = eol

    def listar_unidades(
        self,
        limite: int | None = None,
    ) -> tuple[UnidadeRecreioEol, ...]:
        """Lista unidades elegíveis já enriquecidas pela integração."""
        return self.eol.listar_unidades_diretas_recreio(limite=limite)


def exibir(unidade: UnidadeRecreioEol) -> None:
    """Imprime uma unidade enriquecida de forma legível."""
    print(f"codigo_eol: {unidade.codigo_eol}")
    print(f"nome_escola: {unidade.nome_escola}")
    print(f"sigla_tipo_escola: {unidade.sigla_tipo_escola}")
    print(
        f"dre: {unidade.nome_dre} ({unidade.sigla_dre} - {unidade.codigo_dre})"
    )
    print(f"email: {unidade.email or '-'}")
    print(f"telefone: {unidade.telefone or '-'}")
    print(f"cep: {unidade.cep or '-'}")
    print(f"endereco: {unidade.endereco or '-'}")
    print(f"nome_diretor: {unidade.nome_diretor or '-'}")


def main() -> None:
    """Executa o exemplo com o limite informado (padrão 5)."""
    limite = int(sys.argv[1]) if len(sys.argv) > 1 else 5

    # Ponto de composição: único lugar onde o adapter concreto aparece.
    porta = EolAdapter()
    consumidor = ConsumidorDeUnidades(porta)

    unidades = consumidor.listar_unidades(limite=limite)

    print(f"Unidades retornadas: {len(unidades)}\n")
    for unidade in unidades:
        exibir(unidade)
        print("-" * 60)


if __name__ == "__main__":
    main()
