"""Testes do cliente HTTP de escolas na SME Integração API."""

from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from infrastructure.services.escolas_integracao_service import (
    CODIGO_CARGO_DIRETOR_ESCOLA,
    EscolasIntegracaoConfigError,
    EscolasIntegracaoIndisponivelError,
    EscolasIntegracaoService,
    SIGLAS_TIPO_UE_RECREIO,
)


class EscolasIntegracaoServiceTests(SimpleTestCase):
    """Valida filtros, enriquecimento e tratamento de erros do serviço."""

    def setUp(self) -> None:
        """Configura serviço com URL e chave explícitas."""
        self.servico = EscolasIntegracaoService(
            base_url="https://integracao.test",
            api_eol_key="chave-teste",
            max_workers=2,
        )

    def test_filtrar_unidades_recreio_por_sigla(self) -> None:
        """Garante retenção apenas das siglas do Recreio nas Férias."""
        unidades = [
            {"codigoEscola": "1", "siglaTipoEscola": "EMEF"},
            {"codigoEscola": "2", "siglaTipoEscola": "ESC.PART."},
            {"codigoEscola": "3", "siglaTipoEscola": " CEU EMEI "},
            {"codigoEscola": "4", "siglaTipoEscola": "CEU AT COMPL"},
        ]

        filtradas = self.servico.filtrar_unidades_recreio(unidades)

        self.assertEqual(
            [item["codigoEscola"] for item in filtradas],
            ["1", "3"],
        )
        self.assertTrue(SIGLAS_TIPO_UE_RECREIO)

    def test_obter_nome_diretor_retorna_vazio_em_204(self) -> None:
        """Garante tratamento de ausência de diretor (HTTP 204)."""
        resposta = MagicMock()
        resposta.status_code = 204
        resposta.content = b""
        resposta.ok = True

        with patch.object(self.servico, "_requisicao", return_value=resposta):
            nome = self.servico.obter_nome_diretor("019411")

        self.assertEqual(nome, "")

    def test_obter_nome_diretor_extrai_primeiro_servidor(self) -> None:
        """Garante extração de ``nomeServidor`` do cargo 3360."""
        resposta = MagicMock()
        resposta.status_code = 200
        resposta.ok = True
        resposta.content = b"[{}]"
        resposta.json.return_value = [
            {"nomeServidor": "MARIA DIRETORA", "cargo": "DIRETOR DE ESCOLA"},
        ]

        with patch.object(self.servico, "_requisicao", return_value=resposta) as mock_req:
            nome = self.servico.obter_nome_diretor("019242")

        self.assertEqual(nome, "MARIA DIRETORA")
        mock_req.assert_called_once_with(
            "GET",
            (
                "https://integracao.test/api/escolas/019242/"
                f"funcionarios/cargos/{CODIGO_CARGO_DIRETOR_ESCOLA}"
            ),
        )

    def test_listar_unidades_diretas_recreio_enriquece_em_paralelo(self) -> None:
        """Garante montagem do payload final com dados e diretor."""
        unidades = [
            {
                "codigoEscola": "019242",
                "nomeEscola": "EMEI TESTE",
                "siglaTipoEscola": "EMEI",
                "nomeDRE": "DRE TESTE",
                "siglaDRE": "DRE TESTE",
                "codigoDRE": "100001",
            },
            {
                "codigoEscola": "999999",
                "nomeEscola": "PARTICULAR",
                "siglaTipoEscola": "ESC.PART.",
            },
        ]

        with (
            patch.object(
                self.servico,
                "listar_todas_unidades",
                return_value=unidades,
            ),
            patch.object(
                self.servico,
                "obter_dados_unidade",
                return_value={
                    "nome": "EMEI TESTE",
                    "siglaTipoEscola": "EMEI",
                    "nomeDRE": "DRE TESTE",
                    "siglaDRE": "DRE TESTE",
                    "codigoDRE": "100001",
                    "email": "emei@escola.sp.gov.br",
                    "telefone": "1133334444",
                    "cep": 12345678,
                    "tipoLogradouro": "Rua",
                    "logradouro": "DAS FLORES",
                    "numero": "10",
                    "bairro": "CENTRO",
                },
            ),
            patch.object(
                self.servico,
                "obter_nome_diretor",
                return_value="JOANA DIRETORA",
            ),
        ):
            resultado = self.servico.listar_unidades_diretas_recreio()

        self.assertEqual(len(resultado), 1)
        self.assertEqual(
            resultado[0],
            {
                "codigoEol": "019242",
                "nomeEscola": "EMEI TESTE",
                "siglaTipoEscola": "EMEI",
                "nomeDre": "DRE TESTE",
                "siglaDre": "DRE TESTE",
                "codigoDre": "100001",
                "email": "emei@escola.sp.gov.br",
                "telefone": "1133334444",
                "cep": "12345-678",
                "endereco": "Rua DAS FLORES, 10 - CENTRO",
                "nomeDiretor": "JOANA DIRETORA",
                "gestao": "Direta",
            },
        )

    def test_exige_configuracao(self) -> None:
        """Garante erro quando URL ou chave não estão configuradas."""
        servico = EscolasIntegracaoService(base_url="", api_eol_key="")

        with self.assertRaises(EscolasIntegracaoConfigError):
            servico.listar_todas_unidades()

    def test_listar_todas_unidades_propaga_indisponibilidade(self) -> None:
        """Garante erro amigável quando a API responde HTTP 5xx."""
        resposta = MagicMock()
        resposta.status_code = 503
        resposta.ok = False

        with patch.object(self.servico, "_requisicao", return_value=resposta):
            with self.assertRaises(EscolasIntegracaoIndisponivelError):
                self.servico.listar_todas_unidades()
