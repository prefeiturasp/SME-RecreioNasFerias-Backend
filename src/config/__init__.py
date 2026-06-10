"""
Pacote principal de configuração do projeto Django.

Agrupa ``settings``, roteamento raiz e pontos de entrada WSGI/ASGI do
backend SME Recreio nas Férias.
"""

# Importa extensões do drf-spectacular (side effects) para que a geração do
# OpenAPI saiba como representar autenticações customizadas.
from config import spectacular_extensions  # noqa: F401
