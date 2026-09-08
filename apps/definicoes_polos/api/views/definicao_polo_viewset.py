"""ViewSet HTTP do domínio de definições de polos."""

from __future__ import annotations

from django.http import Http404
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiTypes,
    extend_schema,
    extend_schema_view,
)
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.definicoes_polos.api.serializers import (
    AlterarEdicaoEmMassaSerializer,
    DefinicaoPoloDetalhamentoSerializer,
    DefinicaoPoloHistoricoSerializer,
    DefinicaoPoloSerializer,
    AlterarTipoEmMassaAlteradoSerializer,
    AlterarTipoEmMassaIgnoradoSerializer,
    AlterarTipoEmMassaRespostaSerializer,
    AlterarTipoEmMassaSerializer,
    PoloComDefinicaoSerializer,
    VincularEmMassaResponseSerializer,
    VincularEmMassaSerializer,
)
from apps.definicoes_polos.models import DefinicaoPolo
from apps.definicoes_polos.services.definicao_polo_service import (
    DefinicaoPoloService,
)
from apps.edicoes.models import Edicao
from apps.polos.models import Polo

EDICAO_NAO_ENCONTRADA = "Edição não encontrada."


@extend_schema_view(
    list=extend_schema(
        summary="Lista definições de polos",
        description=(
            "Lista todos os polos com a definição da edição informada ou, "
            "quando a edição não for informada, com a participação mais "
            "recente de cada polo."
        ),
        tags=["Definições de Polos"],
        parameters=[
            OpenApiParameter(
                name="dre_codigos_eol",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                many=True,
                description="Um ou mais códigos EOL de DRE.",
            ),
            OpenApiParameter(
                name="tipo_ue",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filtra pela sigla do tipo de UE.",
            ),
            OpenApiParameter(
                name="busca",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Busca por nome da UE ou código EOL.",
            ),
            OpenApiParameter(
                name="gestao",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filtra pela gestão do polo.",
            ),
            OpenApiParameter(
                name="edicao",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
                description="Restringe a listagem a uma edição específica.",
            ),
            OpenApiParameter(
                name="tipo_polo",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filtra pelo tipo da participação mais recente.",
            ),
        ],
    ),
    create=extend_schema(
        summary="Vincula polo a edição", tags=["Definições de Polos"]
    ),
    retrieve=extend_schema(
        summary="Recupera definição de polo",
        tags=["Definições de Polos"],
        responses={200: DefinicaoPoloDetalhamentoSerializer},
    ),
    update=extend_schema(
        summary="Atualiza definição de polo", tags=["Definições de Polos"]
    ),
    partial_update=extend_schema(
        summary="Atualiza parcialmente definição de polo",
        tags=["Definições de Polos"],
    ),
    destroy=extend_schema(
        summary="Exclui definição de polo", tags=["Definições de Polos"]
    ),
)
class DefinicaoPoloViewSet(viewsets.ModelViewSet):
    """Expõe a participação e a listagem consolidada."""

    queryset = DefinicaoPolo.objects.select_related("polo", "edicao")
    serializer_class = DefinicaoPoloSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "uuid"
    service_class = DefinicaoPoloService

    def get_queryset(self):
        """Usa a listagem consolidada somente na ação de lista."""
        if self.action != "list":
            return self.queryset
        return self.service_class().listar_polos_com_definicao(
            dre_codigos_eol=self._parametros_multivalorados("dre_codigos_eol"),
            tipo_ue=self.request.query_params.get("tipo_ue"),
            busca=self.request.query_params.get("busca"),
            gestao=self.request.query_params.get("gestao"),
            edicao=self._obter_edicao_parametro(),
            tipo_polo=self.request.query_params.get("tipo_polo"),
        )

    def get_object(self):
        """Converte definição inexistente em erro de validação HTTP 400."""
        try:
            return super().get_object()
        except Http404 as exc:
            raise serializers.ValidationError(
                {"uuid": "Definição de Polo não encontrada."}
            ) from exc

    def get_serializer_class(self):
        """Seleciona o serializer específico da listagem consolidada."""
        if self.action == "list":
            return PoloComDefinicaoSerializer
        if self.action == "retrieve":
            return DefinicaoPoloDetalhamentoSerializer
        if self.action == "historico":
            return DefinicaoPoloHistoricoSerializer
        return super().get_serializer_class()

    def _parametros_multivalorados(self, nome: str) -> list[str]:
        """Aceita parâmetros repetidos ou valores separados por vírgula."""
        return [
            valor.strip()
            for item in self.request.query_params.getlist(nome)
            for valor in item.split(",")
            if valor.strip()
        ]

    def _obter_edicao_parametro(self):
        """Obtém a edição do filtro por UUID, quando informada."""
        valor = self.request.query_params.get("edicao")
        if not valor:
            return None
        return self._obter_recurso_por_uuid(
            Edicao,
            valor,
            "edicao",
            EDICAO_NAO_ENCONTRADA,
        )

    @staticmethod
    def _obter_recurso_por_uuid(modelo, valor, campo, mensagem):
        """Obtém um recurso relacionado convertendo ausência em HTTP 400."""
        try:
            return modelo.objects.get(uuid=valor)
        except modelo.DoesNotExist as exc:
            raise serializers.ValidationError({campo: mensagem}) from exc

    @staticmethod
    def _obter_polos_selecionados(uuids):
        """Obtém todos os polos solicitados ou retorna erro de validação."""
        polos_por_uuid = Polo.objects.in_bulk(uuids, field_name="uuid")
        ausentes = [str(uuid) for uuid in uuids if uuid not in polos_por_uuid]
        if ausentes:
            raise serializers.ValidationError(
                {
                    "polos": (
                        "Os seguintes UUIDs de polos não foram encontrados: "
                        + ", ".join(ausentes)
                    )
                }
            )
        return [polos_por_uuid[uuid] for uuid in uuids]

    @staticmethod
    def _obter_definicoes_selecionadas(uuids):
        """Obtém todas as definições solicitadas ou retorna erro."""
        definicoes_por_uuid = DefinicaoPolo.objects.in_bulk(
            uuids, field_name="uuid"
        )
        ausentes = [
            str(uuid) for uuid in uuids if uuid not in definicoes_por_uuid
        ]
        if ausentes:
            raise serializers.ValidationError(
                {
                    "definicoes": (
                        "Os seguintes UUIDs de definições não foram "
                        "encontrados: " + ", ".join(ausentes)
                    )
                }
            )
        return [definicoes_por_uuid[uuid] for uuid in uuids]

    @extend_schema(
        summary="Consulta histórico do polo",
        description="Retorna todas as participações de um polo.",
        tags=["Definições de Polos"],
        parameters=[
            OpenApiParameter(
                name="polo",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
                required=True,
                description="UUID do polo cujo histórico será consultado.",
            )
        ],
        responses={200: DefinicaoPoloHistoricoSerializer(many=True)},
    )
    @action(detail=False, methods=["get"], url_path="historico")
    def historico(self, request):
        """Lista todas as participações de um polo."""
        polo_uuid = request.query_params.get("polo")
        if not polo_uuid:
            raise serializers.ValidationError(
                {"polo": "O UUID do polo deve ser informado."}
            )
        polo = self._obter_recurso_por_uuid(
            Polo,
            polo_uuid,
            "polo",
            "Polo não encontrado.",
        )
        participacoes = self.service_class().listar_participacoes(polo=polo)
        return Response(
            DefinicaoPoloHistoricoSerializer(participacoes, many=True).data
        )

    def perform_create(self, serializer):
        """Cria a participação através do service de domínio."""
        dados = serializer.validated_data
        serializer.instance = self.service_class().vincular(
            polo=dados["polo"],
            edicao=dados["edicao"],
            projecao_inscritos=dados["projecao_inscritos"],
            ponto_focal_nome=dados.get("ponto_focal_nome", ""),
            ponto_focal_telefone=dados.get("ponto_focal_telefone", ""),
            ponto_focal_email=dados.get("ponto_focal_email", ""),
        )

    def perform_update(self, serializer):
        """Atualiza a participação através do service de domínio."""
        serializer.instance = self.service_class().atualizar(
            serializer.instance, **serializer.validated_data
        )

    def perform_destroy(self, instance):
        """Exclui a participação através do service de domínio."""
        self.service_class().excluir(instance)

    @extend_schema(
        summary="Vincula polos a uma edição em massa",
        tags=["Definições de Polos"],
        request=VincularEmMassaSerializer,
        responses={201: VincularEmMassaResponseSerializer},
    )
    @action(detail=False, methods=["post"], url_path="vincular-em-massa")
    def vincular_em_massa(self, request):
        """Vincula vários polos a uma edição."""
        entrada = VincularEmMassaSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        dados = entrada.validated_data
        polos = self._obter_polos_selecionados(dados["polos"])
        edicao = self._obter_recurso_por_uuid(
            Edicao,
            dados["edicao"],
            "edicao",
            EDICAO_NAO_ENCONTRADA,
        )
        resultado = self.service_class().vincular_em_massa(
            polos, edicao, dados["projecao_inscritos"]
        )
        return Response(
            {
                "criadas": DefinicaoPoloSerializer(
                    resultado["criadas"], many=True
                ).data,
                "ignorados": [polo.uuid for polo in resultado["ignorados"]],
            },
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(
        summary="Altera o tipo de polos em massa",
        description=(
            "Altera o tipo de cada polo para sua edição específica. Itens "
            "sem edição são ignorados e retornados na lista de ignorados."
        ),
        tags=["Definições de Polos"],
        request=AlterarTipoEmMassaSerializer,
        responses={200: AlterarTipoEmMassaRespostaSerializer},
    )
    @action(detail=False, methods=["post"], url_path="alterar-tipo-em-massa")
    def alterar_tipo_em_massa(self, request):
        """Altera tipos para polos e edições específicas em massa."""
        entrada = AlterarTipoEmMassaSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        operacoes = []
        for item in entrada.validated_data:
            polo = self._obter_recurso_por_uuid(
                Polo,
                item["polo_uuid"],
                "polo_uuid",
                "Polo não encontrado.",
            )
            edicao = None
            if item["edicao"] is not None:
                edicao = self._obter_recurso_por_uuid(
                    Edicao,
                    item["edicao"],
                    "edicao",
                    EDICAO_NAO_ENCONTRADA,
                )
            operacoes.append(
                {"polo": polo, "edicao": edicao, "tipo": item["tipo"]}
            )

        resultado = self.service_class().alterar_tipo_em_massa(operacoes)
        return Response(
            {
                "mensagem": resultado["mensagem"],
                "alterados": AlterarTipoEmMassaAlteradoSerializer(
                    [
                        {
                            "polo_uuid": definicao.polo.uuid,
                            "edicao_uuid": definicao.edicao.uuid,
                            "tipo": definicao.tipo,
                        }
                        for definicao in resultado["alterados"]
                    ],
                    many=True,
                ).data,
                "ignorados": AlterarTipoEmMassaIgnoradoSerializer(
                    resultado["ignorados"], many=True
                ).data,
            }
        )

    @extend_schema(
        summary="Altera a edição de definições em massa",
        tags=["Definições de Polos"],
        request=AlterarEdicaoEmMassaSerializer,
        responses={200: DefinicaoPoloSerializer(many=True)},
    )
    @action(detail=False, methods=["post"], url_path="alterar-edicao-em-massa")
    def alterar_edicao_em_massa(self, request):
        """Altera a edição de várias definições."""
        entrada = AlterarEdicaoEmMassaSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        dados = entrada.validated_data
        definicoes = self._obter_definicoes_selecionadas(dados["definicoes"])
        edicao_destino = self._obter_recurso_por_uuid(
            Edicao,
            dados["edicao_destino"],
            "edicao_destino",
            EDICAO_NAO_ENCONTRADA,
        )
        definicoes = self.service_class().alterar_edicao_em_massa(
            definicoes, edicao_destino
        )
        return Response(DefinicaoPoloSerializer(definicoes, many=True).data)


