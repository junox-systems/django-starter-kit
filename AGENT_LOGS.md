# Agent Logs

This file documents the implementation history of the Django 5.2 LTS Starter Kit.

---

## v0.1.0 — Initial Implementation

### Project Setup

- Initialized a new Django project with `apps`, `config`, `frontend`, and `templates` directories.
- Configured `django-environ` to manage environment variables via `.env`.
- Set up settings split: `base.py`, `dev.py`, `production.py`, `test.py` — selected via `DJANGO_SETTINGS_MODULE`.

### Dependencies

Initial set included: `django`, `djangorestframework`, `django-environ`, `django-allauth`, `django-vite`, `django-imagekit`, `django-storages`, `django-anymail`, `django-actioncable`, `django-cors-headers`, `django-redis`, `whitenoise`, `dramatiq`, `ruff`, `sentry-sdk`, `opentelemetry-sdk`, `pytest`, `psycopg`, `pillow`, `boto3`.

### Backend

- Configured PostgreSQL with psycopg v3.
- Implemented custom `SearchManager` in `apps/core/search.py` for ParadeDB BM25 search.
- Added placeholder analytics in `apps/core/analytics.py`.
- Redis cache backend via `django-redis`.
- Dramatiq + Redis (as the message broker) for background tasks.
- `django-anymail` (Postmark) for transactional email.
- `django-storages` (S3) for file storage.
- Sentry + OpenTelemetry for observability.
- Abstract base models: `BaseModel` (UUID + timestamps) and `SoftDeleteModel` (soft delete).

### Models

- `User` model with email login, OIDC fields (`oidc_subject`, `oidc_issuer`), `is_verified`, `deactivated_at`, `profile_completed`.
- `UserProfile` OneToOne model with bio, birth date, encrypted phone number, location, privacy settings, GDPR consent fields, avatar + imagekit thumbnail.
- `UserAuditLog` for tracking sensitive account operations.
- Custom HKDF/Fernet encryption in `apps/users/utils.py`.
- Auto-create UserProfile via `post_save` signal.

### API

- `api` app with DRF `UserViewSet` and `UserSerializer`.

### Authentication

- `django-allauth` with OIDC, Google, Apple, Microsoft providers.
- `allauth.urls` for registration, login/logout, password reset.

### Frontend

- Vite build process with `vite.config.js` and `package.json`.
- Hotwire: `@hotwired/turbo` + `@hotwired/stimulus`.
- Tailwind CSS v4 + DaisyUI v5.
- GSAP 3 for animations.
- Svelte 5 components mounted via Stimulus controllers.
- `django-turbo-helper` middleware and template tags.

### Templates

- Base template structure: `base.html`, `_header.html`, `_footer.html`.
- Allauth account templates: `login.html`, `logout.html`, `signup.html`, `password_reset.html`.

### CI/CD

- GitHub Actions pipeline (lint + test + docker build).
- `Makefile` for standardised commands.

### Containerization

- `docker-compose.yml` (root) — production stack.
- `dev/docker-compose.dev.yml` — development stack with ParadeDB, Redis/Valkey, MinIO.
- `dev/Dockerfile` — AlmaLinux 10 dev image with `mise`, `uv`, `pnpm` (Node 24), `supervisord`.
- `dev/supervisord.conf` — manages Django, Vite, and Dramatiq worker processes.

### OpenTelemetry

- Full instrumentation suite: Django, psycopg, Redis, requests, logging, system metrics, asyncio, threading, urllib, urllib3.
- `config/otel.py` initialised from `asgi.py` when `OTEL_ENABLED=true`.
- `OPENTELEMETRY.md` with SigNoz setup guide.

---

## v0.2.0 — Architecture Refactor (Simplify & Harden)

### Goal

Strip over-engineering. Let mature packages handle what they're built for. Remove anything that reimplements existing package functionality or doesn't belong in a starter kit.

### Dependencies Changed

**Removed (21 packages):**
- `dj-database-url` — `django-environ`'s `env.db()` covers this.
- `django-turbo-helper` — Turbo replaced by htmx.
- `django-actioncable` — Rails port; removed. Channels boilerplate kept for native WebSockets.
- `pyjwt` — Not used; allauth manages tokens.
- `cryptography` — Only used by deleted field encryption utils.
- 16× excess OpenTelemetry instrumentation packages (grpc, pika, boto3sqs, botocore, click, jinja2, sqlite3, asyncio, threading, logging, system-metrics, requests, urllib, urllib3, asgi, distro).

**Added (3 packages):**
- `django-auditlog` — Replaces hand-rolled `UserAuditLog` model.
- `django-cacheops` — Declarative ORM caching backed by Redis.
- `django-htmx` — Middleware for htmx request detection (`request.htmx`).

**Net: ~52 → ~30 dependencies.**

### Settings

- `config/settings/__init__.py` — Removed env-routing logic. Now a 3-line comment. Use `DJANGO_SETTINGS_MODULE` directly.
- `config/settings/base.py`:
  - Removed `dj-database-url`; use `env.db("DATABASE_URL")` + explicit `CONN_MAX_AGE`/`CONN_HEALTH_CHECKS`.
  - Sentry: conditional init (only if `SENTRY_DSN` is set), `traces_sample_rate=0.1`, `send_default_pii=False`.
  - Removed `WSGI_APPLICATION` — ASGI only.
  - Swapped `turbo_helper` → `django_htmx` in `INSTALLED_APPS` and `MIDDLEWARE`.
  - Added `auditlog` + `cacheops` to `INSTALLED_APPS`.
  - Added `auditlog.middleware.AuditlogMiddleware` to `MIDDLEWARE`.
  - Added `CACHEOPS_REDIS`, `CACHEOPS_DEFAULTS`, `CACHEOPS`, `CACHEOPS_DEGRADE_ON_FAILURE` config.
- `config/settings/dev.py` — Removed Turbo-specific `ROOT_TAG_EXTRA_ATTRS` from debug toolbar.
- `config/settings/test.py` — Removed Sentry re-init hack; added `CACHEOPS_ENABLED=False`; updated middleware filter.
- `config/otel.py` — Trimmed from 10 instrumentors to 3 (Django, psycopg, Redis). All `print()` replaced with `logging`.
- `config/asgi.py` — Removed ActionCable. Removed 7 `print()` statements. Kept Channels `ProtocolTypeRouter` with empty `URLRouter` for future WebSocket routes.
- `manage.py` — Default `DJANGO_SETTINGS_MODULE` → `config.settings.dev`.

### Models

**Deleted files:**
- `apps/core/search.py` — Dead code. Used deprecated `.extra()`, was never attached to any model.
- `apps/core/analytics.py` — Empty stub (`pass`).
- `apps/users/utils.py` — 168 lines of HKDF/Fernet encryption for a single phone field.
- `apps/users/signals.py` — UserProfile auto-creation signal (no longer needed).

**`apps/core/models.py`:** Removed `SoftDeleteModel` and `SearchManager` import. Only `BaseModel` remains (19 lines).

**`apps/users/models.py`:** Rewrote from 779 → ~75 lines.
- Removed: `UserAuditLog`, `UserProfile`, all OIDC fields/methods, `is_verified`, `deactivated_at`, `profile_completed`, all GDPR methods (anonymize, export, consent), manual cache-aside pattern, redundant `clean()` overrides, field encryption.
- Kept: `User(AbstractUser, BaseModel)` with email login, `avatar` + `avatar_thumbnail` (imagekit).
- Added: `auditlog.register(User)` for automatic change tracking.

**`apps/users/admin.py`:** Removed `UserAuditLogAdmin`, `UserProfileAdmin`. Added avatar to `UserAdmin`.

**`apps/users/apps.py`:** Removed signal import.

**`apps/api/views.py`:** Removed `select_related('profile')`.

**`apps/api/serializers.py`:** Removed `__init__` that mutated viewset queryset as a side effect.

### Migrations

- Deleted all 5 existing user migrations (referenced deleted models and functions).
- Generated clean `0001_initial.py` — single `CreateModel User` operation.

### Frontend

- `frontend/package.json`: Replaced `@hotwired/turbo` with `htmx.org`.
- `frontend/src/js/main.js`: Replaced Turbo import with htmx; `window.htmx = htmx` for global availability.
- `frontend/src/js/controllers/welcome-svelte.js`: Fixed Svelte 5 API — `unmount(component)` instead of `component.$destroy()`.

### Tests

- Deleted `apps/users/tests/test_utils.py` (encryption tests for deleted module).
- Rewrote `apps/users/tests/test_models.py` — 8 focused tests for the simplified User model.

### Verification

- `uv sync` — 21 uninstalled, 4 installed ✅
- `pytest -v` — 8/8 passed in 0.08s ✅
- `ruff check` — Clean (only pre-existing Django boilerplate unused imports) ✅
- `makemigrations --dry-run` — No changes detected ✅

### Deferred

- DRF → DMR (django-modern-rest) replacement — separate task.
- CI workflow Makefile target alignment — separate task.
- Docker files — left as-is.
