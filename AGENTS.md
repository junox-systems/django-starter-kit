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
  dashboard/    # Authenticated home at /dashboard/ — panel payloads, no models
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
  - Server data goes in via `{{ payload|json_script:"id" }}` +
    `data-svelte-bridge-props-id-value="id"`. Never hand-build JSON into
    `props-value` from template variables — quoting breaks and it is an XSS hazard.
- **Animations: GSAP 3** — transitions in controllers or Svelte components
- **No htmx** — removed by design. `django-htmx` is gone from dependencies,
  `INSTALLED_APPS` and `MIDDLEWARE`. Turbo Drive replaces it for navigation.
- Controllers auto-registered from `frontend/src/js/controllers/` — filename `foo-bar.js` → `data-controller="foo-bar"`
- **Tailwind must be told about `.svelte`.** `frontend/src/css/styles.css` has
  `@source "../js/**/*.svelte";`. Remove it and every class used only inside a
  Svelte component is purged from the production CSS — dev looks fine, prod is
  unstyled, with no warning. Verify after `pnpm run build` by grepping
  `dist/assets/main-*.css` for a Svelte-only class.

### Turbo Drive
- **Scoped to the app shell, not global.** `main.js` sets
  `Turbo.config.drive.enabled = false`; `base_app.html` opts in with
  `data-turbo="true"` on the shell wrapper. Marketing pages and allauth flows
  keep plain page loads. Opt a single link out with `data-turbo="false"`.
- **Forms are browser-native:** `Turbo.config.forms.mode = "off"`. Django
  re-renders an invalid form as HTTP 200, which Turbo Drive rejects. Do not turn
  this on without giving every form a redirect-or-422 response.
- `{% comment %}` blocks, not multi-line `{# #}` (single-line only in Django) —
  a leaked comment closes `<head>` early and pushes the CSS into `<body>`.

### Layouts
- `templates/base.html` — public pages. Blocks: `title`, `extra_head`, `header`,
  `body`, `content`, `footer`, `extra_body`. Also holds the inline pre-paint
  script (theme + transition suppression) — keep it a plain blocking script.
- `templates/base_app.html` — **all authenticated pages.** Holds the app bar and
  mounts the sidebar island; overrides `header`/`footer` to drop the marketing
  chrome. Pages set `{% block page_title %}` for the bar heading.
- **Sidebar is `svelte/app/Sidebar.svelte`**, mounted into the `.sidebar` element
  and marked `data-turbo-permanent`, so it is created once and carried between
  Turbo visits. Because it never re-renders from server HTML it derives the
  active item from `location.pathname` on `turbo:load`. Links come from
  `apps/dashboard/context_processors.py::app_nav` — resolve URLs there with
  `reverse()`, never hardcode paths in JS, and pass icon *names* not SVG markup.
- Markup follows Basecoat's `.sidebar` contract; the CSS already exists in
  `site.css`. **Write no sidebar CSS.** The mount element carries `.sidebar`, and
  the content wrapper must stay its immediate next sibling — `.sidebar + *` is
  what applies the content margin.
- `svelte-bridge` adopts an existing instance on a `data-turbo-permanent`
  element instead of remounting, and defers teardown a tick to tell "Turbo is
  relocating this" from "this is really gone". Don't remove that, or the sidebar
  blinks on every visit (or leaks listeners).

### Dashboard panels
The dashboard is one Svelte root (`svelte/dashboard/Dashboard.svelte`) composing
child panels. The root owns layout and any cross-panel state; children get props
and callbacks — never their own stores or context.

To add a panel:
1. Add `<name>_payload(user) -> dict` to `apps/dashboard/panels.py`. JSON-safe
   primitives only.
2. Add its key to `DashboardView.get_context_data`'s `payload` dict.
3. Add `frontend/src/js/svelte/dashboard/<Name>.svelte`, wrapping content in
   `<Panel>`. Use runes (`$props`, `$state`, `$derived`).
4. Render it in `Dashboard.svelte`'s grid, passing its slice.

Rules:
- Panels get data as **props and do not fetch on mount** — no spinners, no
  empty-state flash. Add a DMR endpoint only for genuinely live refresh, and
  have it call the same `*_payload` function so the shape cannot drift.
- Refresh calls are GET, so no CSRF token is needed. **A panel that POSTs must
  solve CSRF exposure first — nothing hands a token to JS yet.**
- Never put audited *values* in a payload. `LogEntry.changes` carries password
  hashes; `activity_payload` deliberately reports field names only.
- Empty states are the default on a fresh install (auditlog only tracks
  registered models), so build them as real states.

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
