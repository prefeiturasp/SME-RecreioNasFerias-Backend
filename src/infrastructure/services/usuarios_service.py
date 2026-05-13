"""Servico HTTP para autenticacao em API externa."""

import json
import os
from urllib import error, request

from domain.ports.coresso_port import CoressoPort


class UsuariosService(CoressoPort):
    """Implementa consulta de autenticação no CoreSSO."""

    def __init__(
        self,
        base_url: str | None = None,
        timeout_seconds: int = 10,
        api_eol_key: str | None = None,
    ):
        """Inicializa servico com URL base e timeout configuraveis."""
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
        """Autentica no CoreSSO e retorna payload padronizado."""
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
        """Consulta dados funcionais no endpoint DadosSigpae."""
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

        return data

    def _extrair_cargo(self, dados_sigpae: dict) -> str:
        """Extrai campo de cargo de formatos conhecidos da resposta."""
        for chave in ("cargo", "Cargo", "descricaoCargo", "descCargo", "nomeCargo"):
            valor = dados_sigpae.get(chave)
            if valor:
                return str(valor)
        return ""
