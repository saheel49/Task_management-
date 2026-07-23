#!/usr/bin/env bash
set -euo pipefail

echo "Running django-entrypoint.sh"

if [ -n "$DATABASE_URL" ]; then
    echo "Waiting for PostgreSQL to be ready..."

    DB_HOST=$(python -c "import os; from urllib.parse import urlparse; print(urlparse(os.environ['DATABASE_URL']).hostname or 'localhost')")
    DB_PORT=$(python -c "import os; from urllib.parse import urlparse; print(urlparse(os.environ['DATABASE_URL']).port or 5432)")

    echo "Waiting for database connection at ${DB_HOST}:${DB_PORT}..."

    RETRIES=30
    until python manage.py shell -c "from django.db import connection; connection.ensure_connection()" 2>/dev/null; do
        RETRIES=$((RETRIES - 1))
        if [ $RETRIES -eq 0 ]; then
            echo "FATAL: Could not connect to database after 30 attempts. Exiting."
            exit 1
        fi
        echo "Database not ready yet, retrying in 2 seconds... ($RETRIES retries left)"
        sleep 2
    done

    echo "Database connection established."
fi

echo "Running migrations..."
python manage.py migrate --noinput
MIGRATION_EXIT_CODE=$?
if [ $MIGRATION_EXIT_CODE -ne 0 ]; then
    echo "FATAL: Migrations failed with exit code $MIGRATION_EXIT_CODE. Exiting."
    exit $MIGRATION_EXIT_CODE
fi
echo "Migrations completed successfully."

echo "Collecting static files..."
python manage.py collectstatic --noinput
COLLECTSTATIC_EXIT_CODE=$?
if [ $COLLECTSTATIC_EXIT_CODE -ne 0 ]; then
    echo "WARNING: collectstatic failed with exit code $COLLECTSTATIC_EXIT_CODE. Continuing anyway..."
else
    echo "Static files collected successfully."
fi

echo "Starting application..."

if [ $# -eq 0 ]; then
    exec gunicorn config.wsgi:application \
        --bind 0.0.0.0:8000 \
        --workers 3 \
        --access-logfile - \
        --error-logfile -
elif [ $# -eq 1 ] && [[ "$1" == *" "* ]]; then
    exec bash -c "$1"
else
    exec "$@"
fi