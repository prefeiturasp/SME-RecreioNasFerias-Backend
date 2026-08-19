"""Serviço de auditoria do fluxo de autenticação do app `core`."""

from __future__ import annotations

from rest_framework.request import Request

from apps.core.models import CargoPermitido, LogLogin


class AuthAuditService:
    """Centraliza o registro de auditoria do fluxo de autenticação."""

    @staticmethod
    def _obter_ip_request(request: Request) -> str:
        """Extrai o IP da requisição para auditoria operacional."""
        forwarded_for = request.headers.get("X-Forwarded-For", "").strip()
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        endereco = request.META.get("REMOTE_ADDR", "")
        return endereco if isinstance(endereco, str) else ""

    def registrar_tentativa_login(
        self,
        request: Request,
        *,
        sucesso: bool,
        login_tentativa: str,
        codigo_http: int,
        mensagem: str,
        cargo: CargoPermitido | None = None,
    ) -> None:
        """Persiste uma tentativa de login para auditoria operacional."""
        LogLogin.objects.create(
            sucesso=sucesso,
            login_tentativa=login_tentativa,
            codigo_http=codigo_http,
            mensagem=mensagem,
            endereco_ip=self._obter_ip_request(request),
            user_agent=request.headers.get("User-Agent", ""),
            codigo_cargo=cargo.codigo_cargo if cargo else None,
            descricao_cargo=cargo.descricao_cargo if cargo else "",
        )
