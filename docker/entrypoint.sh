#!/bin/sh
set -e

python docker/wait_for_postgres.py

python manage.py migrate --noinput
python manage.py collectstatic --noinput

if [ "${RUN_INITIAL_SETUP:-false}" = "true" ]; then
    python manage.py setup_initial_data
    python manage.py update_roles_and_create_admins
fi

exec gunicorn church.wsgi_production:application \
    --bind 0.0.0.0:8000 \
    --workers "${GUNICORN_WORKERS:-3}" \
    --timeout 60 \
    --access-logfile - \
    --error-logfile -
