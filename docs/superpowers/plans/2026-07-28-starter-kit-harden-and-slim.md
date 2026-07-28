# Harden & Slim Implementation Plan

> **For agentic workers:** Sub-tasks use checkbox (`- [ ]`) syntax for tracking. Each task is independent and commit-worthy.

**Goal:** Fix production-blocking issues, remove htmx, add generic Stimulus+Svelte bridge, update README.

**Architecture:** Settings hardening (env guards, security headers, S3 config warnings), frontend simplification (htmx removal, generic Svelte mounting controller), documentation update.

**Tech Stack:** Dockerfile, Django settings, Stimulus 3, Svelte 5, Vite, Makefile.

## Global Constraints

- Dockerfile must match `pyproject.toml` `requires-python = ">=3.14"`
- htmx removal must not break existing templates (confirmed: none use htmx)
- Stimulus controller must use dynamic import for Svelte components
- No new Python dependencies
- Every task commits independently

---

## File Structure

| File | Action | Responsible Task |
|------|--------|------------------|
| `Dockerfile` | Modify (line 3) | Task 1 |
| `config/asgi.py` | Modify (add warning guard) | Task 2 |
| `Makefile` | Modify (prod-start env) | Task 2 |
| `config/settings/production.py` | Modify (DMR_SETTINGS, SSL comments) | Task 3 |
| `config/settings/base.py` | Modify (S3 warning, regex, CONN_MAX_AGE) | Task 4 |
| `apps/users/models.py` | Modify (add comments) | Task 5 |
| `frontend/package.json` | Modify (remove htmx) | Task 6 |
| `frontend/src/js/main.js` | Modify (remove htmx import) | Task 6 |
| `frontend/src/js/controllers/svelte-bridge.js` | Create (generic bridge) | Task 7 |
| `frontend/src/js/controllers/welcome-svelte.js` | Modify (add bridge note) | Task 7 |
| `README.md` | Rewrite | Task 8 |

---

### Task 1: Fix Dockerfile Python version

**Files:**
- Modify: `Dockerfile:3`

**Interfaces:**
- Consumes: nothing
- Produces: working Docker build on Python 3.14

- [ ] **Step 1: Change base image**

In `Dockerfile`, change `FROM python:3.12-slim` to `FROM python:3.14-slim`:

```diff
- FROM python:3.12-slim
+ FROM python:3.14-slim
```

- [ ] **Step 2: Verify**

```bash
docker build --no-cache -t django-starter-kit-test .
```
Expected: Build succeeds, Python 3.14 reported.

- [ ] **Step 3: Commit**

```bash
git add Dockerfile
git commit -m "fix: update Dockerfile to python:3.14-slim"
```

---

### Task 2: Settings safety — asgi.py + Makefile

**Files:**
- Modify: `config/asgi.py` (after line 20, add warning guard)
- Modify: `Makefile` (line 120, add DJANGO_SETTINGS_MODULE)

**Interfaces:**
- Consumes: nothing
- Produces: warning log when dev settings used in production context

- [ ] **Step 1: Add warning guard to asgi.py**

After `os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")` in `config/asgi.py`, add:

```python
# Warn if production environment but settings still at dev default
if (
    os.environ.get("ENVIRONMENT") == "production"
    and "config.settings.dev" in os.environ.get("DJANGO_SETTINGS_MODULE", "")
):
    logger.warning(
        "DJANGO_SETTINGS_MODULE is '%s' but ENVIRONMENT=production. "
        "Set DJANGO_SETTINGS_MODULE=config.settings.production explicitly.",
        os.environ["DJANGO_SETTINGS_MODULE"],
    )
```

- [ ] **Step 2: Fix Makefile prod-start**

In `Makefile` line ~119-127, change the `prod-start` target:

```diff
 prod-start:
-	env ENVIRONMENT=production uv run granian \
+	env DJANGO_SETTINGS_MODULE=config.settings.production ENVIRONMENT=production uv run granian \
```

- [ ] **Step 3: Verify**

```bash
python -c "import config.asgi"  # should not error
```

- [ ] **Step 4: Commit**

```bash
git add config/asgi.py Makefile
git commit -m "fix: add settings guard in asgi.py and fix Makefile prod-start"
```

---

### Task 3: Production settings cleanup

**Files:**
- Modify: `config/settings/production.py`

**Interfaces:**
- Consumes: base.py settings
- Produces: clean production settings without DMR_SETTINGS duplication

- [ ] **Step 1: Fix DMR_SETTINGS override**

Replace the current full re-declaration in `config/settings/production.py`:

```diff
  from .base import *  # noqa: F403
- from .base import env, DMR_SETTINGS
+ from .base import env

  from dmr.settings import Settings
+ from dmr.openapi import OpenAPIConfig

- # Disable DMR response validation in production for performance.
- # Docs: "Keep it on in development, but disable it in production
- # to get the best of both worlds."
- DMR_SETTINGS = {
-     **DMR_SETTINGS,
-     Settings.validate_responses: False,
- }

+ # Performance: disable response validation in production.
+ DMR_SETTINGS.update({Settings.validate_responses: False})
```

- [ ] **Step 2: Add SSL/HSTS documentation comment**

After the security settings block (after `CSRF_COOKIE_SECURE = True`), add:

```python
# SSL/HSTS: Enable these when your reverse proxy terminates TLS and sets
# SECURE_PROXY_SSL_HEADER. Do NOT enable without the proxy header —
# it causes infinite redirect loops.
# SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
# SECURE_SSL_REDIRECT = True
# SECURE_HSTS_SECONDS = 31536000  # 1 year
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# SECURE_HSTS_PRELOAD = True
```

- [ ] **Step 3: Verify**

```bash
python -c "from config.settings.production import *; print(DMR_SETTINGS)"
```
Expected: No import error, validate_responses is False.

- [ ] **Step 4: Commit**

```bash
git add config/settings/production.py
git commit -m "fix: clean DMR_SETTINGS override, document SSL/HSTS setup"
```

---

### Task 4: Base settings fixes

**Files:**
- Modify: `config/settings/base.py`

**Interfaces:**
- Consumes: nothing
- Produces: S3 warning log, fixed regex, CONN_MAX_AGE comment

- [ ] **Step 1: Add S3 partial config warning**

After the S3 storage conditional block (around line 233-234), add:

```python
# Warn if S3 config is partial
if bool(AWS_ACCESS_KEY_ID) + bool(AWS_SECRET_ACCESS_KEY) + bool(AWS_STORAGE_BUCKET_NAME) in (1, 2):
    logger.warning(
        "Partial S3 configuration detected (%d of 3 vars set). "
        "Falling back to local filesystem storage.",
        bool(AWS_ACCESS_KEY_ID) + bool(AWS_SECRET_ACCESS_KEY) + bool(AWS_STORAGE_BUCKET_NAME),
    )
```

- [ ] **Step 2: Widen immutable_file_test regex**

Change the regex in `immutable_file_test`:

```diff
- return re.match(r"^.+[.-][0-9a-zA-Z_-]{8,12}\..+$", url)
+ return re.match(r"^.+[.-][0-9a-zA-Z_-]{8,}\..+$", url)
```

- [ ] **Step 3: Add CONN_MAX_AGE strategy comment**

After `DATABASES["default"]["CONN_HEALTH_CHECKS"] = True`, add:

```python
# Use max_lifetime strategy for psycopg 3 connection recycling:
# DATABASES["default"]["CONN_MAX_AGE_STRATEGY"] = "max_lifetime"
```

- [ ] **Step 4: Verify**

```bash
python -c "from config.settings.base import *; print('OK')"
```
Expected: No errors.

- [ ] **Step 5: Commit**

```bash
git add config/settings/base.py
git commit -m "fix: add S3 partial config warning, widen hash regex, document CONN_MAX_AGE"
```

---

### Task 5: User model documentation comments

**Files:**
- Modify: `apps/users/models.py`

**Interfaces:**
- Consumes: nothing
- Produces: clearer intent in User model

- [ ] **Step 1: Add comment for username REQUIRED_FIELDS**

After line 57 (`REQUIRED_FIELDS = ["username"]`), add:

```python
# username kept in REQUIRED_FIELDS for django-allauth signup compatibility.
# Removing it breaks allauth's default signup form.
```

- [ ] **Step 2: Add comment for email normalization**

After line 64 (`self.email = self.email.lower().strip()`), add:

```python
# NOTE: django-allauth also normalizes email. This is belt-and-suspenders.
```

- [ ] **Step 3: Commit**

```bash
git add apps/users/models.py
git commit -m "docs: document username/email normalization rationale in User model"
```

---

### Task 6: Remove htmx

**Files:**
- Modify: `frontend/package.json`
- Modify: `frontend/src/js/main.js`

**Interfaces:**
- Consumes: nothing
- Produces: htmx-free frontend bundle

- [ ] **Step 1: Remove htmx from package.json**

In `frontend/package.json`, remove the line:
```diff
-     "htmx.org": "^2.0.10",
```

- [ ] **Step 2: Remove htmx import from main.js**

In `frontend/src/js/main.js`, remove lines 10-12:
```diff
- // Import htmx
- import htmx from "htmx.org";
- window.htmx = htmx;
```

- [ ] **Step 3: Verify**

```bash
cd frontend && pnpm install && pnpm run build
```
Expected: No htmx references in output, build succeeds.

- [ ] **Step 4: Commit**

```bash
git add frontend/package.json frontend/src/js/main.js
git commit -m "feat: remove htmx — Django forms + Stimulus + Svelte islands replace it"
```

---

### Task 7: Generic Stimulus Svelte bridge

**Files:**
- Create: `frontend/src/js/controllers/svelte-bridge.js`
- Modify: `frontend/src/js/controllers/welcome-svelte.js`

**Interfaces:**
- Consumes: Svelte components in `frontend/src/js/svelte/`
- Produces: reusable `data-controller="svelte-bridge"` for templates

- [ ] **Step 1: Create svelte-bridge.js**

```javascript
import { Controller } from "@hotwired/stimulus";
import { mount, unmount } from "svelte";

export default class extends Controller {
  static values = {
    component: String,
    props: { type: Object, default: {} },
  };

  connect() {
    const name = this.componentValue;
    if (!name) return;

    import(`../svelte/${name}.svelte`)
      .then((mod) => {
        this.instance = mount(mod.default, {
          target: this.element,
          props: this.propsValue,
        });
      })
      .catch((err) => {
        console.error(`svelte-bridge: failed to load ${name}.svelte`, err);
      });
  }

  disconnect() {
    if (this.instance) {
      unmount(this.instance);
      this.instance = null;
    }
  }
}
```

- [ ] **Step 2: Update welcome-svelte.js with bridge reference**

Add a comment at the top of `frontend/src/js/controllers/welcome-svelte.js`:

```diff
+ // For new Svelte components, use the generic svelte-bridge controller instead:
+ // <div data-controller="svelte-bridge"
+ //      data-svelte-bridge-component-value="YourComponent"
+ //      data-svelte-bridge-props-value='{"key": "value"}'>
+ // </div>
```

- [ ] **Step 3: Verify**

```bash
cd frontend && pnpm run build
```
Expected: Build succeeds, svelte-bridge.js included in bundle.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/js/controllers/svelte-bridge.js frontend/src/js/controllers/welcome-svelte.js
git commit -m "feat: add generic Stimulus controller for Svelte mounting"
```

---

### Task 8: Update README

**Files:**
- Modify: `README.md`

**Interfaces:**
- Consumes: all changes from Tasks 1-7
- Produces: accurate, current project documentation

- [ ] **Step 1: Rewrite README.md**

Replace the README with:

```markdown
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
# Terminal 1 — Django (Granian ASGI, auto-reload)
make django-dev

# Terminal 2 — Frontend (Vite HMR)
make vite-dev

# Terminal 3 — Dramatiq worker
make worker-dev
```

---

## Frontend Architecture

**Primary rendering: Django templates + HTML forms.** Full page loads for standard interactions.

**Interactive islands: Stimulus mounts Svelte 5 components.** Use a generic bridge controller:

```html
<div data-controller="svelte-bridge"
     data-svelte-bridge-component-value="YourComponent"
     data-svelte-bridge-props-value='{"key": "value"}'>
</div>
```

Svelte components live in `frontend/src/js/svelte/` and are lazy-loaded via dynamic import. Only the components on the page are downloaded.

**Animations: GSAP 3** for transitions and micro-interactions in both Stimulus controllers and Svelte components.

---

## Production Checklist

Before deploying to production:

1. **Set environment variables:** `SECRET_KEY`, `DATABASE_URL`, `REDIS_URL`, `ENVIRONMENT=production`, `DJANGO_SETTINGS_MODULE=config.settings.production`
2. **Configure SSL/TLS:** See `config/settings/production.py` for commented SSL/HSTS settings. Enable these after configuring your reverse proxy to set `X-Forwarded-Proto`.
3. **Static files:** Run `make vite-build && python manage.py collectstatic --no-input`
4. **Database:** Run `python manage.py migrate`
5. **Sentry:** Set `SENTRY_DSN` for error tracking
6. **Email:** Set `POSTMARK_SERVER_TOKEN` (or swap `EMAIL_BACKEND` in settings)

### Known Caveats

| Caveat | Detail |
|--------|--------|
| **Python 3.14** | Bleeding-edge Python. Some packages may not have pre-built wheels. `uv` handles source builds. |
| **DMR (django-modern-rest) 0.x** | API framework is pre-1.0. Stable but may have breaking changes. Pin version in `pyproject.toml`. |
| **Granian** | Rust-based ASGI server. Mature but smaller ecosystem than Gunicorn+Uvicorn. |
| **Redis single-node** | Cache, sessions, Dramatiq broker, and Channels all share one Redis instance. Shard for high traffic. |

---

## Development

See [DEVELOPMENT.md](DEVELOPMENT.md) for in-depth guidance on settings, models, frontend workflow, and observability.
```

- [ ] **Step 2: Verify**

```bash
# Review reads cleanly
cat README.md | head -5
```

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: update README for harden-and-slim changes"
```

---

## Self-Review Checklist

- [ ] Every spec requirement maps to at least one task
- [ ] No TODOs, TBDs, or placeholders
- [ ] All file paths are exact
- [ ] All code blocks are complete
- [ ] Task boundaries produce independently reviewable commits
