"""Testes do modelo de edições."""

from datetime import date

from django.core.exceptions import ValidationError
from django.test import TestCase

from edicoes.models import Edicao


class EdicaoModelTests(TestCase):
    """Garante regras de domínio e metadados do modelo ``Edicao``."""

    def _criar_edicao_valida(self, nome: str = "Recreio Janeiro 2026") -> Edicao:
        """Cria e persiste uma edição válida para os cenários de teste.

        Args:
            nome (str): Nome da edição a ser persistida.

        Returns:
            Edicao: Instância salva no banco com períodos válidos.

        Raises:
            ValidationError: Se algum campo informado for inválido.
        """
        return Edicao.objects.create(
            nome=nome,
            periodo_edicao_inicio=date(2026, 1, 10),
            periodo_edicao_fim=date(2026, 1, 20),
            periodo_inscricoes_inicio=date(2025, 12, 1),
            periodo_inscricoes_fim=date(2025, 12, 31),
        )

    def test_cria_edicao_com_campos_obrigatorios(self):
        edicao = self._criar_edicao_valida()

        self.assertIsNotNone(edicao.id)
        self.assertEqual(edicao.nome, "Recreio Janeiro 2026")

    def test_nao_permite_nome_repetido(self):
        self._criar_edicao_valida()

        with self.assertRaisesMessage(
            ValidationError, "Erro: já existe edição com o nome cadastrado"
        ):
            self._criar_edicao_valida(nome="recreio janeiro 2026")

    def test_nao_permite_periodo_repetido(self):
        self._criar_edicao_valida(nome="Recreio Julho 2026")

        with self.assertRaisesMessage(
            ValidationError, "Erro: já existe edição no período cadastrado"
        ):
            Edicao.objects.create(
                nome="Recreio Férias Inverno 2026",
                periodo_edicao_inicio=date(2026, 1, 10),
                periodo_edicao_fim=date(2026, 1, 20),
                periodo_inscricoes_inicio=date(2026, 6, 1),
                periodo_inscricoes_fim=date(2026, 6, 20),
            )

    def test_nao_permite_periodo_edicao_invertido(self):
        with self.assertRaisesMessage(
            ValidationError,
            "Erro: a data inicial do período da edição deve ser menor ou "
            "igual à data final",
        ):
            Edicao.objects.create(
                nome="Recreio Março 2026",
                periodo_edicao_inicio=date(2026, 3, 25),
                periodo_edicao_fim=date(2026, 3, 10),
                periodo_inscricoes_inicio=date(2026, 2, 1),
                periodo_inscricoes_fim=date(2026, 2, 20),
            )

    def test_nao_permite_periodo_inscricoes_invertido(self):
        with self.assertRaisesMessage(
            ValidationError,
            "Erro: a data inicial do período das inscrições deve ser menor ou "
            "igual à data final",
        ):
            Edicao.objects.create(
                nome="Recreio Abril 2026",
                periodo_edicao_inicio=date(2026, 4, 10),
                periodo_edicao_fim=date(2026, 4, 20),
                periodo_inscricoes_inicio=date(2026, 3, 25),
                periodo_inscricoes_fim=date(2026, 3, 10),
            )

    def test_campos_de_quantidade_sao_travados_para_cadastro(self):
        campos = {
            "quantidade_inscritos",
            "quantidade_atendimento_efetivo",
            "quantidade_passeios",
            "quantidade_apresentacoes",
        }

        for nome_campo in campos:
            campo = Edicao._meta.get_field(nome_campo)
            self.assertFalse(campo.editable)
            self.assertTrue(campo.null)
            self.assertTrue(campo.blank)
