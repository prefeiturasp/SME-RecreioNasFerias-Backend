#!/bin/sh
set -e

python src/manage.py preparar_migracao_polos_legado
python src/manage.py migrate
