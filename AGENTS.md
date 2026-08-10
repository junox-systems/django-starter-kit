# AGENTS.md — Django Starter Kit

## Identity

Modern Django 5.2 LTS starter kit. Opinionated, lean, production-ready.

## Tech Stack

- **Backend:** Django 5.2, Granian (ASGI), ParadeDB/PG17, Redis/Valkey, Celery (django-celery-results, django-celery-beat)
- **Auth:** django-allauth (OIDC/SSO, social, email-based login)
- **API:** django-modern-rest (DMR) 0.x — NOT DRF
- **Frontend:** Django forms (primary) → Stimulus 3 mounts Svelte 5 islands → GSAP animations
- **Styling:** Tailwind CSS v4 + Basecoat (shadcn-compatible tokens, per-site `site.css` style pack)
- **Build:** Vite, uv (Python), pnpm (JS)
- **Admin:** stock Django admin (with dj-control-room dashboard: redis, cache, urls, celery, signals panels; guardian, constance, import_export, simple_history)
- **Observability:** Sentry (opt-in), OpenTelemetry (opt-in)
- **Tooling:** ruff (lint/format), pytest, django-debug-toolbar

## Project Structure

```
apps/           # Django apps
  core/         # BaseModel (UUID v7 PK + timestamps) — keep lean
  users/        # Custom User model (email login, UUID PK, avatar)
  api/          # API endpoints (DMR)
  pages/        # Static/marketing pages
config/         # Django project config
  settings/     # base.py + dev.py + production.py + test.py
  asgi.py       # Channels boilerplate + OTEL init
  otel.py       # OpenTelemetry (opt-in)
frontend/       # JS/CSS assets
  src/js/
    controllers/  # Stimulus controllers (auto-registered via import.meta.glob)
    svelte/       # Svelte 5 components (lazy-loaded)
templates/      # Django templates
```

## Conventions & Rules

### Django Apps
- Every app gets `__init__.py`, `apps.py`, `models.py`, `admin.py`, `views.py`, `tests/`
- Apps live under `apps/` — never at project root
- `apps/core` stays lean — only truly universal abstractions. Extract domains to own apps.

### Models
- All models inherit from `apps.core.models.BaseModel` (UUID v7 PK, created_at, updated_at)
- `User` model is email-based (`USERNAME_FIELD = "email"`), UUID PK
- Register models with `auditlog.register(Model)` for change tracking
- Never add OIDC/social auth fields to User model — allauth stores in SocialAccount

### Settings
- Selected via `DJANGO_SETTINGS_MODULE` env var — no routing in `__init__.py`
- `base.py` → shared, `dev.py` → local, `production.py` → prod, `test.py` → CI
- `production.py` inherits from base via `from .base import *`
- SSL/HSTS left commented — enable manually per deployment topology

### Frontend
- **Primary: Django forms + full page loads** — simple interactions
- **Islands: Stimulus mounts Svelte 5** — complex client-side UI
  - Use generic `svelte-bridge` controller for most Svelte components:
    `<div data-controller="svelte-bridge" data-svelte-bridge-component-value="Name">`
  - Svelte files in `frontend/src/js/svelte/`, lazy-loaded via dynamic import
- **Animations: GSAP 3** — transitions in controllers or Svelte components
- **No htmx** — removed. Use Django forms or Svelte islands.
- Controllers auto-registered from `frontend/src/js/controllers/` — filename `foo-bar.js` → `data-controller="foo-bar"`

### API (DMR)
- Controllers in `apps/api/views.py`, schemas in `apps/api/schemas/`
- Use `dmr.Controller` with `MsgspecSerializer`
- Response validation ON in dev, OFF in production (set in production.py)

## Critical Rules

1. **Never change settings inheritance pattern** — base/dev/production/test split with `from .base import *`
2. **Never add OIDC fields to User model** — allauth SocialAccount handles it
3. **Never add htmx back** — removed by design
4. **Never create new files outside apps/ for backend code** — everything goes in apps/
5. **Never tune cacheops/auditlog for hypothetical scale** — starter kit, YAGNI
6. **Never auto-enable SSL/HSTS** — must be manual per deployment

## Dependency Management

- Python: `uv add <pkg>` / `uv sync`
- JS: `cd frontend && pnpm add <pkg>`
- Python min: 3.14

## Testing

- `make test` — runs pytest with `DJANGO_SETTINGS_MODULE=config.settings.test`
- Write tests per app in `apps/<name>/tests/`
