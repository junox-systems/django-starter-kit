#!/bin/bash

echo "Starting application initialization..."

# Change to the app directory
cd /app

# Install dependencies (let uv and pnpm handle caching)
echo "Installing dependencies..."
just install

# compose waits for the db healthcheck, so the database is reachable here.
echo "Running migrations..."
uv run python manage.py migrate --noinput

# Add node_modules/.bin to PATH for vite command
export PATH="/app/frontend/node_modules/.bin:$PATH"

echo "Starting supervisord..."
# Start supervisord
exec uv run supervisord -c /etc/supervisor/supervisord.conf
