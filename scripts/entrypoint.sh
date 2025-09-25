#!/bin/sh
# scripts/entrypoint.sh

set -e

echo "Waiting for database..."
# Use a more portable approach
until nc -z ${DB_HOST:-db} ${DB_PORT:-5432}; do
  echo "Database is unavailable - sleeping"
  sleep 1
done

echo "Database is ready!"

# Run migrations
echo "Running database migrations..."
cd /app

# Ensure migrations/versions exists
if [ ! -d "/app/migrations/versions" ]; then
  echo "Creating migrations/versions directory..."
  mkdir -p /app/migrations/versions
fi

# If there are no migration files, create an initial autogenerate
if [ -z "$(ls -A /app/migrations/versions || true)" ]; then
  echo "No Alembic revisions found. Generating initial migration..."
  /app/.venv/bin/python -m alembic revision --autogenerate -m "initial"
fi

# Apply migrations
/app/.venv/bin/python -m alembic upgrade head

echo "Starting application..."
exec "$@"
# /app/.venv/bin/fastapi run app/main.py --port 8000 --host 0.0.0.0