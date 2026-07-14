"""
Configurações Django do projeto SME Recreio nas Férias.

Centraliza apps instalados, banco PostgreSQL, DRF, autenticação por token RF
e integração OpenAPI (drf-spectacular). Variáveis sensíveis vêm do ``.env``.
"""

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv()


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    raise ImproperlyConfigured(
        "Defina a variável de ambiente DJANGO_SECRET_KEY (ex.: no arquivo .env)."
    )

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG", "true").strip().lower() in ("1", "true", "yes")

_allowed_hosts = os.getenv("ALLOWED_HOSTS", "")
ALLOWED_HOSTS = [host.strip() for host in _allowed_hosts.split(",") if host.strip()]
if DEBUG and not ALLOWED_HOSTS:
    # Mantém DX local sem precisar configurar ALLOWED_HOSTS no .env.
    ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]"]


# Application definition

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "usuarios.apps.UsuariosConfig",
    "edicoes.apps.EdicoesConfig",
    "polos.apps.PolosConfig",
    "django.contrib.auth",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "auditlog",
    "rest_framework",
    "drf_spectacular",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "auditlog.middleware.AuditlogMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

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


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB"),
        "USER": os.getenv("POSTGRES_USER"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD"),
        "HOST": os.getenv("DB_HOST"),
        "PORT": os.getenv("DB_PORT"),
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = "static/"

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "usuarios.Usuario"

# Validade do token Bearer emitido no login (segundos); padrão 12 horas.
USUARIOS_TOKEN_MAX_AGE = 60 * 60 * 12

# CRUD legado em /api/usuarios/ (desligado por padrão; login permanece ativo).
USUARIOS_CRUD_ENABLED = os.getenv("USUARIOS_CRUD_ENABLED", "false").strip().lower() in (
    "1",
    "true",
    "yes",
)

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "usuarios.authentication.RfTokenAuthentication",
    ],
    "EXCEPTION_HANDLER": "config.exception_handler.custom_exception_handler",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "SME Recreio Nas Ferias Backend API",
    "DESCRIPTION": "Documentacao OpenAPI dos endpoints da aplicacao.",
    "VERSION": "1.0.0",
    # Aplica security global para que o Swagger UI mostre o campo de token.
    "SECURITY": [{"bearerAuth": []}],
    # Oculta o próprio endpoint de schema da lista de rotas documentadas.
    "SERVE_INCLUDE_SCHEMA": False,
}

# Logs do fluxo de login (``recreio.login``) quando LOGIN_DEBUG=1 no .env.
if os.getenv("LOGIN_DEBUG", "").strip().lower() in ("1", "true", "yes"):
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "handlers": {
            "console": {"class": "logging.StreamHandler"},
        },
        "loggers": {
            "recreio.login": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
        },
    }
