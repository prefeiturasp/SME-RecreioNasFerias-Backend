"""Paginação customizada reutilizável para todas as Views do projeto."""

from rest_framework.exceptions import NotFound
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.serializers import ValidationError

DEFAULT_PAGE_SIZE = 10


class PaginacaoCustomizada(PageNumberPagination):
    """
    Paginação customizada que permite:
    - Configurar a quantidade de registros por página
    - Desabilitar a paginação para retornar todos os registros via query param
    - Ser utilizada em ViewSets e @actions
    - Retorna 400 (Bad Request) em vez de 404 para páginas inválidas
    - Centraliza toda lógica de validação e formato de resposta
    
    Exemplo de uso em ViewSet:
        class MeuViewSet(viewsets.ModelViewSet):
            queryset = MinhaClasse.objects.all()
            pagination_class = PaginacaoCustomizada
    
    Exemplo de uso em @action:
        @action(detail=False, methods=['get'])
        def meu_endpoint(self, request):
            paginacao = PaginacaoCustomizada()
            resultado = paginacao.paginate_queryset(
                queryset=MinhaClasse.objects.all(),
                request=request,
                view=self
            )
            serializer = MeuSerializer(resultado, many=True)
            return paginacao.get_paginated_response(serializer.data)
    
    Query Parameters:
        - page: Número da página (padrão: 1)
        - page_size: Registros por página (padrão: 10)
        - desabilita_paginacao: Se true, retorna todos os registros sem paginação
    """

    page_size_query_param = "page_size"
    page_size_query_description = "Quantidade de registros por página"
    max_page_size = 1000

    def __init__(self, page_size: int = DEFAULT_PAGE_SIZE):
        """
        Inicializa a paginação customizada.

        Args:
            page_size: Quantidade de registros por página (padrão: 10)
        """
        super().__init__()
        self.page_size = page_size
        self.desabilita_paginacao = False

    def paginate_queryset(self, queryset, request, view=None):
        """
        Pagina o queryset ou retorna todos os registros baseado no query param.

        Lê automaticamente o parâmetro 'desabilita_paginacao' da requisição.
        Se desabilita_paginacao=true, retorna todos os registros sem paginação.

        Args:
            queryset: QuerySet a ser paginado
            request: Requisição HTTP
            view: View que está fazendo a paginação

        Returns:
            Lista de registros paginados ou todos os registros

        Raises:
            ValidationError: Se a página solicitada é inválida (retorna 400)
        """
        # Ler automaticamente o parâmetro da requisição
        desabilita_paginacao = (
            request.query_params.get("desabilita_paginacao", "false").lower()
            == "true"
        )
        self.desabilita_paginacao = desabilita_paginacao

        # Se paginação desabilitada, retorna todos os registros
        if self.desabilita_paginacao:
            return list(queryset)

        # Caso contrário, aplica a paginação padrão
        # Captura exceção 404 e converte para 400 (Bad Request)
        try:
            return super().paginate_queryset(queryset, request, view)
        except NotFound as exc:
            # Converte 404 em 400 para páginas inválidas
            raise ValidationError(
                {
                    "page": str(exc.detail)
                    if hasattr(exc, "detail")
                    else "Página solicitada é inválida."
                }
            ) from exc

    def get_paginated_response(self, data):
        """
        Retorna a resposta paginada com metadados ou apenas os dados.

        Se desabilita_paginacao for True, retorna os dados em um Response simples.
        Caso contrário, retorna o formato padrão com metadados de paginação.

        Args:
            data: Dados serializados a serem retornados

        Returns:
            Response formatada com ou sem metadados de paginação
        """
        if self.desabilita_paginacao:
            # Quando paginação está desabilitada, retorna os dados em um Response simples
            return Response(data)

        # Caso contrário, aplica a formatação padrão de paginação
        return super().get_paginated_response(data)


