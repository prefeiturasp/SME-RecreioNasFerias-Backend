"""Configuração Sphinx do projeto."""

project = "SME Recreio nas Férias Backend"
author = "SME"
release = "0.1.0"

extensions: list[str] = ["myst_parser"]
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}
templates_path: list[str] = ["_templates"]
exclude_patterns: list[str] = ["_build"]
language = "pt_BR"
html_theme = "sphinx_rtd_theme"
html_static_path: list[str] = ["_static"]
