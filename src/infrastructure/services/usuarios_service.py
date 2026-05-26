"""
Serviço HTTP para autenticação e consulta de dados no CoreSSO.

Realiza ``POST /api/v1/autenticacao`` e ``GET .../DadosSigpae/{rf}`` usando
``urllib``, lendo ``AUTH_API_BASE_URL`` e ``AUTH_API_EOL_KEY`` do ambiente.
"""

import json
import os
from urllib import error, request

from domain.ports.coresso_port import CoressoPort


class UsuariosService(CoressoPort):
    """Implementa ``CoressoPort`` via ``urllib`` e variáveis de ambiente.

    Normaliza cargos SIGPAE (``descricaoCargo``) e monta payload unificado
    consumido por ``LoginUserUseCase``. Erros HTTP 400/401 viram
    ``ValueError`` com mensagem estável para a API.

    Attributes:
        base_url (str): URL base do CoreSSO sem barra final.
        api_eol_key (str): Valor do header ``x-api-eol-key``.
        timeout_seconds (int): Timeout das requisições HTTP.
    """

    def __init__(
        self,
        base_url: str | None = None,
        timeout_seconds: int = 10,
        api_eol_key: str | None = None,
    ):
        """Configura URL base, chave EOL e timeout das requisições HTTP.

        Args:
            base_url (str | None): URL do CoreSSO; usa ``AUTH_API_BASE_URL`` se
                ``None``.
            timeout_seconds (int): Timeout em segundos para ``urlopen``.
            api_eol_key (str | None): Chave ``x-api-eol-key``; usa
                ``AUTH_API_EOL_KEY`` se ``None``.
        """
        source_base_url = (
            os.getenv("AUTH_API_BASE_URL", "") if base_url is None else base_url
        )
        source_api_key = (
            os.getenv("AUTH_API_EOL_KEY", "") if api_eol_key is None else api_eol_key
        )
        self.base_url = source_base_url.rstrip("/")
        self.api_eol_key = source_api_key.strip()
        self.timeout_seconds = timeout_seconds

    def autenticar(self, login: str, senha: str) -> dict:
        """Autentica no CoreSSO, enriquece com DadosSigpae e padroniza o payload.

        Args:
            login (str): RF com 7 dígitos.
            senha (str): Senha do usuário.

        Returns:
            dict: Payload unificado com ``codigoRf``, ``rf``, ``cargos``, ``nome``,
                ``permissoes``, ``contexto`` e demais campos do caso de uso.

        Raises:
            ValueError: Se variáveis de ambiente estiverem ausentes, credenciais
                forem inválidas ou o usuário não for autorizado em DadosSigpae.
            RuntimeError: Se a API externa falhar ou retornar JSON inválido.
        """
        if not self.base_url:
            raise ValueError("AUTH_API_BASE_URL não configurada")
        if not self.api_eol_key:
            raise ValueError("AUTH_API_EOL_KEY não configurada")

        payload = json.dumps({"login": login, "senha": senha}).encode("utf-8")
        req = request.Request(
            url=f"{self.base_url}/api/v1/autenticacao",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "x-api-eol-key": self.api_eol_key,
            },
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=self.timeout_seconds) as response:
                data = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            if exc.code in (400, 401):
                raise ValueError("Credenciais inválidas") from exc
            raise RuntimeError("Erro ao autenticar na API externa") from exc
        except error.URLError as exc:
            raise RuntimeError("Falha de conexão com API externa") from exc

        usuario_id = data.get("usuarioId")
        status = data.get("status")
        nome = data.get("nome")
        codigo_rf = data.get("codigoRf")
        contexto = data.get("contexto", "")
        permissoes = data.get("permissoes", [])

        if not usuario_id or nome is None or codigo_rf is None or status is None:
            raise RuntimeError("Resposta de login inválida")

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
        """Consulta dados funcionais no endpoint ``DadosSigpae``.

        Args:
            codigo_rf (str): Código RF retornado na autenticação.

        Returns:
            dict: Resposta JSON com cargos e dados cadastrais.

        Raises:
            ValueError: Para respostas 400/401/403/404 (usuário não autorizado).
            RuntimeError: Para outros erros HTTP, URL ou JSON inválido.
        """
        req = request.Request(
            url=f"{self.base_url}/api/funcionarios/DadosSigpae/{codigo_rf}",
            headers={"x-api-eol-key": self.api_eol_key},
            method="GET",
        )
        try:
            with request.urlopen(req, timeout=self.timeout_seconds) as response:
                data = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            if exc.code in (400, 401, 403, 404):
                raise ValueError("Usuário não autorizado") from exc
            raise RuntimeError("Erro ao consultar dados funcionais") from exc
        except error.URLError as exc:
            raise RuntimeError("Falha de conexão com API externa") from exc

        if not isinstance(data, dict):
            raise RuntimeError("Resposta inválida em DadosSigpae")

        self._normalizar_cargos_sigpae(data)
        return data

    def _normalizar_cargos_sigpae(self, dados_sigpae: dict) -> None:
        """Alinha ``descricaoCargo`` quando apenas ``nomeCargo`` estiver presente.

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
