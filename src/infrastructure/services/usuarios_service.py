"""
Serviço HTTP para autenticação e consulta de dados no CoreSSO.

Realiza ``POST /api/v1/autenticacao`` e ``GET /api/funcionarios/DadosSigpae/{rf}``
usando ``requests``, com timeouts de conexão e leitura configuráveis via
variáveis ``AUTH_API_*`` no ambiente.
"""

import os
import time
from typing import Any

import requests
from requests import exceptions as excecoes_requests

from application.exceptions import (
    ERRO_CORESSO_INDISPONIVEL,
    MENSAGEM_PADRAO_CREDENCIAIS_INCORRETAS,
    MENSAGEM_PADRAO_RF_SEM_DADOS,
    CoressoIndisponivelError,
    CoressoRespostaError,
)

__all__ = ["ERRO_CORESSO_INDISPONIVEL", "UsuariosService"]
from config.login_debug import login_debug
from domain.ports.coresso_port import CoressoPort
from infrastructure.services.coresso_resposta import extrair_mensagem_coresso

_TIMEOUT_LEITURA_PADRAO_SEGUNDOS = 60
_TIMEOUT_LEITURA_AUTENTICACAO_PADRAO_SEGUNDOS = 10
_TIMEOUT_CONEXAO_PADRAO_SEGUNDOS = 5


def _inteiro_do_ambiente(nome: str, padrao: int) -> int:
    """Lê variável de ambiente inteira positiva ou retorna o padrão.

    Args:
        nome (str): Nome da variável (ex.: ``AUTH_API_TIMEOUT_SECONDS``).
        padrao (int): Valor usado quando ausente ou inválido.

    Returns:
        int: Timeout em segundos (mínimo 1).
    """
    bruto = os.getenv(nome, "").strip()
    if not bruto:
        return padrao
    try:
        return max(1, int(bruto))
    except ValueError:
        return padrao


def _timeout_leitura_segundos() -> int:
    """Timeout de leitura para DadosSigpae e demais GETs após login."""
    return _inteiro_do_ambiente(
        "AUTH_API_TIMEOUT_SECONDS", _TIMEOUT_LEITURA_PADRAO_SEGUNDOS
    )


def _timeout_leitura_autenticacao_segundos() -> int:
    """Timeout de leitura apenas do POST ``/api/v1/autenticacao``."""
    return _inteiro_do_ambiente(
        "AUTH_API_AUTH_TIMEOUT_SECONDS", _TIMEOUT_LEITURA_AUTENTICACAO_PADRAO_SEGUNDOS
    )


def _timeout_conexao_segundos() -> int:
    """Timeout para estabelecer conexão TCP com o CoreSSO."""
    return _inteiro_do_ambiente(
        "AUTH_API_CONNECT_TIMEOUT_SECONDS", _TIMEOUT_CONEXAO_PADRAO_SEGUNDOS
    )


class UsuariosService(CoressoPort):
    """Implementa ``CoressoPort`` via HTTP e variáveis de ambiente.

    Propaga mensagens de erro do CoreSSO em ``CoressoRespostaError`` e trata
    indisponibilidade do serviço com ``CoressoIndisponivelError``.

    Attributes:
        base_url (str): URL base do CoreSSO sem barra final.
        api_eol_key (str): Valor do header ``x-api-eol-key``.
        read_timeout_seconds (int): Timeout de leitura para DadosSigpae.
        auth_read_timeout_seconds (int): Timeout de leitura para autenticação.
        connect_timeout_seconds (int): Timeout de conexão TCP.
    """

    def __init__(
        self,
        base_url: str | None = None,
        timeout_seconds: int | None = None,
        auth_timeout_seconds: int | None = None,
        connect_timeout_seconds: int | None = None,
        api_eol_key: str | None = None,
    ):
        """Configura integração com CoreSSO a partir do ambiente ou parâmetros.

        Args:
            base_url (str | None): URL do CoreSSO; usa ``AUTH_API_BASE_URL`` se
                ``None``.
            timeout_seconds (int | None): Timeout de leitura do DadosSigpae; usa
                ``AUTH_API_TIMEOUT_SECONDS`` se ``None``.
            auth_timeout_seconds (int | None): Timeout do POST de autenticação;
                usa ``AUTH_API_AUTH_TIMEOUT_SECONDS`` se ``None``.
            connect_timeout_seconds (int | None): Timeout de conexão; usa
                ``AUTH_API_CONNECT_TIMEOUT_SECONDS`` se ``None``.
            api_eol_key (str | None): Chave ``x-api-eol-key``; usa
                ``AUTH_API_EOL_KEY`` se ``None``.
        """
        origem_base_url = (
            os.getenv("AUTH_API_BASE_URL", "") if base_url is None else base_url
        )
        origem_chave_api = (
            os.getenv("AUTH_API_EOL_KEY", "") if api_eol_key is None else api_eol_key
        )
        self.base_url = origem_base_url.rstrip("/")
        self.api_eol_key = origem_chave_api.strip()
        self.read_timeout_seconds = (
            _timeout_leitura_segundos() if timeout_seconds is None else timeout_seconds
        )
        self.auth_read_timeout_seconds = (
            _timeout_leitura_autenticacao_segundos()
            if auth_timeout_seconds is None
            else auth_timeout_seconds
        )
        self.connect_timeout_seconds = (
            _timeout_conexao_segundos()
            if connect_timeout_seconds is None
            else connect_timeout_seconds
        )

    @property
    def timeout_seconds(self) -> int:
        """Alias de ``read_timeout_seconds`` para compatibilidade com testes."""
        return self.read_timeout_seconds

    def _timeouts(self, segundos_leitura: int | None = None) -> tuple[int, int]:
        """Monta tupla ``(conexão, leitura)`` para ``requests.request``.

        Args:
            segundos_leitura (int | None): Override do timeout de leitura.

        Returns:
            tuple[int, int]: Par ``(connect_timeout_seconds, read_timeout)``.
        """
        leitura = (
            self.read_timeout_seconds if segundos_leitura is None else segundos_leitura
        )
        return (self.connect_timeout_seconds, leitura)

    def _cabecalhos(self) -> dict[str, str]:
        """Retorna cabeçalhos obrigatórios das chamadas ao CoreSSO."""
        return {"x-api-eol-key": self.api_eol_key}

    def _requisicao_json(
        self,
        metodo: str,
        url: str,
        *,
        etapa: str,
        corpo_json: dict | None = None,
        timeout_leitura_segundos: int | None = None,
    ) -> dict[str, Any]:
        """Executa requisição HTTP e devolve JSON em caso de sucesso.

        Args:
            metodo (str): Verbo HTTP (``GET``, ``POST``, etc.).
            url (str): URL completa do endpoint.
            etapa (str): Nome lógico para logs (``autenticacao``, ``dados_sigpae``).
            corpo_json (dict | None): Payload JSON do POST, se houver.
            timeout_leitura_segundos (int | None): Override do timeout de leitura.

        Returns:
            dict[str, Any]: Corpo JSON decodificado.

        Raises:
            CoressoRespostaError: Erro de negócio retornado pelo CoreSSO.
            CoressoIndisponivelError: Serviço indisponível, timeout ou HTTP 5xx.
        """
        limite_leitura = (
            self.read_timeout_seconds
            if timeout_leitura_segundos is None
            else timeout_leitura_segundos
        )
        inicio = time.monotonic()
        try:
            resposta = requests.request(
                metodo,
                url,
                json=corpo_json,
                headers=self._cabecalhos(),
                timeout=self._timeouts(limite_leitura),
            )
        except excecoes_requests.ConnectTimeout as exc:
            login_debug(f"coresso.{etapa}.connect_timeout", url=url)
            raise CoressoIndisponivelError() from exc
        except excecoes_requests.ReadTimeout as exc:
            login_debug(
                f"coresso.{etapa}.read_timeout",
                url=url,
                read_s=limite_leitura,
                duracao_ms=int((time.monotonic() - inicio) * 1000),
            )
            raise CoressoIndisponivelError() from exc
        except excecoes_requests.RequestException as exc:
            login_debug(f"coresso.{etapa}.erro_rede", url=url, motivo=str(exc))
            raise CoressoIndisponivelError() from exc

        duracao_ms = int((time.monotonic() - inicio) * 1000)

        if resposta.status_code in (400, 401) and etapa == "autenticacao":
            mensagem = (
                extrair_mensagem_coresso(resposta)
                or MENSAGEM_PADRAO_CREDENCIAIS_INCORRETAS
            )
            login_debug(
                f"coresso.{etapa}.credenciais_invalidas",
                status=resposta.status_code,
                duracao_ms=duracao_ms,
                mensagem=mensagem,
            )
            raise CoressoRespostaError(mensagem, status_http=401)

        if resposta.status_code in (400, 401, 403, 404) and etapa == "dados_sigpae":
            mensagem = (
                extrair_mensagem_coresso(resposta) or MENSAGEM_PADRAO_RF_SEM_DADOS
            )
            login_debug(
                f"coresso.{etapa}.erro_negocio",
                status=resposta.status_code,
                duracao_ms=duracao_ms,
                mensagem=mensagem,
            )
            raise CoressoRespostaError(mensagem, status_http=resposta.status_code)

        if resposta.status_code >= 500:
            login_debug(f"coresso.{etapa}.http_erro", status=resposta.status_code)
            raise CoressoIndisponivelError() from excecoes_requests.HTTPError(
                f"HTTP {resposta.status_code}"
            )

        if not resposta.ok:
            login_debug(f"coresso.{etapa}.http_erro", status=resposta.status_code)
            raise CoressoIndisponivelError()

        try:
            dados = resposta.json()
        except ValueError as exc:
            raise CoressoIndisponivelError() from exc

        login_debug(f"coresso.{etapa}.ok", duracao_ms=duracao_ms)
        if not isinstance(dados, dict):
            raise CoressoIndisponivelError()
        return dados

    def autenticar(self, login: str, senha: str) -> dict:
        """Autentica no CoreSSO, consulta DadosSigpae e padroniza o payload.

        Args:
            login (str): RF com 7 dígitos.
            senha (str): Senha do usuário.

        Returns:
            dict: Payload unificado com ``codigoRf``, ``rf``, ``cargos``, ``nome``,
                ``permissoes``, ``contexto`` e demais campos do caso de uso.

        Raises:
            ValueError: Se ``AUTH_API_BASE_URL`` ou ``AUTH_API_EOL_KEY`` estiverem
                ausentes.
            CoressoRespostaError: Credenciais inválidas ou RF sem dados no SIGPAE.
            CoressoIndisponivelError: Falha de comunicação com o CoreSSO.
        """
        if not self.base_url:
            raise ValueError("AUTH_API_BASE_URL não configurada")
        if not self.api_eol_key:
            raise ValueError("AUTH_API_EOL_KEY não configurada")

        url_autenticacao = f"{self.base_url}/api/v1/autenticacao"
        login_debug(
            "coresso.autenticacao.inicio",
            url=url_autenticacao,
            connect_s=self.connect_timeout_seconds,
            read_s=self.auth_read_timeout_seconds,
        )
        dados = self._requisicao_json(
            "POST",
            url_autenticacao,
            etapa="autenticacao",
            corpo_json={"login": login, "senha": senha},
            timeout_leitura_segundos=self.auth_read_timeout_seconds,
        )

        usuario_id = dados.get("usuarioId")
        status = dados.get("status")
        nome = dados.get("nome")
        codigo_rf = dados.get("codigoRf")
        contexto = dados.get("contexto", "")
        permissoes = dados.get("permissoes", [])

        if not usuario_id or nome is None or codigo_rf is None or status is None:
            raise CoressoIndisponivelError()

        login_debug("coresso.autenticacao.ok", codigo_rf=codigo_rf)
        dados_sigpae = self._obter_dados_sigpae(codigo_rf)
        cargo = self._extrair_cargo(dados_sigpae)
        cargos = dados_sigpae.get("cargos", [])
        rf = dados_sigpae.get("rf", codigo_rf)
        cpf = dados_sigpae.get("cpf")
        email = dados_sigpae.get("email")
        nome_final = dados_sigpae.get("nome", nome)
        inexistente_eol = bool(dados_sigpae.get("inexistenteEol", False))

        return {
            "usuarioId": usuario_id,
            "status": status,
            "nome": nome_final,
            "codigoRf": codigo_rf,
            "rf": rf,
            "cpf": cpf,
            "email": email,
            "cargos": cargos,
            "inexistenteEol": inexistente_eol,
            "cargo": cargo,
            "dadosSigpae": dados_sigpae,
            "contexto": contexto,
            "permissoes": permissoes,
        }

    def _obter_dados_sigpae(self, codigo_rf: str) -> dict:
        """Consulta dados funcionais no endpoint DadosSigpae.

        Args:
            codigo_rf (str): Código RF retornado na autenticação.

        Returns:
            dict: Resposta JSON com cargos e dados cadastrais.

        Raises:
            CoressoRespostaError: Quando o CoreSSO indica ausência ou bloqueio.
            CoressoIndisponivelError: Quando o serviço não responde adequadamente.
        """
        url_sigpae = f"{self.base_url}/api/funcionarios/DadosSigpae/{codigo_rf}"
        login_debug("coresso.dados_sigpae.inicio", url=url_sigpae)
        dados = self._requisicao_json("GET", url_sigpae, etapa="dados_sigpae")
        self._normalizar_cargos_sigpae(dados)
        return dados

    def _normalizar_cargos_sigpae(self, dados_sigpae: dict) -> None:
        """Preenche ``descricaoCargo`` a partir de ``nomeCargo`` quando necessário.

        Args:
            dados_sigpae (dict): Payload mutável retornado pelo CoreSSO (alterado
                in-place).
        """
        cargos = dados_sigpae.get("cargos")
        if not isinstance(cargos, list):
            return
        for item in cargos:
            if not isinstance(item, dict):
                continue
            if not item.get("descricaoCargo") and item.get("nomeCargo"):
                item["descricaoCargo"] = str(item["nomeCargo"])

    def _extrair_cargo(self, dados_sigpae: dict) -> str:
        """Extrai descrição de cargo de formatos conhecidos da resposta SIGPAE.

        Args:
            dados_sigpae (dict): Dados funcionais do endpoint DadosSigpae.

        Returns:
            str: Texto do cargo ou string vazia se não identificado.
        """
        for chave in ("cargo", "Cargo", "descricaoCargo", "descCargo", "nomeCargo"):
            valor = dados_sigpae.get(chave)
            if valor:
                return str(valor)
        cargos = dados_sigpae.get("cargos")
        if isinstance(cargos, list) and cargos:
            primeiro_cargo = cargos[0]
            if isinstance(primeiro_cargo, dict):
                descricao = primeiro_cargo.get("descricaoCargo")
                if descricao:
                    return str(descricao)
        return ""
