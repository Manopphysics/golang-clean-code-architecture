#!/bin/bash
set -e

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
max_attempts=30
attempt=1
until PGPASSWORD="$POSTGRES_DB_PASSWORD" psql -h "$POSTGRES_DB_HOST" -U "$POSTGRES_DB_USER" -d "$POSTGRES_DB_NAME" -c "SELECT 1" >/dev/null 2>&1 || [ $attempt -eq $max_attempts ]; do
  echo "Attempt $attempt/$max_attempts: PostgreSQL not ready yet, waiting..."
  sleep 1
  attempt=$((attempt + 1))
done

if [ $attempt -eq $max_attempts ]; then
  echo "ERROR: PostgreSQL failed to start after $max_attempts attempts"
  exit 1
fi

echo "PostgreSQL is ready!"

echo "Running database migrations..."
alembic upgrade head

echo "Starting FastAPI server..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
