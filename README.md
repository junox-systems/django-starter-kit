# Django 5.2 LTS Starter Kit

A modern, production-ready Django starter kit — opinionated, lean, and ready to build on.

## What's Inside

### Backend

| Package | Purpose |
|---------|---------|
| **Django 5.2 LTS** | Core framework |
| **PostgreSQL 18** (ParadeDB image) | Database, BM25/vector search (`django-paradedb`), cache, settings and task queue |
| **RustFS** | S3-compatible media storage in the production stack |
| **Granian** | Production ASGI server (Rust-based, async-native) |
| **Whitenoise** | Static file serving |
| **django-allauth** | Auth — local accounts, OIDC/SSO, social login |
| **django-auditlog** | Automatic model change tracking |
| **django-imagekit** | On-demand image processing (avatar thumbnails) |
| **django-storages** | S3-compatible media file backend |
| **django-anymail** | Transactional email (Postmark / AWS SES) |
| **django-q2** | Background tasks + schedules, Postgres as broker |
| **Sentry SDK** | Error tracking + performance monitoring (opt-in) |
| **OpenTelemetry** | Distributed tracing — Django, psycopg (opt-in) |

### Frontend

| Package | Purpose |
|---------|---------|
| **Stimulus 3** | Controller glue — mounts Svelte components, handles DOM behaviour |
| **Svelte 5** | Interactive islands (for high-interactivity UI) |
| **GSAP 3** | Animations and transitions |
| **Tailwind CSS v4** | Utility-first styling |
| **Basecoat CSS** | Component library (shadcn-compatible tokens) |
| **Vite** | Asset bundler with HMR |

### Developer Tools

| Tool | Purpose |
|------|---------|
| **uv** | Fast Python package manager |
| **pnpm** | Fast JS package manager (Node 24) |
| **ruff** | Linter + formatter |
| **pytest** | Testing framework |
| **django-debug-toolbar** | Query analysis in development |
| **just** | Task runner (`justfile`; the `Makefile` mirrors it) |
| **Docker + mise** | Reproducible dev environment (Debian trixie-slim: x86-64 v1+ and arm64) |

---

## Quick Start

### Prerequisites

- Docker and Docker Compose ([OrbStack](https://orbstack.dev/) recommended on macOS)

### Dockerised (all-in-one)

```bash
git clone <repository-url>
cd django-starter-kit

cp .env.example .env   # optional: every key has a dev default

just dev               # db, Django, Vite, qcluster + ClickStack analytics
just logs              # follow logs
just dev-createsuperuser   # admin@example.com / admin
```

Migrations run automatically every time the app container starts.

Without analytics (lighter, OTEL off):

```bash
just dev-slim          # db + app only
```

ClickStack UI: http://localhost:8080 (no login, local mode).
OTLP endpoint: http://localhost:4318 (HTTP) / http://localhost:4317 (gRPC).

### Local (database in Docker, app on host)

Needs mise (`mise install` provides python, uv, node, pnpm, just).

```bash
docker compose -f dev/docker-compose.dev.yml up -d db
echo 'DATABASE_URL=postgresql://postgres:postgres@localhost:5432/db' >> .env
just install
just migrate

# One terminal each:
just django-dev        # runserver on :8000
just vite-dev          # Vite HMR on :5173
just qcluster-dev      # django-q2 workers + scheduler
```

Dev keeps media on local disk (`media/`). S3 is configured only in the
production stack.

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
| ClickStack | `8080` / `4317` / `4318` | `just dev` only: UI / OTLP gRPC / OTLP HTTP |

These ports are published on your host. Stop anything already bound to them
(a local Postgres, say) before `just dev`.

---

## Project Structure

```
django-starter-kit/
├── apps/
│   ├── core/          # BaseModel (UUID + timestamps) — keep lean
│   ├── users/         # User model (email login, avatar, auditlog)
│   ├── api/           # API endpoints (DMR)
│   ├── pages/         # Static/marketing pages, terms, privacy
│   ├── dashboard/     # Authenticated home
│   └── orgs/          # Organizations, roles, email invitations
├── config/
│   ├── settings/
│   │   ├── base.py        # Shared config
│   │   ├── dev.py         # Development overrides
│   │   ├── production.py  # Production hardening
│   │   └── test.py        # Test isolation
│   ├── asgi.py            # ASGI entry point (+ OTEL init)
│   └── otel.py            # OpenTelemetry setup (opt-in)
├── frontend/
│   └── src/
│       ├── css/styles.css # Tailwind v4 + Basecoat
│       └── js/
│           ├── main.js                # Stimulus + GSAP bootstrap
│           └── controllers/           # Stimulus controllers (auto-registered)
├── templates/             # Django templates
├── dev/                   # Docker dev environment
│   ├── Dockerfile
│   ├── docker-compose.dev.yml
│   ├── supervisord.conf
│   └── init.sh
├── justfile           # Task runner (Makefile mirrors it)
└── pyproject.toml         # All Python deps (managed by uv)
```

---

## Common Commands

```bash
# Dev environment (Docker)
just dev             # Start the stack (alias of dev-up)
just dev-slim        # Same, without analytics
just stop            # Stop the stack
just logs            # Follow logs
just bash            # Shell in the app container
just shell           # Django shell in the app container
just dev-clean       # Destroy containers + volumes (deletes the dev DB)

# App on host
just django-dev      # runserver
just vite-dev        # Vite HMR dev server
just qcluster-dev    # django-q2 workers + scheduler

# Database
just makemigrations  # Generate migrations
just migrate         # Apply migrations

# Quality
just lint            # ruff check
just lint-fix        # ruff check --fix
just format          # ruff format
just precommit       # all pre-commit hooks
just test            # pytest
```

`make <target>` works for the same names, except `precommit` (just only).

---

## Environment Variables

Copy `.env.example` to `.env`. It lists every key the settings read, with
comments. Real environment variables win over `.env`.

---

## Production Checklist

Before deploying:

1. **Set environment:** `ENVIRONMENT=production` + `DJANGO_SETTINGS_MODULE=config.settings.production`
2. **SSL/TLS:** Configure reverse proxy; then enable `SECURE_PROXY_SSL_HEADER`, `SECURE_SSL_REDIRECT`, and HSTS in `production.py`
3. **Static files:** built into the image (`just vite-build && just collectstatic`)
4. **Database:** migrations run on container start (`prod/init.sh`) under a Postgres advisory lock, so replicas never migrate concurrently
5. **Hosts:** set `ALLOWED_HOSTS`, keeping `localhost`: the container healthcheck calls `/healthz/` with `Host: localhost`
6. **Sentry:** Set `SENTRY_DSN` for error tracking
7. **Email:** Set `POSTMARK_SERVER_TOKEN` (or swap `EMAIL_BACKEND`)
8. **Legal:** replace the placeholder text in `templates/pages/terms.html` and `privacy.html`

### Production (Docker Swarm)

Build image and deploy stack:

```bash
export IMAGE_NAME=your-registry/django-starter-kit:latest
just stack-build
docker tag django-starter-kit $IMAGE_NAME
docker push $IMAGE_NAME
just stack-deploy
```

Required env vars:
- `SECRET_KEY` — Django secret
- `IMAGE_NAME` — Docker image for stack
- `POSTGRES_PASSWORD` — DB password
- `RUSTFS_SECRET_KEY` — S3 secret key
- `DEFAULT_FROM_EMAIL` — sender verified in Postmark
- `CSRF_TRUSTED_ORIGINS` — public https origin(s), e.g. `https://example.com`

### Known Caveats

| Caveat | Detail |
|--------|--------|
| **Python 3.14** | Recent. Every current dependency ships wheels, so the images carry no compiler; add `build-essential` to the builder if one ever needs a source build. |
| **Root-owned files** | The dev container runs as root, so files it writes into the bind mount (e.g. `just makemigrations` via `just bash`) are root-owned on the host. `sudo chown -R $USER .` fixes it. |
| **DMR 0.x** | API framework pre-1.0. Pin version in `pyproject.toml` for stability. |
| **Granian** | Rust ASGI server — mature but smaller ecosystem than Gunicorn+Uvicorn. |
| **Postgres does it all** | Cache, sessions and the task queue live in Postgres — no Redis. Add a dedicated cache/broker only when load demands it. |

---

## Documentation

| Doc | Contents |
|-----|---------|
| [BRIEF.md](BRIEF.md) | Full architecture specification |
| [DEVELOPMENT.md](DEVELOPMENT.md) | Developer guide — models, frontend patterns, conventions |
| [CHANGELOG.md](CHANGELOG.md) | Release changelog |

---

## License

MIT — see [LICENSE](LICENSE).
