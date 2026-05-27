#!/bin/sh
set -e

python src/manage.py migrate

if [ "${DEBUGPY_WAIT}" = "1" ]; then
  exec python -m debugpy --listen 0.0.0.0:5678 --wait-for-client src/manage.py runserver 0.0.0.0:8000 --noreload
else
  exec python -m debugpy --listen 0.0.0.0:5678 src/manage.py runserver 0.0.0.0:8000 --noreload
fi
