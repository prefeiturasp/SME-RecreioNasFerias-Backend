"""Models abstratos com campos compartilhados entre apps Django."""

from django.db import models


class ModeloAtualizavel(models.Model):
    """Rastreia a última alteração do registro (ex.: entidades de autenticação)."""

    atualizado_em = models.DateTimeField("atualizado em", auto_now=True)

    class Meta:
        abstract = True


class ModeloBase(ModeloAtualizavel):
    """Timestamps padrão para entidades persistidas na aplicação."""

    criado_em = models.DateTimeField("criado em", auto_now_add=True)

    class Meta:
        abstract = True
        ordering = ("-criado_em",)
