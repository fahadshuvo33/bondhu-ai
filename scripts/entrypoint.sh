#!/bin/bash
set -e

# Wait for database
echo "Waiting for database..."
while ! nc -z db 5432; do
  sleep 0.1
done
echo "Database is ready!"

# Run migrations
echo "Running database migrations..."
uv run alembic upgrade head

# Start the application
echo "Starting application..."
exec "$@"