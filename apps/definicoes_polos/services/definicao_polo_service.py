"""Casos de uso do domínio de definições de polos."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import (
    F,
    FilteredRelation,
    OuterRef,
    Q,
    QuerySet,
    Subquery,
)
from django.db.models.functions import Coalesce

from apps.definicoes_polos.constants import TipoPolo
from apps.definicoes_polos.models import DefinicaoPolo
from apps.polos.models import Polo

MENSAGEM_TIPOS_DEFINIDOS = "Tipos de polo alterados com sucesso."
MENSAGEM_POLOS_SEM_EDICAO = (
    "Houve polos que não tiveram o tipo alterado, pois não existe vínculo "
    "com edição."
)


class DefinicaoPoloService:
    """Orquestra o cadastro e a participação dos polos nas edições."""

    def listar_participacoes(
        self, polo: Polo | None = None, edicao: object | None = None
    ) -> QuerySet[DefinicaoPolo]:
        """Lista participações, opcionalmente filtradas."""
        consulta = DefinicaoPolo.objects.select_related("polo", "edicao")
        if polo is not None:
            consulta = consulta.filter(polo=polo)
        if edicao is not None:
            consulta = consulta.filter(edicao=edicao)
        return consulta

    def obter_participacao(self, uuid: object) -> DefinicaoPolo:
        """Obtém uma participação pelo UUID público."""
        return DefinicaoPolo.objects.select_related("polo", "edicao").get(
            uuid=uuid
        )

    @transaction.atomic
    def vincular(
        self,
        polo: Polo,
        edicao: object,
        projecao_inscritos: int,
        ponto_focal_nome: str = "",
        ponto_focal_telefone: str = "",
        ponto_focal_email: str = "",
    ) -> DefinicaoPolo:
        """Cria uma participação iniciada como pendente."""
        definicao = DefinicaoPolo(
            polo=polo,
            edicao=edicao,
            tipo=TipoPolo.PENDENTE,
            projecao_inscritos=projecao_inscritos,
            ponto_focal_nome=ponto_focal_nome,
            ponto_focal_telefone=ponto_focal_telefone,
            ponto_focal_email=ponto_focal_email,
        )
        definicao.save()
        return definicao

    @transaction.atomic
    def atualizar(
        self, definicao: DefinicaoPolo, **dados: Any
    ) -> DefinicaoPolo:
        """Atualiza os dados editáveis de uma participação."""
        dados.pop("uuid", None)
        dados.pop("total_inscritos", None)
        dados.pop("ativo", None)
        for campo, valor in dados.items():
            setattr(definicao, campo, valor)
        definicao.save()
        return definicao

    @transaction.atomic
    def atualizar_capacidade_e_ponto_focal(
        self, definicao: DefinicaoPolo, **dados: Any
    ) -> DefinicaoPolo:
        """Atualiza projeção e dados do ponto focal."""
        permitidos = {
            "projecao_inscritos",
            "ponto_focal_nome",
            "ponto_focal_telefone",
            "ponto_focal_email",
        }
        return self.atualizar(
            definicao,
            **{
                campo: valor
                for campo, valor in dados.items()
                if campo in permitidos
            },
        )

    @transaction.atomic
    def alterar_tipo(
        self, definicao: DefinicaoPolo, tipo: str
    ) -> DefinicaoPolo:
        """Altera o tipo da participação."""
        definicao.tipo = tipo
        definicao.save()
        return definicao

    @transaction.atomic
    def excluir(self, definicao: DefinicaoPolo) -> None:
        """Exclui uma participação."""
        definicao.delete()

    @transaction.atomic
    def vincular_em_massa(
        self, polos: Iterable[Polo], edicao: object, projecao_inscritos: int
    ) -> dict[str, list[DefinicaoPolo | Polo]]:
        """Cria participações para vários polos, ignorando já vinculados."""
        polos = list(polos)
        vinculados = set(
            DefinicaoPolo.objects.filter(
                edicao=edicao, polo__in=polos
            ).values_list("polo_id", flat=True)
        )
        criadas: list[DefinicaoPolo] = []
        ignorados: list[Polo] = []
        for polo in polos:
            if polo.pk in vinculados:
                ignorados.append(polo)
                continue
            vinculados.add(polo.pk)
            criadas.append(
                self.vincular(
                    polo,
                    edicao,
                    projecao_inscritos,
                )
            )
        return {"criadas": criadas, "ignorados": ignorados}

    @transaction.atomic
    def alterar_tipo_em_massa(
        self, operacoes: Iterable[dict[str, object]]
    ) -> dict[str, list[DefinicaoPolo | dict[str, object]] | str]:
        """Define o tipo de cada polo para a edição informada.

        Operações sem edição são ignoradas. Operações com edição criam o
        vínculo ausente com projeção inicial zero ou atualizam o vínculo já
        existente.
        """
        alterados: list[DefinicaoPolo] = []
        ignorados: list[dict[str, object]] = []

        for operacao in operacoes:
            polo = operacao["polo"]
            edicao = operacao["edicao"]
            tipo = operacao["tipo"]
            if edicao is None:
                ignorados.append(
                    {
                        "polo_uuid": polo.uuid,
                        "motivo": "Polo sem vínculo com edição.",
                    }
                )
                continue

            definicao = (
                DefinicaoPolo.objects.select_for_update()
                .filter(polo=polo, edicao=edicao)
                .first()
            )
            if definicao is None:
                definicao = DefinicaoPolo(
                    polo=polo,
                    edicao=edicao,
                    tipo=TipoPolo.PENDENTE,
                    projecao_inscritos=0,
                )
                definicao.save()

            definicao.tipo = tipo
            definicao.save()
            alterados.append(definicao)

        return {
            "mensagem": (
                MENSAGEM_POLOS_SEM_EDICAO
                if ignorados
                else MENSAGEM_TIPOS_DEFINIDOS
            ),
            "alterados": alterados,
            "ignorados": ignorados,
        }

    @transaction.atomic
    def alterar_edicao_em_massa(
        self, definicoes: Iterable[DefinicaoPolo], edicao_destino: object
    ) -> list[DefinicaoPolo]:
        """Move definições selecionadas para uma edição de destino."""
        definicoes = list(
            DefinicaoPolo.objects.select_for_update().filter(
                uuid__in=[definicao.uuid for definicao in definicoes]
            )
        )
        polo_ids = [definicao.polo_id for definicao in definicoes]
        conflitos = DefinicaoPolo.objects.filter(
            edicao=edicao_destino, polo_id__in=polo_ids
        ).exclude(pk__in=[definicao.pk for definicao in definicoes])
        if conflitos.exists():
            nomes = ", ".join(
                conflitos.values_list("polo__nome_polo", flat=True)
            )
            raise ValidationError(
                "Erro: os seguintes polos já estão vinculados à edição de "
                "destino: "
                f"{nomes}."
            )
        if len(polo_ids) != len(set(polo_ids)):
            raise ValidationError(
                "Erro: não é possível mover mais de uma definição do mesmo "
                "polo "
                "para a mesma edição de destino."
            )
        for definicao in definicoes:
            definicao.edicao = edicao_destino
            definicao.save()
        return definicoes

    def listar_polos_com_definicao(
        self,
        dre_codigos_eol: Iterable[str] | None = None,
        tipo_ue: str | None = None,
        busca: str | None = None,
        gestao: str | None = None,
        edicao: object | None = None,
        tipo_polo: str | None = None,
    ) -> QuerySet[Polo]:
        """Lista polos com a definição da edição ou mais recente."""
        if edicao is not None:
            consulta = self._anotar_com_edicao_filtrada(edicao)
        else:
            consulta = self._anotar_com_participacao_mais_recente(tipo_polo)
        consulta = self._aplicar_filtros_estruturais(
            consulta, dre_codigos_eol, tipo_ue, busca, gestao
        )
        if tipo_polo and tipo_polo.strip():
            tipo_polo = tipo_polo.strip()
            consulta = consulta.filter(tipo_polo_edicao=tipo_polo)
        return consulta.order_by("nome_polo")

    def _anotar_com_edicao_filtrada(self, edicao: object) -> QuerySet[Polo]:
        """Anota a participação da edição sem reutilizar o alias no JOIN."""
        definicao_da_edicao = DefinicaoPolo.objects.filter(
            polo=OuterRef("pk"),
            edicao=edicao,
        ).order_by()
        return (
            Polo.objects.annotate(
                definicao_filtrada=FilteredRelation(
                    "definicoes", condition=Q(definicoes__edicao=edicao)
                )
            )
            .filter(definicao_filtrada__isnull=False)
            .annotate(
                definicao_uuid=Subquery(
                    definicao_da_edicao.values("uuid")[:1]
                ),
                edicao_uuid=Subquery(
                    definicao_da_edicao.values("edicao__uuid")[:1]
                ),
                nome_edicao=Subquery(
                    definicao_da_edicao.values("edicao__nome")[:1]
                ),
                tipo_polo_edicao=Subquery(
                    definicao_da_edicao.values("tipo")[:1]
                ),
                projecao_inscritos_edicao=Subquery(
                    definicao_da_edicao.values("projecao_inscritos")[:1]
                ),
                total_inscritos_edicao=Subquery(
                    definicao_da_edicao.values("total_inscritos")[:1]
                ),
            )
        )

    def _anotar_com_participacao_mais_recente(
        self, tipo_polo: str | None = None
    ) -> QuerySet[Polo]:
        ultima = DefinicaoPolo.objects.filter(polo=OuterRef("pk")).order_by(
            "-edicao__data_inicio", "-criado_em"
        )
        if tipo_polo and tipo_polo.strip():
            ultima = ultima.filter(tipo=tipo_polo.strip())
        return Polo.objects.annotate(
            definicao_uuid=Subquery(ultima.values("uuid")[:1]),
            edicao_uuid=Subquery(ultima.values("edicao__uuid")[:1]),
            nome_edicao=Subquery(ultima.values("edicao__nome")[:1]),
            tipo_polo_edicao=Coalesce(
                Subquery(ultima.values("tipo")[:1]),
                F("tipo"),
            ),
            projecao_inscritos_edicao=Subquery(
                ultima.values("projecao_inscritos")[:1]
            ),
            total_inscritos_edicao=Subquery(
                ultima.values("total_inscritos")[:1]
            ),
        )

    @staticmethod
    def _aplicar_filtros_estruturais(
        consulta: QuerySet[Polo],
        dre_codigos_eol: Iterable[str] | None,
        tipo_ue: str | None,
        busca: str | None,
        gestao: str | None,
    ) -> QuerySet[Polo]:
        """Aplica filtros pertencentes ao cadastro do polo."""
        if dre_codigos_eol:
            codigos = [str(codigo).strip() for codigo in dre_codigos_eol]
            codigos = [codigo for codigo in codigos if codigo]
            if codigos:
                consulta = consulta.filter(dre_codigo_eol__in=codigos)
        if tipo_ue and tipo_ue.strip():
            consulta = consulta.filter(tipo_ue=tipo_ue.strip())
        if busca and busca.strip():
            termo = busca.strip()
            consulta = consulta.filter(
                Q(nome_polo__icontains=termo) | Q(codigo_eol__icontains=termo)
            )
        if gestao and gestao.strip():
            consulta = consulta.filter(gestao=gestao.strip())
        return consulta
