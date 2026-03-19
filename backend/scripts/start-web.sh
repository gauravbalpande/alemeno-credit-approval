#!/bin/sh
set -eu

cd /app/backend

python manage.py makemigrations customers loans core --noinput
python manage.py migrate --noinput

exec gunicorn credit_system.wsgi:application --bind 0.0.0.0:8000

