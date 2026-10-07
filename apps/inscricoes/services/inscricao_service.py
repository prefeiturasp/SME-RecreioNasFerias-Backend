"""Casos de uso e consultas do domínio de inscrições."""

from __future__ import annotations

from typing import Any

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone

from apps.definicoes_polos.constants import TipoPolo
from apps.inscricoes.constants import StatusInscricao
from apps.inscricoes.models import Inscricao
from apps.inscricoes.validators import (
    MENSAGEM_CODIGO_EOL_OBRIGATORIO,
    MENSAGEM_EOL_NAO_ENCONTRADO,
)
from apps.integracoes.eol.adapter import EolAdapter
from apps.integracoes.eol.port import EolPort, ParticipanteRedeEol
from apps.polos.constants import StatusPolo
from apps.polos.models import Polo


class InscricaoService:
    """Orquestra cadastro, edição, cancelamento e consultas de inscrições."""

    def __init__(self, eol: EolPort | None = None) -> None:
        """Inicializa o serviço adiando a criação da integração EOL."""
        self._eol = eol

    @property
    def eol(self) -> EolPort:
        """Cria a integração EOL apenas quando ela é efetivamente usada."""
        if self._eol is None:
            self._eol = EolAdapter()
        return self._eol

    def consultar_participante_por_eol(
        self,
        codigo_eol: str | None,
    ) -> ParticipanteRedeEol:
        """Consulta o participante da rede pelo código EOL.

        Args:
            codigo_eol: Código informado na busca. Vazio não chama a SME.

        Returns:
            Participante enriquecido.

        Raises:
            ValidationError: Quando o código está vazio ou a SME devolve
                lista vazia.
        """
        codigo = (codigo_eol or "").strip()
        if not codigo:
            raise ValidationError(
                {"codigo_eol": MENSAGEM_CODIGO_EOL_OBRIGATORIO}
            )
        participante = self.eol.consultar_participante(codigo)
        if participante is None:
            raise ValidationError({"codigo_eol": MENSAGEM_EOL_NAO_ENCONTRADO})
        return participante

    def listar(self, **filtros: object) -> QuerySet[Inscricao]:
        """Lista inscrições aplicando os filtros da tela de listagem."""
        consulta = Inscricao.objects.select_related("polo", "edicao")
        mapa_exato = {
            "tipo_estudante": "tipo_estudante",
            "grupo": "grupo",
            "status": "status",
            "polo": "polo__uuid",
        }
        for parametro, campo in mapa_exato.items():
            valor = filtros.get(parametro)
            if valor:
                consulta = consulta.filter(**{campo: valor})
        if filtros.get("codigo_eol"):
            valor = str(filtros["codigo_eol"]).strip()
            consulta = consulta.filter(codigo_eol__icontains=valor)
        if filtros.get("cpf"):
            valor = str(filtros["cpf"]).strip()
            consulta = consulta.filter(cpf__icontains=valor)
        if filtros.get("nome_participante"):
            consulta = consulta.filter(
                nome_participante__icontains=str(
                    filtros["nome_participante"]
                ).strip()
            )
        return consulta

    def obter(self, uuid: object) -> Inscricao:
        """Obtém uma inscrição pelo UUID público."""
        return Inscricao.objects.select_related("polo", "edicao").get(
            uuid=uuid
        )

    @transaction.atomic
    def criar(self, **dados: Any) -> Inscricao:
        """Cria uma inscrição, derivando o status pelo conteúdo informado."""
        dados.pop("status", None)
        return Inscricao.objects.create(**dados)

    @transaction.atomic
    def atualizar(self, inscricao: Inscricao, **dados: Any) -> Inscricao:
        """Atualiza uma inscrição sem remover um cancelamento explícito."""
        dados.pop("uuid", None)
        dados.pop("status", None)
        dados.pop("ativo", None)
        inscricao.refresh_from_db()
        for campo, valor in dados.items():
            setattr(inscricao, campo, valor)
        inscricao.save()
        return inscricao

    @transaction.atomic
    def cancelar(self, inscricao: Inscricao) -> Inscricao:
        """Cancela manualmente a inscrição."""
        inscricao.refresh_from_db()
        inscricao.status = StatusInscricao.CANCELADA
        inscricao.save(update_fields=("status", "atualizado_em"))
        return inscricao

    @transaction.atomic
    def reativar(self, inscricao: Inscricao) -> Inscricao:
        """Reativa e recalcula o status com base nos dados atuais."""
        inscricao.refresh_from_db()
        inscricao.status = StatusInscricao.RASCUNHO
        inscricao.save()
        return inscricao

    def listar_polos_elegiveis(
        self, dre_codigo_eol: str | None = None
    ) -> QuerySet[Polo]:
        """Lista polos ativos oficiais da edição com inscrições abertas."""
        hoje = timezone.localdate()
        consulta = Polo.objects.filter(
            status=StatusPolo.ATIVO,
            definicoes__tipo=TipoPolo.OFICIAL,
            definicoes__edicao__inscricoes_inicio__lte=hoje,
            definicoes__edicao__inscricoes_fim__gte=hoje,
        ).distinct()
        if dre_codigo_eol and dre_codigo_eol.strip():
            consulta = consulta.filter(dre_codigo_eol=dre_codigo_eol.strip())
        return consulta.order_by("nome_polo")

    def listar_polos_oficiais(self) -> QuerySet[Polo]:
        """Lista polos que foram oficiais ao menos uma vez.

        A consulta do gestor não restringe por período de inscrição, DRE
        nem status do polo.
        """
        return (
            Polo.objects.filter(definicoes__tipo=TipoPolo.OFICIAL)
            .distinct()
            .order_by("nome_polo")
        )
