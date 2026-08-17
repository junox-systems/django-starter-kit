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

# Terminal 3 — Celery worker (auto-reload)
make worker-dev
```

---

## Settings & Environment

Settings are split by environment. Select the active file via `DJANGO_SETTINGS_MODULE`:

| Value | Use |
|-------|-----|
| `config.settings.dev` | Local development (default in `manage.py` and `asgi.py`; logs warning if `ENVIRONMENT=production`) |
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

Two complementary layers — no overlap:

| Layer | Tool | Use case |
|-------|------|----------|
| Controller glue | **Stimulus 3** | Mounting Svelte components, minor DOM behaviour |
| Interactive islands | **Svelte 5** | Complex client-side UI with state (calls the API) |
| Animations | **GSAP 3** | Transitions, entrance/exit effects |

**Standard Django forms + full page loads handle the rest.** If a page section needs Svelte, mount it via a Stimulus controller. If it's a simple form, let Django handle it.

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

### Mounting a Svelte Component (Generic Bridge)

Use the built-in `svelte-bridge` controller for most cases:

```html
<div data-controller="svelte-bridge"
     data-svelte-bridge-component-value="YourComponent"
     data-svelte-bridge-props-value='{"key": "value"}'>
</div>
```

The bridge dynamically imports `frontend/src/js/svelte/YourComponent.svelte`, mounts it with the given props, and unmounts on disconnect. The component value is a
path relative to `frontend/src/js/svelte/` without the extension, so nested
components work too (e.g. `dashboard/Dashboard`).

#### Passing server data

Inline `props-value` is fine for hand-written constants. For anything coming out
of a Django view, use `json_script` and point the bridge at it by id — Django
escapes it safely and you avoid attribute-quoting bugs:

```html
{{ payload|json_script:"my-island-data" }}
<div data-controller="svelte-bridge"
     data-svelte-bridge-component-value="dashboard/Dashboard"
     data-svelte-bridge-props-id-value="my-island-data">
</div>
```

Props are read once at mount and are not reactive — the bridge has no
`propsValueChanged` hook. Components that need live data should fetch it
themselves (see `apps/dashboard/` for the pattern).

> **Tailwind and `.svelte`:** classes used only inside Svelte components survive
> the production build solely because `frontend/src/css/styles.css` declares
> `@source "../js/**/*.svelte";`. Keep it.

### Per-Component Pattern (Alternative)

For controllers that need additional logic beyond mount/unmount, create a dedicated Stimulus controller:

```javascript
// frontend/src/js/controllers/my-island.js
import { Controller } from "@hotwired/stimulus";
import { mount, unmount } from "svelte";
import MyComponent from "../svelte/MyComponent.svelte";

export default class extends Controller {
  connect() {
    this.component = mount(MyComponent, { target: this.element });
  }
  disconnect() {
    if (this.component) unmount(this.component);
  }
}
```

Note this imports the component statically, so it ships in the main bundle
rather than a lazy chunk. Prefer `svelte-bridge` unless you need the extra
lifecycle control.

See `frontend/src/js/controllers/svelte-bridge.js` for the generic
implementation, and `frontend/src/js/controllers/sidebar.js` for a controller
that drives Basecoat CSS via attributes.

---

## Database Conventions

- All new models inherit from `BaseModel`.
- Use `select_related` (FK/one-to-one) and `prefetch_related` (M2M/reverse relations) in querysets to prevent N+1 problems.
- Django Debug Toolbar is available in development at `/__debug__/`.

---

## Observability

### Sentry

Initialises automatically if `SENTRY_DSN` is set. Features:

- Error tracking across Django + Celery
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

## Task Queue (Celery)

Background tasks are defined with the `@shared_task` decorator:

```python
# apps/myapp/tasks.py
from celery import shared_task

@shared_task
def send_welcome_email(user_id: str):
    # runs asynchronously in the worker process
    ...
```

Enqueue from a view:

```python
send_welcome_email.delay(str(user.id))
```

Start the worker:

```bash
make worker-dev   # development (with auto-reload)
```

> **Broker:** Celery uses Redis as the message broker (same Redis instance as the cache, on a dedicated DB index). Results persist to the DB (`django-celery-results`); periodic tasks via `django-celery-beat` (DatabaseScheduler). Monitor workers/tasks/queues in the admin at `/admin/dj-celery-panel/`.
