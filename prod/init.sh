#!/bin/bash
set -e

MAX_ATTEMPTS=60
attempt=0
echo "Waiting for database..."
until uv run python -c "
import os
import psycopg
url = os.environ.get('DATABASE_URL', '')
if not url:
    print('DATABASE_URL not set')
    raise SystemExit(1)
try:
    psycopg.connect(url, connect_timeout=2)
except Exception as e:
    print(f'Database connection failed: {e}')
    raise SystemExit(1)
"; do
  attempt=$((attempt+1))
  if [ "$attempt" -ge "$MAX_ATTEMPTS" ]; then
    echo "Database not ready after ${MAX_ATTEMPTS} attempts; giving up"
    exit 1
  fi
  echo "Database not ready (attempt $attempt/$MAX_ATTEMPTS), retrying in 2s..."
  sleep 2
done
echo "Database ready."

echo "Running migrations..."
uv run python manage.py migrate --noinput

echo "Starting: $@"
exec "$@"
