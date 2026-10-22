"""Endpoint de consulta dos perfis RBAC disponíveis."""

from typing import cast

from django.contrib.auth.models import Group
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.api.serializers.perfil_serializer import PerfilSerializer
from apps.core.permission_catalog import PERFIS, detalhar_permissoes
from apps.core.permissions import PermissaoConsultaPerfis


class PerfisView(APIView):
    """Lista os perfis configurados para seleção na interface cliente."""

    permission_classes = [PermissaoConsultaPerfis]

    @extend_schema(
        tags=["Permissões"],
        summary="Lista perfis disponíveis",
        description=(
            "Retorna os grupos RBAC disponíveis e as permissões associadas."
        ),
        responses={
            200: PerfilSerializer(many=True),
            401: OpenApiResponse(description="Não autenticado."),
            403: OpenApiResponse(description="Sem permissão para consultar."),
        },
    )
    def get(self, request: Request) -> Response:
        """Retorna grupos e respectivas permissões em ordem estável."""
        codigos = [str(perfil["codigo"]) for perfil in PERFIS]
        grupos = {
            grupo.name: grupo
            for grupo in Group.objects.filter(name__in=codigos)
        }
        dados = []
        for perfil in PERFIS:
            codigo = str(perfil["codigo"])
            grupo = grupos.get(codigo)
            if grupo is None:
                continue
            permissoes = cast(tuple[str, ...], perfil["permissoes"])
            dados.append(
                {
                    "id": grupo.pk,
                    "codigo": codigo,
                    "nome": str(perfil["nome"]),
                    "descricao": str(perfil["descricao"]),
                    "permissoes": detalhar_permissoes(permissoes),
                }
            )
        return Response(
            PerfilSerializer(dados, many=True).data,
            status=status.HTTP_200_OK,
        )
