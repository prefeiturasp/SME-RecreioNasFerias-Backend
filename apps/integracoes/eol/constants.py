"""Constantes da integração com a SME Integração/EOL."""

from __future__ import annotations

# Siglas de tipo de unidade escolar elegíveis ao Recreio nas Férias.
SIGLAS_TIPO_UE_RECREIO = frozenset(
    {
        "EMEF",
        "EMEI",
        "EMEI P FOM",
        "CEI DIRET",
        "CEI INDIR",
        "CEU",
        "CEU EMEI",
        "CEU CEI",
        "CEU CEMEI",
    }
)

# Código do cargo Diretor de Escola no catálogo oficial da SME.
CODIGO_CARGO_DIRETOR_ESCOLA = 3360

# Quantidade padrão de requisições paralelas no enriquecimento de unidades.
MAX_WORKERS_PADRAO = 8
