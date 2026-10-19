# syntax=docker/dockerfile:1

#### Builder stage
FROM debian:trixie-slim AS builder

ARG MISE_VERSION=2026.8.0

ENV UV_NO_CACHE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1

# Debian's x86-64 baseline runs on v2 CPUs; AlmaLinux/RHEL 10 require v3.
# No compiler: every dependency ships prebuilt wheels/binaries.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl xz-utils \
    && rm -rf /var/lib/apt/lists/* \
    && curl -fsSL "https://github.com/jdx/mise/releases/download/v${MISE_VERSION}/mise-v${MISE_VERSION}-linux-$(uname -m | sed 's/x86_64/x64/;s/aarch64/arm64/').tar.xz" \
    | tar -xJf - -C /usr/local/bin --strip-components=2 mise/bin/mise

WORKDIR /app

SHELL ["/bin/bash", "-c"]

COPY mise.toml /app/mise.toml
COPY pyproject.toml uv.lock /app/
COPY frontend/package.json frontend/pnpm-lock.yaml ./frontend/

RUN mise trust && mise install

ENV PATH="/root/.local/share/mise/shims:${PATH}"

RUN uv sync --frozen && \
    cd frontend && pnpm install --frozen-lockfile

COPY . .

RUN just vite-build && \
    just collectstatic

#### Runtime stage
FROM debian:trixie-slim AS runtime

ARG MISE_VERSION=2026.8.0

ENV ENVIRONMENT=production \
    DJANGO_SETTINGS_MODULE=config.settings.production \
    PYTHONUNBUFFERED=1 \
    UV_NO_CACHE=1 \
    UV_NO_DEV=1 \
    MISE_DATA_DIR=/opt/mise \
    MISE_CONFIG_DIR=/opt/mise

# curl is also the healthcheck client.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl xz-utils \
    && rm -rf /var/lib/apt/lists/* \
    && curl -fsSL "https://github.com/jdx/mise/releases/download/v${MISE_VERSION}/mise-v${MISE_VERSION}-linux-$(uname -m | sed 's/x86_64/x64/;s/aarch64/arm64/').tar.xz" \
    | tar -xJf - -C /usr/local/bin --strip-components=2 mise/bin/mise

RUN useradd --create-home --shell /bin/bash django_user && \
    mkdir -p /opt/mise && \
    chown -R root:django_user /opt/mise && \
    chmod -R 775 /opt/mise

WORKDIR /app

SHELL ["/bin/bash", "-c"]

COPY prod/mise.runtime.toml /app/mise.toml
COPY pyproject.toml uv.lock /app/

RUN chown -R django_user:django_user /app

USER django_user

ENV PATH="/opt/mise/shims:${PATH}"

RUN mise trust && mise install

RUN uv sync --frozen --no-dev

USER root

COPY --from=builder /app/staticfiles /app/staticfiles
COPY --from=builder /app/frontend/dist /app/frontend/dist
COPY --chown=django_user:django_user . .
# Re-copy runtime-scoped config: COPY . . clobbers the runtime mise.toml with the dev-scoped one
COPY prod/mise.runtime.toml /app/mise.toml

COPY prod/init.sh /init.sh
RUN chmod +x /init.sh && chown django_user:django_user /init.sh

USER django_user

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import socket; s=socket.create_connection(('localhost',8000),timeout=2); s.close()" || exit 1

EXPOSE 8000

ENTRYPOINT ["/init.sh"]
CMD ["uv", "run", "granian", "--interface", "asginl", "--workers", "3", "--runtime-mode", "mt", "--loop", "uvloop", "--host", "0.0.0.0", "--port", "8000", "config.asgi:application"]
