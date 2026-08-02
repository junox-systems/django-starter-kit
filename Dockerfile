# syntax=docker/dockerfile:1

#### Builder stage
FROM almalinux:10-kitten-minimal AS builder

ENV UV_NO_CACHE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_SYSTEM_PYTHON=1

RUN microdnf install -y dnf dnf-plugins-core \
    && dnf install -y \
    gcc \
    make \
    openssl-devel \
    libffi-devel \
    && dnf config-manager --add-repo https://mise.jdx.dev/rpm/mise.repo \
    && dnf install -y --nodocs mise \
    && dnf clean all \
    && rm -rf /var/cache/dnf

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

RUN make vite-build && \
    make collectstatic

#### Runtime stage
FROM almalinux:10-kitten-minimal AS runtime

ENV ENVIRONMENT=production \
    PYTHONUNBUFFERED=1 \
    UV_NO_CACHE=1 \
    MISE_DATA_DIR=/opt/mise \
    MISE_CONFIG_DIR=/opt/mise

RUN microdnf install -y dnf dnf-plugins-core \
    && dnf config-manager --add-repo https://mise.jdx.dev/rpm/mise.repo \
    && dnf install -y --nodocs mise \
    && dnf clean all \
    && rm -rf /var/cache/dnf

RUN useradd --create-home --shell /bin/bash django_user && \
    mkdir -p /opt/mise && \
    chown -R root:django_user /opt/mise && \
    chmod -R 775 /opt/mise

WORKDIR /app

SHELL ["/bin/bash", "-c"]

COPY mise.toml /app/mise.toml
COPY pyproject.toml uv.lock /app/

RUN mise trust && mise install

ENV PATH="/opt/mise/shims:${PATH}"

RUN uv sync --frozen --no-dev

COPY --from=builder /app/staticfiles /app/staticfiles
COPY --from=builder /app/frontend/dist /app/frontend/dist
COPY --chown=django_user:django_user . .

COPY prod/init.sh /init.sh
RUN chmod +x /init.sh

RUN chown -R django_user:django_user /app /init.sh

USER django_user

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import socket; s=socket.create_connection(('localhost',8000),timeout=2); s.close()" || exit 1

EXPOSE 8000

ENTRYPOINT ["/init.sh"]
CMD ["uv", "run", "granian", "--interface", "asginl", "--workers", "3", "--runtime-mode", "mt", "--loop", "uvloop", "--host", "0.0.0.0", "--port", "8000", "config.asgi:application"]
