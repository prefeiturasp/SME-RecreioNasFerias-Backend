"""Casos de uso do domínio de edições."""

from __future__ import annotations

from typing import Any

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.edicoes.constants import StatusEdicao
from apps.edicoes.models import Edicao
from apps.edicoes.validators import MENSAGEM_EDICAO_ENCERRADA


class EdicaoService:
    """Orquestra criação, consulta, alteração e exclusão de edições."""

    @staticmethod
    @transaction.atomic
    def sincronizar_status() -> None:
        """Atualiza os status conforme a data atual do sistema.

        A ordem das transições é importante: uma edição que já terminou
        precisa deixar de ser ativa antes que outra edição seja promovida.
        O bloqueio das linhas serializa sincronizações concorrentes e a
        transação impede que uma sincronização fique parcialmente aplicada.
        """
        hoje = timezone.localdate()

        # Avaliar o queryset mantém todas as edições bloqueadas até o fim da
        # transação. A ordenação evita locks em ordens diferentes entre
        # requisições concorrentes.
        list(
            Edicao.objects.select_for_update()
            .order_by("pk")
            .values_list("pk", flat=True)
        )

        # Primeiro libera a constraint de edição ativa para a nova edição.
        Edicao.objects.filter(data_fim__lt=hoje).exclude(
            status=StatusEdicao.ENCERRADA
        ).update(status=StatusEdicao.ENCERRADA)

        Edicao.objects.filter(data_inicio__gt=hoje).exclude(
            status=StatusEdicao.PLANEJADA
        ).update(status=StatusEdicao.PLANEJADA)

        Edicao.objects.filter(
            data_inicio__lte=hoje,
            data_fim__gte=hoje,
        ).exclude(status=StatusEdicao.ATIVA).update(status=StatusEdicao.ATIVA)

    def listar(self):
        """Sincroniza status e retorna as edições ordenadas."""
        self.sincronizar_status()
        return Edicao.objects.all()

    def obter(self, uuid: object) -> Edicao:
        """Sincroniza status e obtém uma edição pelo UUID público."""
        self.sincronizar_status()
        return Edicao.objects.get(uuid=uuid)

    @transaction.atomic
    def criar(self, **dados: Any) -> Edicao:
        """Cria uma edição, sempre iniciando com status planejada."""
        self.sincronizar_status()
        dados.pop("status", None)
        edicao = Edicao(status=StatusEdicao.PLANEJADA, **dados)
        edicao.save()
        return edicao

    @transaction.atomic
    def atualizar(self, edicao: Edicao, **dados: Any) -> Edicao:
        """Atualiza uma edição que ainda não foi encerrada."""
        self.sincronizar_status()
        edicao.refresh_from_db()
        if edicao.status == StatusEdicao.ENCERRADA:
            raise ValidationError({"status": MENSAGEM_EDICAO_ENCERRADA})
        dados.pop("status", None)
        for campo, valor in dados.items():
            setattr(edicao, campo, valor)
        edicao.save()
        return edicao

    @transaction.atomic
    def excluir(self, edicao: Edicao) -> None:
        """Exclui uma edição somente enquanto ela não estiver encerrada."""
        self.sincronizar_status()
        edicao.refresh_from_db()
        if edicao.status == StatusEdicao.ENCERRADA:
            raise ValidationError({"status": MENSAGEM_EDICAO_ENCERRADA})
        edicao.delete()
