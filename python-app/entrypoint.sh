#!/bin/bash
set -e

# Wait for PostgreSQL to be ready using bash TCP check (no extra packages needed)
echo "Waiting for PostgreSQL to be ready at $POSTGRES_DB_HOST:$POSTGRES_DB_PORT..."

max_attempts=30
attempt=1

while [ $attempt -le $max_attempts ]; do
  if timeout 2 bash -c "cat < /dev/null > /dev/tcp/$POSTGRES_DB_HOST/$POSTGRES_DB_PORT" 2>/dev/null; then
    echo "PostgreSQL port is open!"
    break
  fi
  
  if [ $attempt -eq $max_attempts ]; then
    echo "ERROR: PostgreSQL failed to start after $max_attempts attempts"
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
