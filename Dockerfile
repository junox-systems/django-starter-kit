# syntax=docker/dockerfile:1

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY pyproject.toml .

RUN pip install uv

# Install Python dependencies
COPY pyproject.toml .
RUN uv pip install --system --no-cache-dir .

# Install Node 24 + pnpm and frontend dependencies
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_24.x | bash - && \
    apt-get install -y nodejs && \
    npm install -g pnpm
COPY frontend/package.json frontend/pnpm-lock.yaml ./frontend/
RUN cd frontend && pnpm install --frozen-lockfile

# Build frontend assets
COPY frontend/src ./frontend/src
COPY frontend/vite.config.mjs ./frontend/
RUN cd frontend && pnpm run build

# Copy remaining project files
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uv", "run", "granian", "--interface", "asgi", "--log-level", "info", "config.asgi:application"]