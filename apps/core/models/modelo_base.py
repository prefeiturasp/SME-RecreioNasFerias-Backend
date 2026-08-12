"""Modelos abstratos compartilhados do projeto."""

import uuid as uuid_lib

from django.db import models


class ModeloBase(models.Model):
    """Define campos comuns de criação e atualização."""

    uuid: models.UUIDField = models.UUIDField(
        default=uuid_lib.uuid4,
        editable=False,
        unique=True,
    )
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
