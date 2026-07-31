"""Modelos abstratos compartilhados do projeto."""

from django.db import models


class ModeloBase(models.Model):
    """Define campos comuns de criação e atualização."""

    id: models.BigAutoField = models.BigAutoField(primary_key=True)
    criado_em: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    atualizado_em: models.DateTimeField = models.DateTimeField(auto_now=True)

    class Meta:
        """Metadados do modelo abstrato base."""

        abstract = True


class ModeloAtualizavel(ModeloBase):
    """Adiciona marcação simples de ativo/inativo ao modelo base."""

    ativo: models.BooleanField = models.BooleanField(default=True)

    class Meta:
        """Metadados do modelo abstrato atualizável."""

        abstract = True
