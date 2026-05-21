"""Token de API assinado vinculado ao usuário Django (pós-CoreSSO)."""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import signing

TOKEN_SALT = "usuarios.login"
TOKEN_MAX_AGE = getattr(settings, "USUARIOS_TOKEN_MAX_AGE", 60 * 60 * 12)


def gerar_token_acesso(usuario) -> str:
    """Gera token Bearer assinado com RF e id do usuário Django."""
    return signing.dumps(
        {"rf": usuario.rf, "uid": usuario.pk},
        salt=TOKEN_SALT,
    )


def resolver_usuario_por_token(token: str):
    """Valida token e retorna o usuário ativo ou None."""
    Usuario = get_user_model()
    try:
        payload = signing.loads(token, salt=TOKEN_SALT, max_age=TOKEN_MAX_AGE)
    except signing.BadSignature:
        return None

    rf = payload.get("rf")
    if not rf:
        return None

    uid = payload.get("uid")
    if uid is not None:
        return Usuario.objects.filter(pk=uid, rf=rf, is_active=True).first()

    return Usuario.objects.filter(rf=rf, is_active=True).first()
