"""
Token de API assinado vinculado ao usuário Django (pós-CoreSSO).

Utiliza ``django.core.signing`` com salt fixo e validade configurável em
``settings.USUARIOS_TOKEN_MAX_AGE`` (padrão 12 horas).
"""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import signing
from typing import Any

TOKEN_SALT = "usuarios.login"
TOKEN_MAX_AGE = getattr(settings, "USUARIOS_TOKEN_MAX_AGE", 60 * 60 * 12)


def gerar_token_acesso(usuario: Any) -> str:
    """Gera token Bearer assinado com RF e id do usuário Django.

    Args:
        usuario: Instância de ``AUTH_USER_MODEL`` autenticada no login.

    Returns:
        str: Token opaco para o header ``Authorization: Bearer``.
    """
    return signing.dumps(
        {"rf": usuario.rf, "uid": usuario.pk},
        salt=TOKEN_SALT,
    )


def resolver_usuario_por_token(token: str) -> Any | None:
    """Valida assinatura e expiração do token e carrega o usuário ativo.

    Args:
        token (str): Valor após o prefixo ``Bearer`` no header Authorization.

    Returns:
        Usuario | None: Usuário ativo correspondente ou ``None`` se inválido/expirado.
    """
    usuario_model = get_user_model()
    try:
        payload = signing.loads(token, salt=TOKEN_SALT, max_age=TOKEN_MAX_AGE)
    except signing.BadSignature:
        return None

    rf = payload.get("rf")
    if not rf:
        return None

    uid = payload.get("uid")
    if uid is not None:
        return usuario_model.objects.filter(pk=uid, rf=rf, is_active=True).first()

    return usuario_model.objects.filter(rf=rf, is_active=True).first()
