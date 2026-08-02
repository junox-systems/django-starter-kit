#!/bin/bash
set -e

echo "Waiting for database..."
while ! uv run python -c "
import socket, os
url = os.environ.get('DATABASE_URL', '')
host_port = url.split('@')[-1].split('/')[0]
host, port = host_port.split(':') if ':' in host_port else (host_port, '5432')
s = socket.create_connection((host, int(port)), timeout=2)
s.close()
" 2>/dev/null; do
  echo "Database not ready, retrying in 2s..."
  sleep 2
done
echo "Database ready."

echo "Running migrations..."
uv run python manage.py migrate --noinput

echo "Starting: $@"
exec "$@"
