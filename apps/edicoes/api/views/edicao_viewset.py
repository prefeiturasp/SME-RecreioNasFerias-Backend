"""ViewSet HTTP do domínio de edições."""

from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
)
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.edicoes.api.serializers import EdicaoSerializer
from apps.edicoes.models.edicao import Edicao
from apps.edicoes.services.edicao_service import EdicaoService


@extend_schema_view(
    list=extend_schema(
        summary="Lista edições",
        description="Lista todas as edições, atualizando seus status automáticos.",
        tags=["Edições"],
    ),
    create=extend_schema(
        summary="Cria edição",
        description="Cria uma nova edição, validando os dados e delegando a criação ao serviço de domínio.",
        tags=["Edições"],
    ),
    retrieve=extend_schema(
        summary="Recupera edição",
        description="Recupera uma edição específica pelo UUID.",
        tags=["Edições"],
    ),
    update=extend_schema(
        summary="Atualiza edição",
        description="Atualiza uma edição existente, validando os dados e delegando a atualização ao serviço de domínio.",
        tags=["Edições"],
    ),
    partial_update=extend_schema(
        summary="Atualiza parcialmente edição",
        description="Atualiza parcialmente uma edição existente, validando os dados e delegando a atualização ao serviço de domínio.",
        tags=["Edições"],
    ),
    destroy=extend_schema(
        summary="Exclui edição",
        description="Exclui uma edição existente, delegando a exclusão ao serviço de domínio.",
        tags=["Edições"],
    ),
)
class EdicaoViewSet(viewsets.ModelViewSet):
    """Expõe os casos de uso HTTP das edições."""

    queryset = Edicao.objects.all()
    serializer_class = EdicaoSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "uuid"
    service_class = EdicaoService

    def get_queryset(self):
        """Retorna as edições após atualizar seus status automáticos."""
        return self.service_class().listar()

    def perform_create(self, serializer: EdicaoSerializer) -> None:
        """Cria a edição por meio do serviço de domínio."""
        serializer.instance = self.service_class().criar(
            **serializer.validated_data
        )

    def perform_update(self, serializer: EdicaoSerializer) -> None:
        """Atualiza a edição por meio do serviço de domínio."""
        serializer.instance = self.service_class().atualizar(
            serializer.instance,
            **serializer.validated_data,
        )

    def perform_destroy(self, instance: object) -> None:
        """Exclui a edição por meio do serviço de domínio."""
        self.service_class().excluir(instance)
