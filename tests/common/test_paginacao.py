"""Testes dos utilitários compartilhados de paginação HTTP."""

from django.http import HttpRequest
from django.test import TestCase

from common.paginacao import (
    TAMANHO_PAGINA_MAXIMO,
    extrair_parametro_inteiro,
    serializar_lista_paginada,
)
from usuarios.models import CargoPermitidoModel


class PaginacaoTests(TestCase):
    """Valida leitura de parâmetros e montagem de payload paginado."""

    def test_deve_retornar_padrao_quando_parametro_ausente(self) -> None:
        """Garante valor padrão quando query string não informa o parâmetro."""
        request = HttpRequest()
        request.GET = {}

        valor = extrair_parametro_inteiro(request, "page", padrao=1)

        self.assertEqual(valor, 1)

    def test_deve_retornar_none_para_parametro_invalido(self) -> None:
        """Garante ``None`` quando o parâmetro não for inteiro válido."""
        request = HttpRequest()
        request.GET = {"page": "abc"}

        valor = extrair_parametro_inteiro(request, "page", padrao=1)

        self.assertIsNone(valor)

    def test_deve_limitar_page_size_maximo(self) -> None:
        """Garante que ``pageSize`` acima do máximo seja limitado."""
        for indice in range(150):
            CargoPermitidoModel.objects.create(
                codigo_cargo=10_000 + indice,
                descricao_cargo=f"Cargo {indice}",
            )

        request = HttpRequest()
        request.GET = {"page": "1", "pageSize": "500"}

        def serializar_cargo(cargo: CargoPermitidoModel) -> dict[str, str]:
            return {"id": str(cargo.id)}

        payload = serializar_lista_paginada(
            request,
            CargoPermitidoModel.objects.all(),
            serializar_cargo,
        )

        self.assertIsNotNone(payload)
        assert payload is not None
        self.assertEqual(payload["pageSize"], TAMANHO_PAGINA_MAXIMO)
        self.assertEqual(len(payload["results"]), TAMANHO_PAGINA_MAXIMO)
