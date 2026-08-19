#!/bin/sh
set -e

case " $* " in
	*" manage.py runserver "*)
		python manage.py migrate --noinput
		;;
esac

exec "$@"