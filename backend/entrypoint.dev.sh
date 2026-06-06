#!/bin/sh
set -e

echo "==> Waiting for PostgreSQL..."
until python -c "
import os, psycopg2
psycopg2.connect(
    host=os.environ.get('POSTGRES_HOST','db'),
    dbname=os.environ.get('POSTGRES_DB','arrematex'),
    user=os.environ.get('POSTGRES_USER','arrematex'),
    password=os.environ.get('POSTGRES_PASSWORD','')
)" 2>/dev/null; do
  sleep 1
done
echo "==> PostgreSQL ready"

echo "==> Migrating shared schema..."
python manage.py migrate_schemas --shared --noinput --skip-checks 2>/dev/null || \
python manage.py migrate_schemas --shared --noinput

echo "==> Starting Django ASGI server (uvicorn)..."
exec uvicorn config.asgi:application --host 0.0.0.0 --port 8000 --reload
