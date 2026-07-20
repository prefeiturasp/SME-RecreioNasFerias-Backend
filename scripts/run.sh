#!/bin/sh
set -e

python src/manage.py preparar_migracao_polos_legado
python src/manage.py migrate
exec python src/manage.py runserver 0.0.0.0:8000
