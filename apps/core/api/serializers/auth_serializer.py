"""Serializers do fluxo de autenticação do app `core`."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypedDict

from rest_framework import serializers

if TYPE_CHECKING:
    from apps.core.services.auth_service import AuthenticatedSessionData


class CargoResponsePayload(TypedDict):
    """Representa um cargo serializado no contrato HTTP de auth."""

    codigoCargo: int | None
    descricaoCargo: str


def _serializar_cargo_resposta(
    cargo: Any | None,
) -> list[CargoResponsePayload]:
    """Converte o cargo autorizado do domínio para o contrato HTTP da API."""
    if cargo is None:
        return []

    codigo_cargo = getattr(cargo, "codigo_cargo", None)
    descricao_cargo = getattr(cargo, "descricao_cargo", "")
    return [
        {
            "codigoCargo": (
                codigo_cargo
                if isinstance(codigo_cargo, int) or codigo_cargo is None
                else None
            ),
            "descricaoCargo": (
                descricao_cargo if isinstance(descricao_cargo, str) else ""
            ),
        }
    ]


class LoginRequestSerializer(serializers.Serializer):
    """Valida o payload esperado pelo endpoint de login."""

    login = serializers.CharField(max_length=32)
    senha = serializers.CharField(max_length=128, trim_whitespace=False)


class CargoSerializer(serializers.Serializer):
    """Representa um cargo serializado para resposta HTTP."""

    codigoCargo = serializers.IntegerField(allow_null=True)  # noqa: N815
    descricaoCargo = serializers.CharField()  # noqa: N815


class LoginResponseSerializer(serializers.Serializer):
    """Representa a resposta de sucesso do endpoint de login."""

    token = serializers.CharField()
    rf = serializers.CharField()
    nome = serializers.CharField()
    email = serializers.EmailField(
        allow_null=True, allow_blank=True, required=False
    )
    cpf = serializers.CharField(
        allow_null=True, allow_blank=True, required=False
    )
    cargos = CargoSerializer(many=True)

    @classmethod
    def from_session_data(
        cls,
        session_data: AuthenticatedSessionData,
        *,
        token: str,
    ) -> LoginResponseSerializer:
        """Monta a resposta HTTP de login a partir do usuário autenticado."""
        return cls(
            {
                "token": token,
                "rf": session_data.rf,
                "nome": session_data.nome,
                "email": session_data.email,
                "cpf": session_data.cpf,
                "cargos": _serializar_cargo_resposta(session_data.cargo),
            }
        )


class RefreshResponseSerializer(serializers.Serializer):
    """Representa a resposta de renovação de token."""

    token = serializers.CharField()


class TokenVerifyRequestSerializer(serializers.Serializer):
    """Representa o payload esperado pelo endpoint de verificação."""

    token = serializers.CharField()


class MeResponseSerializer(serializers.Serializer):
    """Representa a resposta do endpoint `me`."""

    rf = serializers.CharField(
        allow_null=True, allow_blank=True, required=False
    )
    nome = serializers.CharField(allow_blank=True)
    email = serializers.EmailField(
        allow_null=True, allow_blank=True, required=False
    )
    cpf = serializers.CharField(
        allow_null=True, allow_blank=True, required=False
    )
    cargos = CargoSerializer(many=True)

    @classmethod
    def from_user(cls, usuario: Any) -> MeResponseSerializer:
        """Monta a resposta HTTP a partir do vínculo local do usuário."""
        return cls(
            {
                "rf": usuario.rf or usuario.username,
                "nome": usuario.nome_completo,
                "email": usuario.email or None,
                "cpf": usuario.cpf or None,
                "cargos": _serializar_cargo_resposta(usuario.cargo_permitido),
            }
        )
