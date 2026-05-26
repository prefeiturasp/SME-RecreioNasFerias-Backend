"""
Models abstratos reutilizáveis (timestamps e campos comuns).

Exporta ``ModeloBase`` e ``ModeloAtualizavel`` para herança em models
concretos sem duplicar definição de ``criado_em`` / ``atualizado_em``.
"""

from common.models.base import ModeloAtualizavel, ModeloBase

__all__ = ["ModeloAtualizavel", "ModeloBase"]
