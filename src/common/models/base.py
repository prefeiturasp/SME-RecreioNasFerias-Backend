"""
Models abstratos com campos compartilhados entre apps Django.

Fornece rastreamento temporal consistente para auditoria e ordenação
padrão por data de criação decrescente nas listagens administrativas.
"""

from django.db import models


class ModeloAtualizavel(models.Model):
    """Rastreia a última alteração do registro (``atualizado_em``).

    Deve ser herdado por entidades que precisam apenas do timestamp de
    atualização, sem campo de criação explícito.
    """

    atualizado_em = models.DateTimeField("atualizado em", auto_now=True)

    class Meta:
        """Metadados do model abstrato sem tabela física própria.

        ``abstract = True`` impede migração de tabela isolada para esta classe.
        """

        abstract = True


class ModeloBase(ModeloAtualizavel):
    """Timestamps padrão (``criado_em`` e ``atualizado_em``) para entidades.

    Base recomendada para models persistidos com histórico de criação e
    ordenação cronológica em consultas e Django Admin.
    """

    criado_em = models.DateTimeField("criado em", auto_now_add=True)

    class Meta:
        """Ordenação padrão por data de criação decrescente.

        Garante que listagens recentes apareçam primeiro sem ``order_by``
        explícito em cada ``QuerySet``.
        """

        abstract = True
        ordering = ("-criado_em",)
