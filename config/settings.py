"""Configuração Django do projeto Recreio nas Férias."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import environ

# -----------------------------------------------------------------------------
# Diretórios e variáveis de ambiente
# -----------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
arquivo_env = BASE_DIR / ".env"
if arquivo_env.exists():
    environ.Env.read_env(str(arquivo_env))


# -----------------------------------------------------------------------------
# Banco de dados
# -----------------------------------------------------------------------------

database_config = {
    "ENGINE": "django.db.backends.postgresql",
    "HOST": env("POSTGRES_HOST", default="db"),
    "PORT": env.str("POSTGRES_PORT", default="5432"),
    "NAME": env("POSTGRES_DB"),
    "USER": env("POSTGRES_USER"),
    "PASSWORD": env("POSTGRES_PASSWORD"),
}


# -----------------------------------------------------------------------------
# Segurança e configurações gerais
# -----------------------------------------------------------------------------

# Sem valor padrão propositalmente.
# A aplicação não deverá iniciar se DJANGO_SECRET_KEY não estiver configurada.
SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost"])


# -----------------------------------------------------------------------------
# CORS e CSRF
# -----------------------------------------------------------------------------

CORS_ALLOW_CREDENTIALS = env.bool("CORS_ALLOW_CREDENTIALS", default=True)
CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=[],
)
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])


# -----------------------------------------------------------------------------
# Integrações externas
# -----------------------------------------------------------------------------

AUTH_API_BASE_URL = env("AUTH_API_BASE_URL", default="").rstrip("/")
AUTH_API_EOL_KEY = env("AUTH_API_EOL_KEY", default="")
AUTH_API_TIMEOUT_SECONDS = env.int("AUTH_API_TIMEOUT_SECONDS", default=60)
AUTH_API_AUTH_TIMEOUT_SECONDS = env.int(
    "AUTH_API_AUTH_TIMEOUT_SECONDS",
    default=AUTH_API_TIMEOUT_SECONDS,
)
AUTH_API_CONNECT_TIMEOUT_SECONDS = env.int(
    "AUTH_API_CONNECT_TIMEOUT_SECONDS",
    default=5,
)
AUTH_CODIGO_SISTEMA = env.int("AUTH_CODIGO_SISTEMA", default=1009)


# -----------------------------------------------------------------------------
# Sessão JWT
# -----------------------------------------------------------------------------

AUTH_JWT_ACCESS_TOKEN_LIFETIME = timedelta(minutes=15)
AUTH_JWT_REFRESH_TOKEN_LIFETIME = timedelta(days=7)
AUTH_REFRESH_COOKIE_NAME = "refresh_token"
AUTH_REFRESH_COOKIE_PATH = "/api/v1/auth/"
AUTH_REFRESH_COOKIE_SAMESITE = "Lax"
AUTH_REFRESH_COOKIE_SECURE = env.bool(
    "AUTH_REFRESH_COOKIE_SECURE",
    default=not DEBUG,
)


# -----------------------------------------------------------------------------
# Aplicações instaladas
# -----------------------------------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # 3rd
    "corsheaders",
    "rest_framework",
    "drf_spectacular",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    # local
    "apps.core.apps.CoreConfig",
    "apps.edicoes.apps.EdicoesConfig",
    "apps.polos.apps.PolosConfig",
    "apps.definicoes_polos.apps.DefinicoesPolosConfig",
]


# -----------------------------------------------------------------------------
# Middlewares
# -----------------------------------------------------------------------------

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# -----------------------------------------------------------------------------
# URLs, templates, WSGI e ASGI
# -----------------------------------------------------------------------------

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"


# -----------------------------------------------------------------------------
# Banco de dados do Django
# -----------------------------------------------------------------------------

DATABASES = {"default": database_config}


# -----------------------------------------------------------------------------
# Validação de senhas
# -----------------------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation.MinimumLengthValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation.CommonPasswordValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation.NumericPasswordValidator"
        ),
    },
]


# -----------------------------------------------------------------------------
# Internacionalização
# -----------------------------------------------------------------------------

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True


# -----------------------------------------------------------------------------
# Arquivos estáticos
# -----------------------------------------------------------------------------

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": ("whitenoise.storage.CompressedManifestStaticFilesStorage"),
    },
}


# -----------------------------------------------------------------------------
# Modelo de usuário e modelos Django
# -----------------------------------------------------------------------------

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "core.Usuario"


# -----------------------------------------------------------------------------
# Django REST Framework
# -----------------------------------------------------------------------------

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "apps.core.authentication.RfTokenAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "apps.core.exception_handler.tratar_excecoes_drf",
}


# -----------------------------------------------------------------------------
# Simple JWT
# -----------------------------------------------------------------------------

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": AUTH_JWT_ACCESS_TOKEN_LIFETIME,
    "REFRESH_TOKEN_LIFETIME": AUTH_JWT_REFRESH_TOKEN_LIFETIME,
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
}


# -----------------------------------------------------------------------------
# drf-spectacular / OpenAPI
# -----------------------------------------------------------------------------

SPECTACULAR_SETTINGS = {
    "TITLE": "SME Recreio nas Férias Backend API",
    "DESCRIPTION": "Documentação OpenAPI dos endpoints da aplicação.",
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SERVE_AUTHENTICATION": [],
    "SERVE_PERMISSIONS": ["rest_framework.permissions.AllowAny"],
}
