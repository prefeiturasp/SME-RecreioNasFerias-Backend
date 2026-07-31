#!/bin/sh
set -e

if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
    case "${RUN_MIGRATIONS_MODE:-strict}" in
        strict)
            python manage.py migrate --noinput
            ;;
        best-effort)
            python manage.py migrate --noinput || echo "AVISO: migrate falhou, subindo mesmo assim"
            ;;
        *)
            echo "Valor invalido para RUN_MIGRATIONS_MODE: ${RUN_MIGRATIONS_MODE}" >&2
            exit 1
            ;;
    esac
fi

if [ "$1" = "gunicorn" ]; then
    shift
    exec gunicorn config.wsgi:application \
        --bind 0.0.0.0:8000 \
        --workers "${GUNICORN_WORKERS:-3}" \
        --timeout "${GUNICORN_TIMEOUT:-60}" \
        --access-logfile - \
        --error-logfile - \
        "$@"
fi

exec "$@"