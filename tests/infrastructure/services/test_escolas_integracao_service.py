"""Testes do cliente HTTP de escolas na SME Integração API."""

from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase
from requests import exceptions as excecoes_requests

from infrastructure.services.escolas_integracao_service import (
    CODIGO_CARGO_DIRETOR_ESCOLA,
    EscolasIntegracaoConfigError,
    EscolasIntegracaoIndisponivelError,
    EscolasIntegracaoService,
    SIGLAS_TIPO_UE_RECREIO,
    _carregar_properties,
    _inteiro_do_ambiente,
    codigo_cargo_diretor_escola,
)


class InteiroDoAmbienteTests(SimpleTestCase):
    """Valida leitura de inteiros positivos a partir do ambiente."""

    def test_retorna_padrao_quando_variavel_ausente(self) -> None:
        """Garante fallback quando a variável está vazia."""
        with patch.dict("os.environ", {"VAR_INT_TESTE": ""}, clear=False):
            self.assertEqual(_inteiro_do_ambiente("VAR_INT_TESTE", 7), 7)

    def test_retorna_padrao_quando_valor_invalido(self) -> None:
        """Garante fallback quando o valor não é inteiro."""
        with patch.dict("os.environ", {"VAR_INT_TESTE": "abc"}, clear=False):
            self.assertEqual(_inteiro_do_ambiente("VAR_INT_TESTE", 7), 7)

    def test_aplica_minimo_um(self) -> None:
        """Garante que valores zero/negativos viram 1."""
        with patch.dict("os.environ", {"VAR_INT_TESTE": "0"}, clear=False):
            self.assertEqual(_inteiro_do_ambiente("VAR_INT_TESTE", 7), 1)


class CodigoCargoDiretorEscolaTests(SimpleTestCase):
    """Valida leitura do código via arquivo ``.properties``."""

    def tearDown(self) -> None:
        """Limpa cache entre testes que alteram o arquivo/mocked path."""
        codigo_cargo_diretor_escola.cache_clear()

    def test_le_valor_do_arquivo_properties(self) -> None:
        """Garante leitura de ``codigo.cargo.diretor.escola`` no properties."""
        self.assertEqual(
            codigo_cargo_diretor_escola(),
            CODIGO_CARGO_DIRETOR_ESCOLA,
        )

    def test_usa_padrao_quando_arquivo_ausente(self) -> None:
        """Garante fallback 3360 quando o arquivo não existe."""
        from pathlib import Path

        with patch(
            "infrastructure.services.escolas_integracao_service._ARQUIVO_PROPERTIES",
            Path("/tmp/arquivo-inexistente-escolas.properties"),
        ):
            codigo_cargo_diretor_escola.cache_clear()
            self.assertEqual(
                codigo_cargo_diretor_escola(),
                CODIGO_CARGO_DIRETOR_ESCOLA,
            )

    def test_usa_padrao_quando_valor_invalido(self) -> None:
        """Garante fallback quando a chave não é inteira."""
        with patch(
            "infrastructure.services.escolas_integracao_service._carregar_properties",
            return_value={"codigo.cargo.diretor.escola": "abc"},
        ):
            codigo_cargo_diretor_escola.cache_clear()
            self.assertEqual(
                codigo_cargo_diretor_escola(),
                CODIGO_CARGO_DIRETOR_ESCOLA,
            )

    def test_carregar_properties_ignora_comentarios(self) -> None:
        """Garante parser de chave=valor ignorando linhas ``#``."""
        from pathlib import Path
        from tempfile import NamedTemporaryFile

        with NamedTemporaryFile(
            "w",
            suffix=".properties",
            encoding="utf-8",
            delete=False,
        ) as tmp:
            tmp.write("# comentario\n")
            tmp.write("codigo.cargo.diretor.escola=9999\n")
            caminho = Path(tmp.name)

        try:
            self.assertEqual(
                _carregar_properties(caminho),
                {"codigo.cargo.diretor.escola": "9999"},
            )
        finally:
            caminho.unlink(missing_ok=True)


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

    def test_exige_configuracao_sem_chave(self) -> None:
        """Garante erro quando apenas a chave está ausente."""
        servico = EscolasIntegracaoService(
            base_url="https://integracao.test",
            api_eol_key="",
        )

        with self.assertRaises(EscolasIntegracaoConfigError):
            servico._garantir_configuracao()

    def test_exige_configuracao(self) -> None:
        """Garante erro quando URL ou chave não estão configuradas."""
        servico = EscolasIntegracaoService(base_url="", api_eol_key="")

        with self.assertRaises(EscolasIntegracaoConfigError):
            servico.listar_todas_unidades()

    def test_cabecalhos_e_timeouts(self) -> None:
        """Garante montagem dos cabeçalhos e timeouts do cliente."""
        self.assertEqual(
            self.servico._cabecalhos(),
            {"x-api-eol-key": "chave-teste"},
        )
        self.assertEqual(self.servico._timeouts(), (10, 30))

    def test_requisicao_converte_falha_de_rede(self) -> None:
        """Garante mapeamento de RequestException para erro de domínio."""
        with patch(
            "infrastructure.services.escolas_integracao_service.requests.request",
            side_effect=excecoes_requests.Timeout(),
        ):
            with self.assertRaises(EscolasIntegracaoIndisponivelError):
                self.servico._requisicao(
                    "GET",
                    "https://integracao.test/api/escolas/todas-unidades",
                )

    def test_listar_todas_unidades_propaga_indisponibilidade(self) -> None:
        """Garante erro amigável quando a API responde HTTP 5xx."""
        resposta = MagicMock()
        resposta.status_code = 503
        resposta.ok = False

        with patch.object(self.servico, "_requisicao", return_value=resposta):
            with self.assertRaises(EscolasIntegracaoIndisponivelError):
                self.servico.listar_todas_unidades()

    def test_listar_todas_unidades_json_invalido(self) -> None:
        """Garante erro quando o corpo não é JSON válido."""
        resposta = MagicMock()
        resposta.status_code = 200
        resposta.ok = True
        resposta.json.side_effect = ValueError("json inválido")

        with patch.object(self.servico, "_requisicao", return_value=resposta):
            with self.assertRaises(EscolasIntegracaoIndisponivelError):
                self.servico.listar_todas_unidades()

    def test_listar_todas_unidades_formato_inesperado(self) -> None:
        """Garante erro quando a resposta não é uma lista."""
        resposta = MagicMock()
        resposta.status_code = 200
        resposta.ok = True
        resposta.json.return_value = {"itens": []}

        with patch.object(self.servico, "_requisicao", return_value=resposta):
            with self.assertRaises(EscolasIntegracaoIndisponivelError):
                self.servico.listar_todas_unidades()

    def test_listar_todas_unidades_filtra_itens_nao_dict(self) -> None:
        """Garante que apenas dicionários são retornados."""
        resposta = MagicMock()
        resposta.status_code = 200
        resposta.ok = True
        resposta.json.return_value = [
            {"codigoEscola": "1"},
            "invalido",
            10,
            {"codigoEscola": "2"},
        ]

        with patch.object(self.servico, "_requisicao", return_value=resposta):
            unidades = self.servico.listar_todas_unidades()

        self.assertEqual(
            [item["codigoEscola"] for item in unidades],
            ["1", "2"],
        )

    def test_obter_dados_unidade_retorna_none_em_404(self) -> None:
        """Garante None quando a unidade não existe."""
        resposta = MagicMock()
        resposta.status_code = 404
        resposta.ok = False

        with patch.object(self.servico, "_requisicao", return_value=resposta):
            self.assertIsNone(self.servico.obter_dados_unidade("019999"))

    def test_obter_dados_unidade_propaga_5xx(self) -> None:
        """Garante erro amigável em falha HTTP 5xx."""
        resposta = MagicMock()
        resposta.status_code = 502
        resposta.ok = False

        with patch.object(self.servico, "_requisicao", return_value=resposta):
            with self.assertRaises(EscolasIntegracaoIndisponivelError):
                self.servico.obter_dados_unidade("019242")

    def test_obter_dados_unidade_json_invalido(self) -> None:
        """Garante erro quando os dados não são JSON válido."""
        resposta = MagicMock()
        resposta.status_code = 200
        resposta.ok = True
        resposta.json.side_effect = ValueError("json inválido")

        with patch.object(self.servico, "_requisicao", return_value=resposta):
            with self.assertRaises(EscolasIntegracaoIndisponivelError):
                self.servico.obter_dados_unidade("019242")

    def test_obter_dados_unidade_retorna_payload(self) -> None:
        """Garante retorno do dicionário quando a API responde 200."""
        resposta = MagicMock()
        resposta.status_code = 200
        resposta.ok = True
        resposta.json.return_value = {"nome": "EMEI OK", "cep": 12345678}

        with patch.object(self.servico, "_requisicao", return_value=resposta):
            dados = self.servico.obter_dados_unidade("019242")

        self.assertEqual(dados, {"nome": "EMEI OK", "cep": 12345678})

    def test_obter_dados_unidade_formato_inesperado(self) -> None:
        """Garante erro quando o payload não é um dicionário."""
        resposta = MagicMock()
        resposta.status_code = 200
        resposta.ok = True
        resposta.json.return_value = ["lista"]

        with patch.object(self.servico, "_requisicao", return_value=resposta):
            with self.assertRaises(EscolasIntegracaoIndisponivelError):
                self.servico.obter_dados_unidade("019242")

    def test_obter_nome_diretor_retorna_vazio_em_204(self) -> None:
        """Garante tratamento de ausência de diretor (HTTP 204)."""
        resposta = MagicMock()
        resposta.status_code = 204
        resposta.content = b""
        resposta.ok = True

        with patch.object(self.servico, "_requisicao", return_value=resposta):
            nome = self.servico.obter_nome_diretor("019411")

        self.assertEqual(nome, "")

    def test_obter_nome_diretor_retorna_vazio_em_404(self) -> None:
        """Garante string vazia quando o cargo não é encontrado."""
        resposta = MagicMock()
        resposta.status_code = 404
        resposta.ok = False

        with patch.object(self.servico, "_requisicao", return_value=resposta):
            self.assertEqual(self.servico.obter_nome_diretor("019411"), "")

    def test_obter_nome_diretor_propaga_5xx(self) -> None:
        """Garante erro amigável quando a consulta do diretor falha."""
        resposta = MagicMock()
        resposta.status_code = 500
        resposta.ok = False

        with patch.object(self.servico, "_requisicao", return_value=resposta):
            with self.assertRaises(EscolasIntegracaoIndisponivelError):
                self.servico.obter_nome_diretor("019242")

    def test_obter_nome_diretor_conteudo_vazio(self) -> None:
        """Garante string vazia quando a resposta 200 não tem corpo."""
        resposta = MagicMock()
        resposta.status_code = 200
        resposta.ok = True
        resposta.content = b""

        with patch.object(self.servico, "_requisicao", return_value=resposta):
            self.assertEqual(self.servico.obter_nome_diretor("019242"), "")

    def test_obter_nome_diretor_json_invalido(self) -> None:
        """Garante erro quando o cargo não retorna JSON válido."""
        resposta = MagicMock()
        resposta.status_code = 200
        resposta.ok = True
        resposta.content = b"{}"
        resposta.json.side_effect = ValueError("json inválido")

        with patch.object(self.servico, "_requisicao", return_value=resposta):
            with self.assertRaises(EscolasIntegracaoIndisponivelError):
                self.servico.obter_nome_diretor("019242")

    def test_obter_nome_diretor_lista_vazia_ou_primeiro_invalido(self) -> None:
        """Garante string vazia para lista vazia ou item não-dicionário."""
        resposta_vazia = MagicMock()
        resposta_vazia.status_code = 200
        resposta_vazia.ok = True
        resposta_vazia.content = b"[]"
        resposta_vazia.json.return_value = []

        resposta_invalida = MagicMock()
        resposta_invalida.status_code = 200
        resposta_invalida.ok = True
        resposta_invalida.content = b"[1]"
        resposta_invalida.json.return_value = ["servidor"]

        with patch.object(
            self.servico,
            "_requisicao",
            side_effect=[resposta_vazia, resposta_invalida],
        ):
            self.assertEqual(self.servico.obter_nome_diretor("019242"), "")
            self.assertEqual(self.servico.obter_nome_diretor("019243"), "")

    def test_obter_nome_diretor_extrai_primeiro_servidor(self) -> None:
        """Garante extração de ``nomeServidor`` do cargo 3360."""
        resposta = MagicMock()
        resposta.status_code = 200
        resposta.ok = True
        resposta.content = b"[{}]"
        resposta.json.return_value = [
            {"nomeServidor": "MARIA DIRETORA", "cargo": "DIRETOR DE ESCOLA"},
        ]

        with patch.object(
            self.servico,
            "_requisicao",
            return_value=resposta,
        ) as mock_req:
            nome = self.servico.obter_nome_diretor("019242")

        self.assertEqual(nome, "MARIA DIRETORA")
        mock_req.assert_called_once_with(
            "GET",
            (
                "https://integracao.test/api/escolas/019242/"
                f"funcionarios/cargos/{CODIGO_CARGO_DIRETOR_ESCOLA}"
            ),
        )

    def test_formatar_cep_vazio_e_parcial(self) -> None:
        """Garante normalização e retorno vazio para CEP sem dígitos."""
        self.assertEqual(self.servico._formatar_cep(None), "")
        self.assertEqual(self.servico._formatar_cep("abc"), "")
        self.assertEqual(self.servico._formatar_cep("123"), "00000-123")

    def test_montar_endereco_variantes(self) -> None:
        """Garante montagem com número/bairro e cenários parciais."""
        completo = self.servico._montar_endereco(
            {
                "tipoLogradouro": "Rua",
                "logradouro": "A",
                "numero": "10",
                "bairro": "Centro",
            },
        )
        self.assertEqual(completo, "Rua A, 10 - Centro")

        so_bairro = self.servico._montar_endereco({"bairro": "Centro"})
        self.assertEqual(so_bairro, "Centro")

        so_numero = self.servico._montar_endereco({"numero": "15"})
        self.assertEqual(so_numero, "15")

    def test_enriquecer_unidade_usa_fallback_quando_apis_falham(self) -> None:
        """Garante uso dos dados básicos quando dados/diretor falham."""
        unidade = {
            "codigoEscola": "019242",
            "nomeEscola": "EMEI BASICA",
            "siglaTipoEscola": "EMEI",
            "nomeDRE": "DRE BASICA",
            "siglaDRE": "DRE B",
            "codigoDRE": "1",
        }

        with (
            patch.object(
                self.servico,
                "obter_dados_unidade",
                side_effect=EscolasIntegracaoIndisponivelError("dados"),
            ),
            patch.object(
                self.servico,
                "obter_nome_diretor",
                side_effect=EscolasIntegracaoIndisponivelError("diretor"),
            ),
        ):
            resultado = self.servico._enriquecer_unidade(unidade)

        self.assertEqual(resultado["codigoEol"], "019242")
        self.assertEqual(resultado["nomeEscola"], "EMEI BASICA")
        self.assertEqual(resultado["nomeDiretor"], "")
        self.assertEqual(resultado["cep"], "")
        self.assertEqual(resultado["gestao"], "Direta")

    def test_enriquecer_unidade_sem_codigo_eol(self) -> None:
        """Garante payload básico quando a unidade não tem EOL."""
        resultado = self.servico._enriquecer_unidade(
            {
                "nomeEscola": "SEM EOL",
                "siglaTipoEscola": "EMEF",
                "nomeDRE": "DRE",
            },
        )

        self.assertEqual(resultado["codigoEol"], "")
        self.assertEqual(resultado["nomeEscola"], "SEM EOL")
        self.assertEqual(resultado["nomeDiretor"], "")

    def test_enriquecer_unidades_lista_vazia(self) -> None:
        """Garante retorno imediato para lista vazia."""
        self.assertEqual(self.servico.enriquecer_unidades([]), [])

    def test_enriquecer_unidades_usa_payload_basico_em_falha_inesperada(
        self,
    ) -> None:
        """Garante fallback mínimo quando o futuro lança Exception genérica."""
        unidade = {
            "codigoEscola": "019242",
            "nomeEscola": "EMEI FALLBACK",
            "siglaTipoEscola": "EMEI",
            "nomeDRE": "DRE F",
            "siglaDRE": "DF",
            "codigoDRE": "9",
        }

        with patch.object(
            self.servico,
            "_enriquecer_unidade",
            side_effect=RuntimeError("falha inesperada"),
        ):
            resultado = self.servico.enriquecer_unidades([unidade])

        self.assertEqual(len(resultado), 1)
        self.assertEqual(
            resultado[0],
            {
                "codigoEol": "019242",
                "nomeEscola": "EMEI FALLBACK",
                "siglaTipoEscola": "EMEI",
                "nomeDre": "DRE F",
                "siglaDre": "DF",
                "codigoDre": "9",
                "email": "",
                "telefone": "",
                "cep": "",
                "endereco": "",
                "nomeDiretor": "",
                "gestao": "Direta",
            },
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

    def test_listar_unidades_diretas_recreio_respeita_limite(self) -> None:
        """Garante aplicação do parâmetro ``limite`` antes do enriquecimento."""
        unidades = [
            {
                "codigoEscola": "1",
                "nomeEscola": "A",
                "siglaTipoEscola": "EMEF",
            },
            {
                "codigoEscola": "2",
                "nomeEscola": "B",
                "siglaTipoEscola": "EMEF",
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
                "enriquecer_unidades",
                return_value=[{"codigoEol": "1"}],
            ) as mock_enriquecer,
        ):
            self.servico.listar_unidades_diretas_recreio(limite=1)

        mock_enriquecer.assert_called_once()
        self.assertEqual(len(mock_enriquecer.call_args.args[0]), 1)
