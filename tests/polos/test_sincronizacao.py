"""Testes da sincronização de unidades diretas na tabela ``polos``."""

from unittest.mock import MagicMock, patch

from django.core.exceptions import ValidationError
from django.test import TestCase

from polos.models import GESTAO_DIRETA, GESTAO_PARCEIRA, Polo, STATUS_ATIVO
from polos.sincronizacao import (
    _TAMANHO_LOTE_SINCRONIZACAO,
    _persistir_lote,
    _resolver_nome_polo,
    sincronizar_unidades_diretas,
)


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

    def test_deve_registrar_sync_quando_nao_ha_unidades_novas(self) -> None:
        """Garante registro da sync mesmo sem criar polos novos."""
        Polo.objects.create(
            gestao=GESTAO_DIRETA,
            codigo_eol="019241",
            nome_polo="ESCOLA A",
            dre="DRE TESTE",
            tipo_ue="EMEF",
            quantidade_maxima_alunos=1,
        )
        filtradas = [self._unidade_basica("019241", "ESCOLA A")]
        servico = self._servico_mock(filtradas, [])

        resultado = sincronizar_unidades_diretas(servico=servico)

        self.assertTrue(resultado.executada)
        self.assertEqual(resultado.total_novos, 0)
        self.assertEqual(resultado.total_ja_existentes, 1)
        servico.enriquecer_unidades.assert_not_called()

    def test_deve_respeitar_limite_de_unidades_filtradas(self) -> None:
        """Garante aplicação do ``limite`` antes do diff/enriquecimento."""
        filtradas = [
            self._unidade_basica("019241", "ESCOLA A"),
            self._unidade_basica("019242", "ESCOLA B"),
        ]
        enriquecidas = [self._unidade_enriquecida("019241", "ESCOLA A")]
        servico = self._servico_mock(filtradas, enriquecidas)

        resultado = sincronizar_unidades_diretas(servico=servico, limite=1)

        self.assertEqual(resultado.total_consultados, 1)
        self.assertEqual(resultado.total_novos, 1)

    def test_resolver_nome_polo_usa_fallback_e_sufixos_em_colisao(self) -> None:
        """Garante nome padrão e sufixos ``(eol)`` / ``(eol-N)`` em colisão."""
        self.assertEqual(_resolver_nome_polo("", "019250"), "Unidade 019250")

        Polo.objects.create(
            gestao=GESTAO_DIRETA,
            codigo_eol="019251",
            nome_polo="ESCOLA COLISAO",
            dre="DRE TESTE",
            tipo_ue="EMEF",
            quantidade_maxima_alunos=1,
        )
        self.assertEqual(
            _resolver_nome_polo("ESCOLA COLISAO", "019252"),
            "ESCOLA COLISAO (019252)",
        )

        Polo.objects.create(
            gestao=GESTAO_DIRETA,
            codigo_eol="019252",
            nome_polo="ESCOLA COLISAO (019252)",
            dre="DRE TESTE",
            tipo_ue="EMEF",
            quantidade_maxima_alunos=1,
        )
        Polo.objects.create(
            gestao=GESTAO_DIRETA,
            codigo_eol="019253",
            nome_polo="ESCOLA COLISAO (019252-2)",
            dre="DRE TESTE",
            tipo_ue="EMEF",
            quantidade_maxima_alunos=1,
        )
        self.assertEqual(
            _resolver_nome_polo("ESCOLA COLISAO", "019252"),
            "ESCOLA COLISAO (019252-3)",
        )

    def test_persistir_lote_ignora_eol_vazio_ou_validation_error(self) -> None:
        """Garante skip de EOL vazio e unidades com ValidationError."""
        eols: set[str] = set()
        unidade_ok = self._unidade_enriquecida("019260", "ESCOLA OK")
        unidade_sem_eol = {**unidade_ok, "codigoEol": ""}
        unidade_erro = self._unidade_enriquecida("019261", "ESCOLA ERRO")

        with patch(
            "polos.sincronizacao._mapear_unidade_para_polo",
            side_effect=[
                ValidationError("falha"),
                Polo(
                    gestao=GESTAO_DIRETA,
                    codigo_eol="019260",
                    nome_polo="ESCOLA OK",
                    dre="DRE TESTE",
                    tipo_ue="EMEF",
                    quantidade_maxima_alunos=1,
                ),
            ],
        ):
            criados = _persistir_lote(
                [unidade_sem_eol, unidade_erro, unidade_ok],
                eols,
            )

        self.assertEqual(len(criados), 1)
        self.assertEqual(criados[0].codigo_eol, "019260")
        self.assertIn("019260", eols)

    def test_deve_processar_mais_de_um_lote_de_sincronizacao(self) -> None:
        """Garante particionamento quando há mais unidades que o tamanho do lote."""
        filtradas = [
            self._unidade_basica(f"{indice:06d}", f"ESCOLA {indice}")
            for indice in range(1, _TAMANHO_LOTE_SINCRONIZACAO + 2)
        ]
        enriquecidas_lote1 = [
            self._unidade_enriquecida(f"{indice:06d}", f"ESCOLA {indice}")
            for indice in range(1, _TAMANHO_LOTE_SINCRONIZACAO + 1)
        ]
        enriquecidas_lote2 = [
            self._unidade_enriquecida(
                f"{_TAMANHO_LOTE_SINCRONIZACAO + 1:06d}",
                f"ESCOLA {_TAMANHO_LOTE_SINCRONIZACAO + 1}",
            ),
        ]
        servico = MagicMock()
        servico.listar_todas_unidades.return_value = filtradas
        servico.filtrar_unidades_recreio.side_effect = lambda unidades: unidades
        servico.enriquecer_unidades.side_effect = [
            enriquecidas_lote1,
            enriquecidas_lote2,
        ]

        resultado = sincronizar_unidades_diretas(servico=servico)

        self.assertEqual(resultado.total_novos, _TAMANHO_LOTE_SINCRONIZACAO + 1)
        self.assertEqual(servico.enriquecer_unidades.call_count, 2)

    def test_mapear_unidade_usa_nao_informado_quando_dre_ou_tipo_vazios(
        self,
    ) -> None:
        """Garante defaults de DRE/tipo UE e truncamento de telefone."""
        telefone_longo = "1" * 30
        enriquecida = {
            "codigoEol": "019270",
            "nomeEscola": "ESCOLA DEFAULTS",
            "siglaTipoEscola": "",
            "nomeDre": "",
            "siglaDre": "",
            "email": "a@b.com",
            "telefone": telefone_longo,
            "cep": "",
            "endereco": "",
            "nomeDiretor": "",
            "gestao": GESTAO_DIRETA,
        }
        servico = self._servico_mock(
            [self._unidade_basica("019270", "ESCOLA DEFAULTS")],
            [enriquecida],
        )

        resultado = sincronizar_unidades_diretas(servico=servico)

        self.assertEqual(resultado.total_novos, 1)
        polo = Polo.objects.get(codigo_eol="019270")
        self.assertEqual(polo.dre, "Não informado")
        self.assertEqual(polo.tipo_ue, "Não informado")
        self.assertEqual(len(polo.telefone_polo), 20)
