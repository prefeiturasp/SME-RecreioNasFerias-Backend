"""
Logs opcionais do fluxo de login para diagnóstico em desenvolvimento.

Ative com ``LOGIN_DEBUG=1`` no ``.env`` ou no ``docker-compose.debug.yml``.
Requer a configuração de ``LOGGING`` em ``config.settings`` para o logger
``recreio.login``.
"""

import logging
import os

logger = logging.getLogger("recreio.login")


def login_debug(etapa: str, **contexto) -> None:
    """Registra uma etapa do fluxo de login quando o modo debug está ativo.

    Args:
        etapa (str): Identificador da etapa (ex.: ``coresso.autenticacao.inicio``).
        **contexto: Pares chave-valor exibidos no log (URL, status HTTP, etc.).
    """
    if os.getenv("LOGIN_DEBUG", "").strip().lower() not in ("1", "true", "yes"):
        return
    if contexto:
        logger.info("[login] %s | %s", etapa, contexto)
    else:
        logger.info("[login] %s", etapa)
