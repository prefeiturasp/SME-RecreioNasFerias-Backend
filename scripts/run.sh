#!/bin/sh
set -e

sh scripts/aplicar-migracoes.sh
exec python src/manage.py runserver 0.0.0.0:8000
