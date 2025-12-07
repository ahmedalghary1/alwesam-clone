#!/bin/sh

echo "Running migrations..."
python manage.py makemigrations --noinput
python manage.py migrate --noinput

echo "Collecting static..."
python manage.py collectstatic --noinput

echo "Starting Gunicorn server..."
gunicorn project.wsgi:application --bind 0.0.0.0:80 --workers 3
