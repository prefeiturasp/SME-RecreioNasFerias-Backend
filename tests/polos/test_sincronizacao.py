"""Testes da sincronização de unidades diretas na tabela ``polos``."""

from unittest.mock import MagicMock

from django.test import TestCase

from polos.models import GESTAO_DIRETA, GESTAO_PARCEIRA, Polo, STATUS_ATIVO
from polos.sincronizacao import sincronizar_unidades_diretas


class SincronizacaoUnidadesDiretasTests(TestCase):
    """Garante inserção apenas de unidades Direta ainda inexistentes."""

    def _unidade_basica(self, codigo: str, nome: str = "ESCOLA") -> dict[str, str]:
        """Montar item no formato de ``todas-unidades``."""
        return {
            "codigoEscola": codigo,
            "nomeEscola": nome,
            "siglaTipoEscola": "EMEF",
            "nomeDRE": "DRE TESTE",
            "siglaDRE": "DRE TESTE",
            "codigoDRE": "100001",
        }

    def _unidade_enriquecida(
        self,
        codigo: str,
        nome: str = "ESCOLA",
    ) -> dict[str, str]:
        """Montar item enriquecido pronto para persistência."""
        return {
            "codigoEol": codigo,
            "nomeEscola": nome,
            "siglaTipoEscola": "EMEF",
            "nomeDre": "DRE TESTE",
            "siglaDre": "DRE TESTE",
            "codigoDre": "100001",
            "email": "escola@educacao.sp.gov.br",
            "telefone": "1133334444",
            "cep": "01234-567",
            "endereco": "Rua A, 1 - Centro",
            "nomeDiretor": "Diretor Teste",
            "gestao": GESTAO_DIRETA,
        }

    def _servico_mock(
        self,
        filtradas: list[dict[str, str]],
        enriquecidas: list[dict[str, str]],
    ) -> MagicMock:
        """Montar mock do cliente de integração."""
        servico = MagicMock()
        servico.listar_todas_unidades.return_value = filtradas
        servico.filtrar_unidades_recreio.side_effect = lambda unidades: unidades
        servico.enriquecer_unidades.return_value = enriquecidas
        return servico

    def test_deve_salvar_unidades_novas_com_gestao_direta(self) -> None:
        """Garante persistência de unidades ainda inexistentes."""
        filtradas = [
            self._unidade_basica("019241", "ESCOLA A"),
            self._unidade_basica("019242", "ESCOLA B"),
        ]
        enriquecidas = [
            self._unidade_enriquecida("019241", "ESCOLA A"),
            self._unidade_enriquecida("019242", "ESCOLA B"),
        ]
        servico = self._servico_mock(filtradas, enriquecidas)

        resultado = sincronizar_unidades_diretas(servico=servico)

        self.assertEqual(resultado.total_consultados, 2)
        self.assertEqual(resultado.total_novos, 2)
        self.assertEqual(resultado.total_ja_existentes, 0)
        self.assertEqual(Polo.objects.filter(gestao=GESTAO_DIRETA).count(), 2)
        polo = Polo.objects.get(codigo_eol="019241")
        self.assertEqual(polo.gestao, GESTAO_DIRETA)
        self.assertEqual(polo.tipo, "Pendente")
        self.assertEqual(polo.nome_polo, "ESCOLA A")
        self.assertEqual(polo.nome_gestor, "Diretor Teste")
        self.assertEqual(polo.status, STATUS_ATIVO)
        servico.enriquecer_unidades.assert_called_once()

    def test_nao_deve_duplicar_unidade_ja_existente(self) -> None:
        """Garante que segunda sincronização não reinsere EOL já salvo."""
        Polo.objects.create(
            gestao=GESTAO_DIRETA,
            codigo_eol="019241",
            nome_polo="ESCOLA A",
            dre="DRE TESTE",
            tipo_ue="EMEF",
            quantidade_maxima_alunos=1,
        )
        filtradas = [
            self._unidade_basica("019241", "ESCOLA A"),
            self._unidade_basica("019242", "ESCOLA B"),
        ]
        enriquecidas = [self._unidade_enriquecida("019242", "ESCOLA B")]
        servico = self._servico_mock(filtradas, enriquecidas)

        resultado = sincronizar_unidades_diretas(servico=servico)

        self.assertEqual(resultado.total_consultados, 2)
        self.assertEqual(resultado.total_novos, 1)
        self.assertEqual(resultado.total_ja_existentes, 1)
        self.assertEqual(Polo.objects.filter(gestao=GESTAO_DIRETA).count(), 2)
        args = servico.enriquecer_unidades.call_args.args[0]
        self.assertEqual(len(args), 1)
        self.assertEqual(args[0]["codigoEscola"], "019242")

    def test_nao_deve_considerar_polo_parceiro_como_existente(self) -> None:
        """Garante que o diff usa apenas polos com gestão Direta."""
        Polo.objects.create(
            gestao=GESTAO_PARCEIRA,
            nome_osc="OSC",
            nome_polo="ESCOLA A",
            dre="DRE TESTE",
            tipo_ue="EMEF",
            quantidade_maxima_alunos=10,
            cep="01234-567",
            endereco="Rua X",
            nome_gestor="Gestor",
            email_polo="osc@osc.org.br",
            telefone_polo="11999999999",
        )
        filtradas = [self._unidade_basica("019241", "ESCOLA DIRETA A")]
        enriquecidas = [self._unidade_enriquecida("019241", "ESCOLA DIRETA A")]
        servico = self._servico_mock(filtradas, enriquecidas)

        resultado = sincronizar_unidades_diretas(servico=servico)

        self.assertEqual(resultado.total_novos, 1)
        self.assertEqual(Polo.objects.filter(gestao=GESTAO_DIRETA).count(), 1)
        self.assertEqual(
            Polo.objects.get(codigo_eol="019241").nome_polo,
            "ESCOLA DIRETA A",
        )

    def test_deve_ignorar_segunda_sincronizacao_no_mesmo_dia(self) -> None:
        """Garante que a sync automática roda no máximo uma vez por dia."""
        filtradas = [self._unidade_basica("019241", "ESCOLA A")]
        enriquecidas = [self._unidade_enriquecida("019241", "ESCOLA A")]
        servico = self._servico_mock(filtradas, enriquecidas)

        primeiro = sincronizar_unidades_diretas(servico=servico)
        segundo = sincronizar_unidades_diretas(servico=servico)

        self.assertTrue(primeiro.executada)
        self.assertEqual(primeiro.total_novos, 1)
        self.assertFalse(segundo.executada)
        self.assertEqual(segundo.motivo_ignorada, "ja_executada_hoje")
        self.assertEqual(segundo.total_consultados, 0)
        self.assertEqual(servico.listar_todas_unidades.call_count, 1)

    def test_deve_permitir_forcar_sincronizacao_no_mesmo_dia(self) -> None:
        """Garante que ``forcar=True`` ignora o limite diário."""
        filtradas = [self._unidade_basica("019241", "ESCOLA A")]
        enriquecidas = [self._unidade_enriquecida("019241", "ESCOLA A")]
        servico = self._servico_mock(filtradas, enriquecidas)

        sincronizar_unidades_diretas(servico=servico)
        segunda = sincronizar_unidades_diretas(servico=servico, forcar=True)

        self.assertTrue(segunda.executada)
        self.assertEqual(servico.listar_todas_unidades.call_count, 2)
