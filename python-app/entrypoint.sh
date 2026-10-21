#!/bin/bash
set -e

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
echo "Trying to connect to: $POSTGRES_DB_HOST:$POSTGRES_DB_PORT as $POSTGRES_DB_USER"

max_attempts=30
attempt=1

while [ $attempt -le $max_attempts ]; do
  if PGPASSWORD="$POSTGRES_DB_PASSWORD" psql -h "$POSTGRES_DB_HOST" -p "$POSTGRES_DB_PORT" -U "$POSTGRES_DB_USER" -d "$POSTGRES_DB_NAME" -c "SELECT 1" >/dev/null 2>&1; then
    echo "PostgreSQL is ready!"
    break
  fi
  
  if [ $attempt -eq $max_attempts ]; then
    echo "ERROR: PostgreSQL failed to start after $max_attempts attempts"
    echo "DEBUG: Last connection attempt output:"
    PGPASSWORD="$POSTGRES_DB_PASSWORD" psql -h "$POSTGRES_DB_HOST" -p "$POSTGRES_DB_PORT" -U "$POSTGRES_DB_USER" -d "$POSTGRES_DB_NAME" -c "SELECT 1"
    exit 1
  fi
  
  echo "Attempt $attempt/$max_attempts: PostgreSQL not ready yet, waiting..."
  sleep 1
  attempt=$((attempt + 1))
done

echo "Running database migrations..."
alembic upgrade head

echo "Starting FastAPI server..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
