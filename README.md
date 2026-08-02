# Django 5.2 LTS Starter Kit

A modern, production-ready Django starter kit — opinionated, lean, and ready to build on.

## What's Inside

### Backend

| Package | Purpose |
|---------|---------|
| **Django 5.2 LTS** | Core framework |
| **ParadeDB** (PostgreSQL 17) | Database + BM25 full-text search |
| **Redis / Valkey 7** | Cache (`django-cacheops`) + sessions + Dramatiq broker |
| **MinIO** | S3-compatible local object storage |
| **Granian** | Production ASGI server (Rust-based, async-native) |
| **Whitenoise** | Static file serving |
| **django-allauth** | Auth — local accounts, OIDC/SSO, social login |
| **django-auditlog** | Automatic model change tracking |
| **django-imagekit** | On-demand image processing (avatar thumbnails) |
| **django-storages** | S3-compatible media file backend |
| **django-anymail** | Transactional email (Postmark / AWS SES) |
| **Dramatiq** | Background task queue |
| **Sentry SDK** | Error tracking + performance monitoring (opt-in) |
| **OpenTelemetry** | Distributed tracing — Django, psycopg, Redis (opt-in) |

### Frontend

| Package | Purpose |
|---------|---------|
| **Stimulus 3** | Controller glue — mounts Svelte components, handles DOM behaviour |
| **Svelte 5** | Interactive islands (for high-interactivity UI) |
| **GSAP 3** | Animations and transitions |
| **Tailwind CSS v4** | Utility-first styling |
| **DaisyUI v5** | Component library |
| **Vite** | Asset bundler with HMR |

### Developer Tools

| Tool | Purpose |
|------|---------|
| **uv** | Fast Python package manager |
| **pnpm** | Fast JS package manager (Node 24) |
| **ruff** | Linter + formatter |
| **pytest** | Testing framework |
| **django-debug-toolbar** | Query analysis in development |
| **Docker + mise** | Reproducible dev environment |

---

## Quick Start

### Prerequisites

- Docker and Docker Compose ([OrbStack](https://orbstack.dev/) recommended on macOS)

### Dockerised (all-in-one)

```bash
git clone <repository-url>
cd django-starter-kit

cp .env.example .env   # configure your environment

make dev-up            # starts DB, Redis, MinIO, Django, Vite, worker
make dev-logs          # follow logs
```

First-time setup:

```bash
make dev-shell
# inside the container:
python manage.py migrate
python manage.py createsuperuser
```

### Local (services in Docker, app on host)

Run infrastructure only, then start the app processes locally for faster iteration:

```bash
docker compose -f dev/docker-compose.dev.yml up db redis s3 -d

# Terminal 1 — Django
make django-dev

# Terminal 2 — Vite (HMR)
make vite-dev

# Terminal 3 — Dramatiq worker
make worker-dev
```

Then:

```bash
make migrate           # run migrations
```

### Development with Analytics

Start dev stack with ClickStack observability:

```bash
make dev-up-analytics
```

ClickStack UI: http://localhost:8080 (no login — local mode)
OTLP endpoint: http://localhost:4318 (HTTP) / http://localhost:4317 (gRPC)

Without analytics:
```bash
make dev-up
```

Note: dev compose requires a root `.env` file (referenced by `env_file: ../.env`). An empty one works; create it with `touch .env` if missing.

---

## Frontend Architecture

**Primary rendering: Django templates + HTML forms.** Standard full-page loads for most interactions.

**Interactive islands: Stimulus mounts Svelte 5 components.** Use the generic bridge controller:

```html
<div data-controller="svelte-bridge"
     data-svelte-bridge-component-value="YourComponent"
     data-svelte-bridge-props-value='{"key": "value"}'>
</div>
```

Svelte components live in `frontend/src/js/svelte/` and are lazy-loaded via dynamic import. Only components on the page are downloaded.

**Animations: GSAP 3** for transitions and micro-interactions in both Stimulus controllers and Svelte components.

---

## Services & Ports

| Service | Port | Notes |
|---------|------|-------|
| Django | `8000` | Main app |
| Vite HMR | `5173` | Dev only — proxied by django-vite |
| PostgreSQL | `5432` | |
| Redis | `6379` | |
| MinIO | `9000` / `9001` | S3 API / Web UI |

---

## Project Structure

```
django-starter-kit/
├── apps/
│   ├── core/          # BaseModel (UUID + timestamps) — keep lean
│   ├── users/         # User model (email login, avatar, auditlog)
│   ├── api/           # API endpoints (DMR)
│   └── pages/         # Static/marketing pages
├── config/
│   ├── settings/
│   │   ├── base.py        # Shared config
│   │   ├── dev.py         # Development overrides
│   │   ├── production.py  # Production hardening
│   │   └── test.py        # Test isolation
│   ├── asgi.py            # ASGI entry point (Channels boilerplate)
│   └── otel.py            # OpenTelemetry setup (opt-in)
├── frontend/
│   └── src/
│       ├── css/styles.css # Tailwind v4 + DaisyUI
│       └── js/
│           ├── main.js                # Stimulus + GSAP bootstrap
│           └── controllers/           # Stimulus controllers (auto-registered)
├── templates/             # Django templates
├── dev/                   # Docker dev environment
│   ├── Dockerfile
│   ├── docker-compose.dev.yml
│   ├── supervisord.conf
│   └── init.sh
├── Makefile
└── pyproject.toml         # All Python deps (managed by uv)
```

---

## Common Commands

```bash
# Dev environment
make dev-up          # Start Docker services
make dev-down        # Stop Docker services
make dev-logs        # Follow logs
make dev-clean       # Destroy containers + volumes

# Local development
make django-dev      # Granian ASGI server with reload
make vite-dev        # Vite HMR dev server
make worker-dev      # Dramatiq worker with reload

# Database
make makemigrations  # Generate migrations
make migrate         # Apply migrations

# Quality
make lint            # ruff check
make lint-fix        # ruff check --fix
make format          # ruff format
make test            # pytest
```

---

## Environment Variables

Copy `.env.example` to `.env` and fill in values. Key variables:

```bash
DJANGO_SETTINGS_MODULE=config.settings.dev   # or .production / .test
SECRET_KEY=...
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/db
REDIS_URL=redis://localhost:6379

# Optional — initialises only if set
SENTRY_DSN=https://...

# Optional — opt-in distributed tracing
OTEL_ENABLED=true
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
```

---

## Production Checklist

Before deploying:

1. **Set environment:** `ENVIRONMENT=production` + `DJANGO_SETTINGS_MODULE=config.settings.production`
2. **SSL/TLS:** Configure reverse proxy; then enable `SECURE_PROXY_SSL_HEADER`, `SECURE_SSL_REDIRECT`, and HSTS in `production.py`
3. **Static files:** `make vite-build && python manage.py collectstatic --no-input`
4. **Database:** `python manage.py migrate`
5. **Sentry:** Set `SENTRY_DSN` for error tracking
6. **Email:** Set `POSTMARK_SERVER_TOKEN` (or swap `EMAIL_BACKEND`)

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
- `RUSTFS_SECRET_KEY` — S3 secret key

### Known Caveats

| Caveat | Detail |
|--------|--------|
| **Python 3.14** | Bleeding-edge. Some packages may lack pre-built wheels. `uv` handles source builds. |
| **DMR 0.x** | API framework pre-1.0. Pin version in `pyproject.toml` for stability. |
| **Granian** | Rust ASGI server — mature but smaller ecosystem than Gunicorn+Uvicorn. |
| **Redis single-node** | Cache, sessions, broker, Channels share one Redis. Shard for high traffic. |

---

## Documentation

| Doc | Contents |
|-----|---------|
| [BRIEF.md](BRIEF.md) | Full architecture specification |
| [DEVELOPMENT.md](DEVELOPMENT.md) | Developer guide — models, frontend patterns, conventions |
| [AGENT_LOGS.md](AGENT_LOGS.md) | Implementation history |
| [CHANGELOG.md](CHANGELOG.md) | Release changelog |

---

## License

MIT — see [LICENSE](LICENSE).
