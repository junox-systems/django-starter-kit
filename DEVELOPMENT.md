# Developer Guide

This document provides in-depth guidance for developers working on or extending this starter kit.

---

## Docker Development Environment

The project includes a complete Docker development environment with all necessary services.

### Services

| Service | Image | Purpose |
|---------|-------|---------|
| **ParadeDB** | `paradedb/paradedb:0.18.0-pg17` | PostgreSQL 17 + BM25 search extensions |
| **Redis / Valkey** | `valkey/valkey:7-alpine` | Cache, session storage |
| **MinIO** | `bitnami/minio:2025.4.22` | S3-compatible local object storage (UI at `:9001`) |

> **Note:** Pin MinIO to `2025.4.22` — newer versions removed the web UI.

### Development Commands

```bash
make dev-up        # Start all services (detached)
make dev-down      # Stop all services
make dev-logs      # Follow container logs
make dev-clean     # Stop and remove volumes (clean slate)
make dev-restart   # Shortcut: dev-down + dev-up
make dev-bash      # Shell into the app container
make dev-shell     # Django manage.py shell inside container
```

### Local (non-Docker) Dev

Run services via Docker, app locally for faster iteration:

```bash
# Terminal 1 — Django (Granian ASGI, auto-reload)
make django-dev

# Terminal 2 — Frontend (Vite HMR)
make vite-dev

# Terminal 3 — Dramatiq worker (auto-reload)
make worker-dev
```

---

## Settings & Environment

Settings are split by environment. Select the active file via `DJANGO_SETTINGS_MODULE`:

| Value | Use |
|-------|-----|
| `config.settings.dev` | Local development (default in `manage.py` and `asgi.py`) |
| `config.settings.production` | Production |
| `config.settings.test` | Automated testing (set in `pyproject.toml`) |

There is no routing logic in `config/settings/__init__.py` — it is intentionally empty. Set `DJANGO_SETTINGS_MODULE` in your shell, `.env`, or process manager.

### Key Environment Variables

```bash
# Required in production
SECRET_KEY=...
DATABASE_URL=postgresql://user:pass@host:5432/db
REDIS_URL=redis://host:6379
ENVIRONMENT=production

# Optional — Sentry (only initialises if set)
SENTRY_DSN=https://...

# Optional — OpenTelemetry (opt-in)
OTEL_ENABLED=true
OTEL_EXPORTER_OTLP_ENDPOINT=http://host:4317
OTEL_SERVICE_NAME=django-starter-kit

# Optional — S3 storage (falls back to local if not set)
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_STORAGE_BUCKET_NAME=...

# Optional — Email
POSTMARK_SERVER_TOKEN=...
```

---

## Architectural Philosophy

**Separation of concerns** and **developer velocity** — without over-engineering.

- **`apps/` vs `frontend/`:** Python/Django code in `apps/`. All JS, CSS, and images in `frontend/`. Clean boundary between backend and frontend work.
- **The `core` App:** Only truly universal, project-wide code lives here. Currently: `BaseModel` (UUID + timestamps). If a piece of functionality grows (e.g., notifications), extract it to its own dedicated app.
- **Fat Models, Thin Views:** Business logic in models, managers, and service functions. Views are thin HTTP handlers.
- **Let Packages Do Their Job:** Don't reimplement what `django-allauth`, `django-auditlog`, or `django-cacheops` already provide. Write integration, not reimplementation.

---

## Dependency Management

**Python** — managed by `uv` via `pyproject.toml`:

```bash
uv add <package>     # Add a dependency
uv remove <package>  # Remove a dependency
uv sync              # Install/sync from lockfile
```

**Frontend** — managed by `pnpm` (Node 24) via `frontend/package.json`:

```bash
cd frontend
pnpm add <package>
pnpm remove <package>
pnpm install
```

---

## Models

### BaseModel

All custom models inherit from `apps.core.models.BaseModel`:

```python
from apps.core.models import BaseModel

class MyModel(BaseModel):
    name = models.CharField(max_length=100)
    # Inherits: id (UUID), created_at, updated_at
```

There is no `SoftDeleteModel` built in. If you need soft-delete, add `django-safedelete` and configure it per-app.

### User Model

The `User` model lives in `apps/users/models.py` and is intentionally minimal:

- Email-based login (`USERNAME_FIELD = "email"`)
- UUID primary key from `BaseModel`
- `avatar` + `avatar_thumbnail` (auto-generated 100×100 JPEG via imagekit)
- All `AbstractUser` fields (`first_name`, `last_name`, `is_active`, `is_staff`, etc.)
- Automatic audit trail via `django-auditlog`

**Auth, social login, and email verification are fully managed by `django-allauth`.** Do not add OIDC fields to the `User` model — allauth stores provider data in `SocialAccount`.

### Audit Logging

`django-auditlog` is pre-configured. To add audit logging to a new model:

```python
from auditlog.registry import auditlog

class MyModel(BaseModel):
    ...

auditlog.register(MyModel)
```

Logs are accessible at `/admin/auditlog/` and via `MyModel.history`.

### Caching (django-cacheops)

Declarative ORM-level caching is provided by `django-cacheops`. Configure in `config/settings/base.py`:

```python
CACHEOPS = {
    "users.User": {"ops": "get", "timeout": 60 * 15},
    "myapp.MyModel": {"ops": ("fetch", "get"), "timeout": 60 * 5},
}
```

`CACHEOPS_DEGRADE_ON_FAILURE = True` means the app works normally if Redis is down.

---

## Frontend Workflow

### Paradigm

Three complementary layers — no overlap:

| Layer | Tool | Use case |
|-------|------|----------|
| In-place HTML | **htmx 2** | Form submissions, partial swaps, server-rendered fragments |
| Controller glue | **Stimulus 3** | Mounting Svelte components, minor DOM behaviour |
| Interactive islands | **Svelte 5** | Complex client-side UI with state (calls the API) |
| Animations | **GSAP 3** | Transitions, entrance/exit effects |

**Do not mix paradigms.** If a page section needs Svelte, mount it via a Stimulus controller. If it just needs a form to submit in-place, use htmx.

### Vite Build

- **Development:** Vite runs HMR at `:5173`. Django-vite proxies assets automatically via `{% vite_hmr_client %}`.
- **Production:** `pnpm run build` outputs hashed assets to `frontend/dist/`. Whitenoise serves them.

```bash
make vite-dev    # HMR dev server
make vite-build  # Production build
```

### Adding a Stimulus Controller

Create `frontend/src/js/controllers/my-feature.js`:

```javascript
import { Controller } from "@hotwired/stimulus";

export default class extends Controller {
  connect() {
    // runs when element with data-controller="my-feature" enters the DOM
  }
}
```

Controllers are auto-registered via `import.meta.glob` in `main.js`. Filename `my-feature.js` → `data-controller="my-feature"`.

### Mounting a Svelte Component

```javascript
// frontend/src/js/controllers/my-island.js
import { Controller } from "@hotwired/stimulus";
import { mount, unmount } from "svelte";
import { Components as C } from "$lib/components";

export default class extends Controller {
  connect() {
    this.component = mount(C.MyComponent, { target: this.element });
  }
  disconnect() {
    if (this.component) unmount(this.component);
  }
}
```

In your template:

```html
<div data-controller="my-island"></div>
```

---

## Database Conventions

- All new models inherit from `BaseModel`.
- Use `select_related` (FK/one-to-one) and `prefetch_related` (M2M/reverse relations) in querysets to prevent N+1 problems.
- Django Debug Toolbar is available in development at `/__debug__/`.

---

## Observability

### Sentry

Initialises automatically if `SENTRY_DSN` is set. Features:

- Error tracking across Django + Dramatiq
- Performance tracing at **10% sample rate** (no PII)

### OpenTelemetry

Opt-in via `OTEL_ENABLED=true`. Instruments Django, psycopg, and Redis. Exports to any OTLP-compatible backend (SigNoz, Grafana Tempo, etc.).

---

## CI/CD Pipeline

The `.github/workflows/ci.yml` pipeline runs on every push and pull request to `main`:

1. **Linting** — `ruff check`
2. **Testing** — `pytest` with `config.settings.test`
3. **Docker Build** — validates the production image builds cleanly

---

## Task Queue (Dramatiq)

Background tasks are defined with the `@dramatiq.actor` decorator:

```python
# apps/myapp/tasks.py
import dramatiq

@dramatiq.actor
def send_welcome_email(user_id: str):
    # runs asynchronously in the worker process
    ...
```

Enqueue from a view:

```python
send_welcome_email.send(str(user.id))
```

Start the worker:

```bash
make worker-dev   # development (with auto-reload)
```

> **Broker:** Dramatiq uses Redis as the message broker (same Redis instance as the cache, on a dedicated DB index).
