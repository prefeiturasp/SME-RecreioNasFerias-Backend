"""Modelo de controle da população de polos diretos."""

from __future__ import annotations

from django.db import models


class ControleSincronizacaoPolos(models.Model):
    """Registra a última execução bem-sucedida da população de polos.

    A chave identifica o tipo de carga. A rotina de unidades diretas usa
    uma única linha para limitar a execução a uma vez por dia.
    """

    chave = models.CharField(
        max_length=64,
        primary_key=True,
        verbose_name="Chave",
    )
    ultima_execucao_em = models.DateTimeField(
        verbose_name="Última execução",
    )

    class Meta:
        """Metadados do controle de sincronização."""

        app_label = "polos"
        verbose_name = "Controle de sincronização de polos"
        verbose_name_plural = "Controles de sincronização de polos"

    def __str__(self) -> str:
        """Retorna a chave e o instante da última execução."""
        return f"{self.chave} @ {self.ultima_execucao_em.isoformat()}"
