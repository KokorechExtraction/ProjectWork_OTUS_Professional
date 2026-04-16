#!/bin/sh
set -eu

export PYTHONPATH=/code

echo "Waiting for database migrations to succeed..."

attempt=1
max_attempts=20

while [ "$attempt" -le "$max_attempts" ]; do
  if alembic upgrade head; then
    echo "Migrations applied successfully."
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
  fi

  echo "Migration attempt $attempt failed. Retrying in 2 seconds..."
  attempt=$((attempt + 1))
  sleep 2
done

echo "Failed to apply migrations after $max_attempts attempts."
exit 1
