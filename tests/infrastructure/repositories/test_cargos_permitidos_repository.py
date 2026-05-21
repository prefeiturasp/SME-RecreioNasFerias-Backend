"""Testes do repositório de cargos permitidos com banco de dados."""

from django.test import TestCase

from infrastructure.repositories.cargos_permitidos_repository import (
    CargosPermitidosRepository,
)
from usuarios.models import CargoPermitidoModel


class CargosPermitidosRepositoryTests(TestCase):
    """Valida consulta ORM à tabela ``usuarios_cargos_permitidos``."""

    def setUp(self):
        self.repository = CargosPermitidosRepository()

    def test_deve_retornar_false_para_lista_vazia_sem_consultar(self):
        with self.assertNumQueries(0):
            self.assertFalse(self.repository.algum_codigo_autorizado([]))

    def test_deve_retornar_true_quando_algum_codigo_existe_no_banco(self):
        CargoPermitidoModel.objects.create(
            codigo_cargo=8800101,
            descricao_cargo="CARGO TESTE REPOSITORIO",
        )

        self.assertTrue(self.repository.algum_codigo_autorizado([8800101]))
        self.assertTrue(self.repository.algum_codigo_autorizado([9999999, 8800101]))

    def test_deve_retornar_false_quando_nenhum_codigo_existe_no_banco(self):
        CargoPermitidoModel.objects.create(
            codigo_cargo=8800102,
            descricao_cargo="OUTRO CARGO",
        )

        self.assertFalse(self.repository.algum_codigo_autorizado([8800199]))
        self.assertFalse(self.repository.algum_codigo_autorizado([8800198, 8800197]))
