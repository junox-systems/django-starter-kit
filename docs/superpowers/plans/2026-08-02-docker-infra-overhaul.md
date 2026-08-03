# Docker Infrastructure Overhaul Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace dev minio with rustfs, add clickstack observability to dev, rewrite prod Dockerfile as multi-stage almalinux:10-kitten-minimal with uv-only pattern, create docker swarm stack file replacing root compose, clean up dead code.

**Architecture:** Single Dockerfile with multi-stage build (builder + runtime). Compose/swarm dispatch service role via command override — no supervisor. Dev compose includes rustfs S3 and clickstack (analytics profile). Prod stack uses pgvector/pgvector for postgres with vector extensions.

**Tech Stack:** Docker Compose, Docker Swarm, AlmaLinux 10, mise, uv, RustFS, ClickStack (ClickHouse observability), pgvector

## Global Constraints

- Base image: `almalinux:10-kitten-minimal` (both stages)
- Python runtime user: `django_user` (not wagtail, not root)
- Package manager: uv only (via mise). No `pip`, no `uv pip install --system`
- S3: `rustfs/rustfs:1.0.0-alpha.86` (dev), pinned version
- Observability: `clickhouse/clickstack-all-in-one:2.21.0` (dev, profile: analytics)
- Postgres: `pgvector/pgvector:0.8.6-pg18` (dev + prod)
- No litestream (project uses postgres, not sqlite)
- No supervisor — single process per container, command dispatched by compose/swarm
- No `version: 3.8` (obsolete)
- Clickstack dev-only (not in prod stack)

---

### Task 1: Add AWS_S3_ENDPOINT_URL to Django settings

**Files:**
- Modify: `config/settings/base.py:214-216`

**Interfaces:**
- Consumes: `env()` from django-environ
- Produces: `AWS_S3_ENDPOINT_URL` setting for django-storages S3 compatibility

- [x] **Step 1: Add AWS_S3_ENDPOINT_URL env var read**

In `config/settings/base.py`, add after line 216:

```python
AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME")
AWS_S3_ENDPOINT_URL = env("AWS_S3_ENDPOINT_URL", default="")
```

- [x] **Step 2: Verify the change**

Run: `python -c "import django; django.setup()" 2>&1 | head -5` (from project root with env)
Expected: No import errors related to settings.

- [x] **Step 3: Commit**

```bash
git add config/settings/base.py
git commit -m "feat: add AWS_S3_ENDPOINT_URL for S3-compatible storage backends"
```

---

### Task 2: Update dev compose — add rustfs S3

**Files:**
- Modify: `dev/docker-compose.dev.yml`

**Interfaces:**
- Consumes: django app service, db service, redis service
- Produces: `s3` service accessible at `s3:9000`, `AWS_S3_ENDPOINT_URL=http://s3:9000` in app env

- [x] **Step 1: Add rustfs s3 service block**

After the `redis` service block (after line 31), add:

```yaml
  s3:
    image: rustfs/rustfs:1.0.0-alpha.86
    container_name: django-s3
    restart: unless-stopped
    volumes:
      - rustfs_data:/data
    ports:
      - "9000:9000"
    environment:
      RUSTFS_ACCESS_KEY: rustfsadmin
      RUSTFS_SECRET_KEY: rustfsadmin
      RUSTFS_ADDRESS: 0.0.0.0:9000
      RUSTFS_EXTERNAL_ADDRESS: ":9000"
      RUSTFS_CORS_ALLOWED_ORIGINS: "*"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 10s
      timeout: 5s
      retries: 3
```

Note: rustfs is minio-compatible. The `/minio/health/live` endpoint works.

- [x] **Step 2: Add s3 to app depends_on and env**

In the `app` service:
- Add `- s3` to `depends_on` list (line ~61)
- Add to `environment` block:

```yaml
      - AWS_ACCESS_KEY_ID=rustfsadmin
      - AWS_SECRET_ACCESS_KEY=rustfsadmin
      - AWS_STORAGE_BUCKET_NAME=devbucket
      - AWS_S3_ENDPOINT_URL=http://s3:9000
```

- [x] **Step 3: Add rustfs_data volume declaration**

In the `volumes:` block at bottom, add:

```yaml
  rustfs_data:
```

- [x] **Step 4: Remove stale comment header**

Remove line 1: `# docker-compose.yml` (stale, file is docker-compose.dev.yml)

- [x] **Step 5: Verify compose file parses**

Run: `docker compose -f dev/docker-compose.dev.yml config --quiet`
Expected: Exit 0, no errors.

- [x] **Step 6: Commit**

```bash
git add dev/docker-compose.dev.yml
git commit -m "feat: add rustfs S3 service to dev compose"
```

---

### Task 3: Add clickstack to dev compose with analytics profile

**Files:**
- Modify: `dev/docker-compose.dev.yml`

**Interfaces:**
- Consumes: nothing (standalone observability service)
- Produces: `clickstack` service on ports 8080 (UI), 4317/4318 (OTLP), activated via `--profile analytics`

- [x] **Step 1: Add clickstack service block**

After the `s3` service, add:

```yaml
  clickstack:
    image: clickhouse/clickstack-all-in-one:2.21.0
    container_name: django-clickstack
    profiles:
      - analytics
    ports:
      - "8080:8080"
      - "4317:4317"
      - "4318:4318"
    volumes:
      - clickstack_db:/data/db
      - clickstack_ch_data:/var/lib/clickhouse
      - clickstack_ch_logs:/var/log/clickhouse-server
```

- [x] **Step 2: Add OTEL env to app for analytics profile**

Add to app `environment` block:

```yaml
      - OTEL_EXPORTER_OTLP_ENDPOINT=http://clickstack:4317
```

Note: only effective when clickstack is running (profile active).

- [x] **Step 3: Add clickstack volume declarations**

In `volumes:` block, add:

```yaml
  clickstack_db:
  clickstack_ch_data:
  clickstack_ch_logs:
```

- [x] **Step 4: Verify compose with analytics profile**

Run: `docker compose -f dev/docker-compose.dev.yml --profile analytics config --quiet`
Expected: Exit 0.

- [x] **Step 5: Commit**

```bash
git add dev/docker-compose.dev.yml
git commit -m "feat: add clickstack observability to dev compose with analytics profile"
```

---

### Task 4: Create prod entrypoint script

**Files:**
- Create: `prod/init.sh`

**Interfaces:**
- Consumes: DATABASE_URL env var
- Produces: runs migrations then exec's the CMD (granian for web, rundramatiq for worker)

- [x] **Step 1: Create prod/init.sh**

```bash
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
```

- [x] **Step 2: Make executable**

```bash
chmod +x prod/init.sh
```

- [x] **Step 3: Commit**

```bash
git add prod/init.sh
git commit -m "feat: add prod entrypoint script with db wait + migrate"
```

---

### Task 5: Rewrite prod Dockerfile (multi-stage, almalinux:10-kitten-minimal, uv-only)

**Files:**
- Modify: `Dockerfile` (rewrite entirely)

**Interfaces:**
- Consumes: mise.toml, pyproject.toml, frontend/package.json, source code
- Produces: production image with built staticfiles, uv-managed .venv, runs as django_user

- [x] **Step 1: Write the builder stage**

Replace `Dockerfile` contents with:

```dockerfile
# syntax=docker/dockerfile:1

#### Builder stage
FROM almalinux:10-kitten-minimal AS builder

ENV UV_NO_CACHE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_SYSTEM_PYTHON=1

RUN dnf install -y \
    dnf-plugins-core \
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
```

- [x] **Step 2: Write the runtime stage**

Append to the Dockerfile:

```dockerfile
#### Runtime stage
FROM almalinux:10-kitten-minimal AS runtime

ENV ENVIRONMENT=production \
    PYTHONUNBUFFERED=1 \
    UV_NO_CACHE=1 \
    MISE_DATA_DIR=/opt/mise \
    MISE_CONFIG_DIR=/opt/mise

RUN dnf install -y \
    dnf-plugins-core \
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
```

Note: HEALTHCHECK uses `/-/health/` — adjust if your health endpoint differs. MISE_DATA_DIR=/opt/mise ensures shims are accessible by django_user (not /root/).

- [x] **Step 3: Verify Dockerfile parses**

Run: `docker build --check .` (or `docker build --no-cache -t test . 2>&1 | tail -20`)
Expected: No syntax errors.

- [x] **Step 4: Commit**

```bash
git add Dockerfile
git commit -m "feat: rewrite prod Dockerfile as multi-stage almalinux:10-kitten-minimal with uv-only"
```

---

### Task 6: Create docker swarm stack file

**Files:**
- Delete: `docker-compose.yml`
- Create: `docker-stack.yml`

**Interfaces:**
- Consumes: prod Dockerfile image, pgvector/pgvector:0.8.6-pg18, valkey/valkey:7-alpine, rustfs
- Produces: web + worker + db + cache + s3 services with deploy config, healthchecks, shared env

- [x] **Step 1: Delete old root docker-compose.yml**

```bash
git rm docker-compose.yml
```

- [x] **Step 2: Create docker-stack.yml**

```yaml
services:
  web:
    image: ${IMAGE_NAME:?IMAGE_NAME required}
    deploy:
      replicas: 2
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
    ports:
      - "8000:8000"
    environment:
      DJANGO_SETTINGS_MODULE: config.settings.production
      DATABASE_URL: postgres://${POSTGRES_USER:-django}:${POSTGRES_PASSWORD:-django}@db:5432/${POSTGRES_DB:-django}
      REDIS_URL: redis://cache:6379/0
      AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID:-}
      AWS_SECRET_ACCESS_KEY: ${AWS_SECRET_ACCESS_KEY:-}
      AWS_STORAGE_BUCKET_NAME: ${AWS_STORAGE_BUCKET_NAME:-}
      AWS_S3_ENDPOINT_URL: ${AWS_S3_ENDPOINT_URL:-}
      SENTRY_DSN: ${SENTRY_DSN:-}
      POSTMARK_SERVER_TOKEN: ${POSTMARK_SERVER_TOKEN:-}
      ALLOWED_HOSTS: ${ALLOWED_HOSTS:-localhost}
      SECRET_KEY: ${SECRET_KEY:?SECRET_KEY required}
    depends_on:
      db:
        condition: service_healthy
      cache:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "python", "-c", "import socket; s=socket.create_connection(('localhost',8000),timeout=2); s.close()"]
      interval: 30s
      timeout: 5s
      retries: 3
    networks:
      - backend

  worker:
    image: ${IMAGE_NAME:?IMAGE_NAME required}
    entrypoint: ["/init.sh"]
    command: ["uv", "run", "python", "manage.py", "rundramatiq"]
    deploy:
      replicas: 1
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
    environment:
      DJANGO_SETTINGS_MODULE: config.settings.production
      DATABASE_URL: postgres://${POSTGRES_USER:-django}:${POSTGRES_PASSWORD:-django}@db:5432/${POSTGRES_DB:-django}
      REDIS_URL: redis://cache:6379/0
      AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID:-}
      AWS_SECRET_ACCESS_KEY: ${AWS_SECRET_ACCESS_KEY:-}
      AWS_STORAGE_BUCKET_NAME: ${AWS_STORAGE_BUCKET_NAME:-}
      AWS_S3_ENDPOINT_URL: ${AWS_S3_ENDPOINT_URL:-}
      SENTRY_DSN: ${SENTRY_DSN:-}
      POSTMARK_SERVER_TOKEN: ${POSTMARK_SERVER_TOKEN:-}
      SECRET_KEY: ${SECRET_KEY:?SECRET_KEY required}
    depends_on:
      db:
        condition: service_healthy
      cache:
        condition: service_healthy
    networks:
      - backend

  db:
    image: pgvector/pgvector:0.8.6-pg18
    deploy:
      replicas: 1
      restart_policy:
        condition: any
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-django}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-django}
      POSTGRES_DB: ${POSTGRES_DB:-django}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-django} -d ${POSTGRES_DB:-django}"]
      interval: 5s
      timeout: 5s
      retries: 5
    networks:
      - backend

  cache:
    image: valkey/valkey:7-alpine
    deploy:
      replicas: 1
      restart_policy:
        condition: any
    healthcheck:
      test: ["CMD", "valkey-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5
    networks:
      - backend

  s3:
    image: rustfs/rustfs:1.0.0-alpha.86
    deploy:
      replicas: 1
      restart_policy:
        condition: any
    environment:
      RUSTFS_ACCESS_KEY: ${RUSTFS_ACCESS_KEY:-rustfsadmin}
      RUSTFS_SECRET_KEY: ${RUSTFS_SECRET_KEY:-rustfsadmin}
      RUSTFS_ADDRESS: 0.0.0.0:9000
      RUSTFS_EXTERNAL_ADDRESS: ":9000"
      RUSTFS_CORS_ALLOWED_ORIGINS: "*"
    volumes:
      - rustfs_data:/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/health"]
      interval: 10s
      timeout: 5s
      retries: 3
    networks:
      - backend

volumes:
  postgres_data:
  rustfs_data:

networks:
  backend:
    driver: overlay
```

- [x] **Step 3: Verify stack file parses**

Run: `docker stack deploy --dry-run -c docker-stack.yml test-stack` (or `docker compose -f docker-stack.yml config --quiet` for syntax check)
Expected: No errors.

- [x] **Step 4: Commit**

```bash
git add docker-stack.yml
git commit -m "feat: add docker swarm stack file replacing root compose

- Removed rabbitmq broker (dead code; dramatiq uses Redis)
- Replaced paradedb with pgvector/pgvector:0.8.6-pg18
- Replaced redis with valkey/valkey:7-alpine
- Added rustfs S3 service
- Added healthchecks and deploy policies
- Unified env blocks for web/worker (no drift)"
```

---

### Task 7: Update Makefile

**Files:**
- Modify: `Makefile`

**Interfaces:**
- Consumes: docker-stack.yml, dev/docker-compose.dev.yml
- Produces: new targets: stack-build, stack-deploy, stack-logs, stack-rm

- [x] **Step 1: Update docker-build target**

Replace existing `docker-build` target:

```makefile
.PHONY: docker-build
docker-build:
	docker build -t django-starter-kit .
```

(No change needed — already points to root Dockerfile, which is now the multi-stage one.)

- [x] **Step 2: Add swarm stack targets**

Add after `## - END PROD - ##`:

```makefile
#### - STACK - #### ------------------------------------------------------------------------------
.PHONY: stack-build
stack-build:
	docker build -t django-starter-kit .

.PHONY: stack-deploy
stack-deploy:
	IMAGE_NAME=django-starter-kit docker stack deploy -c docker-stack.yml django-starter-kit

.PHONY: stack-rm
stack-rm:
	docker stack rm django-starter-kit

.PHONY: stack-logs
stack-logs:
	docker service logs -f django-starter-kit_web

.PHONY: stack-ps
stack-ps:
	docker stack services django-starter-kit
## - END STACK - ##
```

- [x] **Step 3: Update dev compose commands to support analytics profile**

Replace existing dev-up:

```makefile
.PHONY: dev-up dev
dev-up dev:
	docker compose -f dev/docker-compose.dev.yml up --build -d

.PHONY: dev-up-analytics
dev-up-analytics:
	docker compose -f dev/docker-compose.dev.yml --profile analytics up --build -d
```

- [x] **Step 4: Commit**

```bash
git add Makefile
git commit -m "feat: add swarm stack targets and analytics profile shortcut to Makefile"
```

---

### Task 8: Verify all changes work together

- [x] **Step 1: Dev compose — validate full stack**

Run:
```bash
docker compose -f dev/docker-compose.dev.yml config --quiet
docker compose -f dev/docker-compose.dev.yml --profile analytics config --quiet
```
Expected: Both exit 0.

- [x] **Step 2: Dev — boot stack**

Run:
```bash
make dev-up-analytics
```
Expected: All services start. `docker compose -f dev/docker-compose.dev.yml --profile analytics ps` shows db, redis, s3, app, clickstack all running.

- [x] **Step 3: Verify S3 connectivity from app**

Create the bucket the app expects (rustfs does not auto-create buckets):

Run:
```bash
docker compose -f dev/docker-compose.dev.yml exec app uv run python -c "
import boto3
s3 = boto3.client('s3', endpoint_url='http://s3:9000', aws_access_key_id='rustfsadmin', aws_secret_access_key='rustfsadmin')
s3.create_bucket(Bucket='devbucket')
print('S3 OK')
"
```
Expected: "S3 OK" (bucket devbucket created — matches `AWS_STORAGE_BUCKET_NAME=devbucket` in app env)

- [x] **Step 4: Verify clickstack UI accessible**

Open: http://localhost:8080
Expected: HyperDX UI loads.

- [x] **Step 5: Prod Dockerfile — build**

Run:
```bash
make docker-build
```
Expected: Multi-stage build completes. Image size reasonable (~300-500MB).

- [x] **Step 6: Stack file — validate**

Run:
```bash
docker compose -f docker-stack.yml config --quiet
```
Expected: Exit 0.

- [x] **Step 7: Clean up dev**

Run:
```bash
make dev-clean
```

- [x] **Step 8: Final commit (if any fixes needed)**

```bash
git add -A
git commit -m "fix: resolve verification issues"
```

---

### Task 9: Update README

**Files:**
- Modify: `README.md`

- [x] **Step 1: Add dev analytics section**

Add to dev section:

```markdown
### Development with Analytics

Start dev stack with ClickStack observability:

```bash
make dev-up-analytics
```

ClickStack UI: http://localhost:8080
OTLP endpoint: http://localhost:4318 (HTTP) / http://localhost:4317 (gRPC)

Without analytics:
```bash
make dev-up
```

Note: dev compose requires a root `.env` file (referenced by `env_file: ../.env`). An empty one works; create it with `touch .env` if missing.

- [x] **Step 2: Update prod section**

Replace/update prod deployment docs:

```markdown
### Production (Docker Swarm)

Build image and deploy stack:

```bash
export IMAGE_NAME=your-registry/django-starter-kit:latest
make stack-build
docker tag django-starter-kit $IMAGE_NAME
docker push $IMAGE_NAME
make stack-deploy
```

Required env vars:
- `SECRET_KEY` — Django secret
- `IMAGE_NAME` — Docker image for stack
- `POSTGRES_PASSWORD` — DB password
```

- [x] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: update README for rustfs, clickstack, swarm stack"
```
