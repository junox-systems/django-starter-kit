# AGENTS.md — Django Starter Kit

## Identity

Modern Django 5.2 LTS starter kit. Opinionated, lean, production-ready.

## Tech Stack

- **Backend:** Django 5.2, Granian (ASGI), ParadeDB/PG17, Redis/Valkey, Celery (django-celery-results, django-celery-beat)
- **Auth:** django-allauth (OIDC/SSO, social, email-based login)
- **API:** django-modern-rest (DMR) 0.x — NOT DRF
- **Frontend:** Django templates + forms (primary) → Turbo Drive inside the app shell → Stimulus 3 mounts Svelte 5 islands → GSAP animations. See **Frontend Formula** below before touching `templates/` or `frontend/src/js/`.
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
  src/css/
    styles.css    # entry: Tailwind + Basecoat base + @source globs
    site.css      # per-site Basecoat style pack — all component visuals
  src/js/
    main.js       # entry: Turbo config, Stimulus boot, controller auto-register
    controllers/  # Stimulus controllers (auto-registered via import.meta.glob)
    svelte/
      app/        # shell islands (Sidebar)
      dashboard/  # dashboard root + panels
templates/
  base.html       # public pages
  base_app.html   # authenticated app shell (Turbo-enabled)
  _*.html         # shared partials (header, footer, messages)
  <app>/          # per-app pages
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

## Frontend Formula

Django renders pages. Svelte renders the interactive parts of a page. Stimulus is
the only thing allowed to connect them. Read this section before touching
anything under `templates/` or `frontend/src/js/`.

### Who owns what

Each layer has exactly one job. If you find yourself doing another layer's job,
you are in the wrong file.

| Layer | Owns | Never does |
|---|---|---|
| **Django view** | Fetching + authorizing data, shaping it into JSON-safe primitives | Render HTML meant for an island; leak model objects into payloads |
| **Django template** | Page structure, chrome, layout, **every URL**, mount points, `json_script` payloads | Contain client state or business logic |
| **Stimulus controller** | DOM lifecycle, browser APIs (`matchMedia`, `localStorage`, document listeners), mounting islands | Render UI, hold app state |
| **Svelte component** | Interactive UI + client state | Resolve URLs, render nav/chrome, fetch on mount |
| **Basecoat CSS** | All visual styling, via `site.css` | — you write no component CSS |
| **DMR (`apps/api`)** | Refresh + mutation endpoints | Duplicate the view's data shaping |

**URLs are a Django responsibility, always.** Resolve with `reverse()` or
`{% url %}` and pass them down as data. A hardcoded path in a `.svelte` file is a
bug.

### Choose the lightest layer that works

Stop at the first rung that holds:

1. **Static content** → Django template only. No JS.
2. **A form** → Django form + full page load. This is the default for all input.
3. **DOM behavior, no state** (toggle, drawer, keyboard handler, browser API)
   → Stimulus controller. See `controllers/sidebar.js`, `controllers/theme-toggle.js`.
4. **Reactive UI with client state** → Svelte island via `svelte-bridge`.
5. **Must survive navigation** (persistent chrome) → Svelte island +
   `data-turbo-permanent` + a unique `id`. See `svelte/app/Sidebar.svelte`.

Rung 4 is not a reward for complexity — an island costs a chunk, a mount, and a
data contract. Rungs 1–3 are free.

### Data flow

One direction, one shape. The server owns the shape; the client never invents it.

```
view.get_context_data()          →  dict of primitives (no model objects, no datetimes-as-objects)
  ↓ {{ payload|json_script:"x" }}
template                         →  <script type="application/json" id="x">
  ↓ data-svelte-bridge-props-id-value="x"
svelte-bridge (Stimulus)         →  JSON.parse, mount()
  ↓
Component                        →  let { ... } = $props()
```

For live refresh, the island fetches a DMR endpoint that calls **the same payload
function** as the view, so the two shapes cannot drift:

```
Component  →  fetch(urls.thing, {credentials: "same-origin"})  →  DMR controller  →  thing_payload(user)
                                                                       ↑
view.get_context_data() ───────────────────────────────────────────────┘
```

Pass endpoint URLs into the payload (`"urls": {"thing": reverse("thing")}`) rather
than hardcoding them client-side.

**Props are read once at mount and are not reactive.** `svelte-bridge` has no
`propsValueChanged` hook. Anything that must change after mount is either client
state (`$state`) or a fetch.

### Where things go

| What | Where |
|---|---|
| Data shaping (one function per unit) | `apps/<app>/panels.py` |
| Cross-page shell data | `apps/<app>/context_processors.py` (register in `TEMPLATES`) |
| Routes | `apps/<app>/urls.py`, no `app_name` — this project uses the root namespace |
| Page structure | `templates/<app>/<page>.html` |
| Shared chrome | `templates/base.html`, `templates/base_app.html`, `templates/_*.html` |
| Stimulus controller | `frontend/src/js/controllers/<name>.js` → `data-controller="<name>"` |
| Svelte component | `frontend/src/js/svelte/<area>/<Name>.svelte` |
| API endpoint + schema | `apps/api/views.py`, `apps/api/schemas/<name>.py` |

Controllers auto-register from the `controllers/` glob: `foo-bar.js` →
`data-controller="foo-bar"`; `admin/table.js` → `data-controller="admin--table"`.
Component values are paths relative to `svelte/` without the extension, so
`svelte/app/Sidebar.svelte` is `data-svelte-bridge-component-value="app/Sidebar"`.

### Layouts

- `templates/base.html` — public pages. Blocks: `title`, `extra_head`, `header`,
  `body`, `content`, `footer`, `extra_body`. Holds the pre-paint inline script
  (theme + transition suppression) — **keep it a plain blocking `<script>`**;
  `main.js` is a deferred module and runs after first paint.
- `templates/base_app.html` — **every authenticated page.** App bar + sidebar
  mount; overrides `header`/`footer` to drop marketing chrome. Pages set
  `{% block page_title %}`.
- Public pages extend `base.html`; logged-in pages extend `base_app.html`. Adding
  an authenticated route means extending `base_app.html`, nothing else.

### Turbo Drive

- **Scoped to the app shell, not global.** `main.js` sets
  `Turbo.config.drive.enabled = false`; `base_app.html` opts in with
  `data-turbo="true"`. Marketing and allauth pages keep plain loads. Opt one link
  out with `data-turbo="false"`.
- **Forms are browser-native:** `Turbo.config.forms.mode = "off"`. Django
  re-renders an invalid form as HTTP 200, which Turbo Drive rejects. Do not enable
  form handling without giving every form a redirect-or-422 response.
- A persistent island needs a unique `id` + `data-turbo-permanent`. `svelte-bridge`
  then **adopts** the existing instance instead of remounting, and defers teardown
  one tick to tell "Turbo is relocating this" from "this is gone". Remove that and
  the island blinks on every visit, or leaks its listeners.
- A permanent island cannot re-render from server HTML, so anything page-dependent
  (active nav state) must derive from `location.pathname` on `turbo:load`.

### Adding an interactive unit — the recipe

1. **Shape the data.** Add `<name>_payload(user) -> dict` to `apps/<app>/panels.py`.
   JSON-safe primitives only.
2. **Expose it.** Add the key to the view's `payload` dict in `get_context_data`.
3. **Render the mount.** In the template: `{{ payload|json_script:"<id>" }}` plus a
   mount element with `data-controller="svelte-bridge"`, the component value, and
   `data-svelte-bridge-props-id-value="<id>"`.
4. **Build the component.** `frontend/src/js/svelte/<area>/<Name>.svelte`, runes
   only (`$props`, `$state`, `$derived`). Reuse `dashboard/Panel.svelte` for card
   chrome.
5. **Only if it needs live refresh:** add a DMR controller that calls the same
   `*_payload` function, and pass its URL through the payload.
6. **Verify.** `make test`, then `cd frontend && pnpm run build`, then load the page
   and check the console. A `svelte-bridge: no component found` error means the
   component value path is wrong.

Dashboard specifics: `svelte/dashboard/Dashboard.svelte` is one root composing
child panels. The root owns layout and cross-panel state; children get props and
callbacks, **never their own stores or context**. Add a panel by rendering it in
the root's grid with its slice.

### Hard rules

Each of these has already caused a real bug in this repo.

1. The `.svelte` line in `@source` globs, in `frontend/src/css/styles.css`, **must
   stay.** Without it, classes used only inside a component are purged from production
   CSS — dev looks perfect, prod is unstyled, with no warning. Verify after a
   build by grepping `dist/assets/main-*.css` for a Svelte-only class.
2. **Django's `{# #}` is single-line only.** A multi-line one leaks as text, which
   closes `<head>` early and pushes the CSS into `<body>`. Use `{% comment %}`
   for multi-line — and `{% extends %}` must be the file's first tag.
3. **Never hand-build JSON into an HTML attribute.** Autoescaping produces
   `&quot;`, an apostrophe in the data breaks the quoting, and it is an injection
   vector. Use `json_script`.
4. **Never put secrets or raw audit values in a payload.** `LogEntry.changes`
   carries password hashes; `activity_payload` reports field *names* only.
5. **Islands fetch GET only.** Nothing exposes a CSRF token to JS yet, so a POST
   from an island requires solving that first.
6. **Pass icon names, not markup, through JSON.** Components map names to markup
   from a closed constant table.
7. **Anything that must apply before first paint is a blocking inline script** in
   `base.html`, never a Stimulus controller.
8. **Write no component CSS.** Basecoat's `site.css` already styles `.card`,
   `.sidebar`, `.alert`, `.empty`, `.btn`, `.field`, and the rest via
   class + `data-*` variants (`class="btn" data-variant="outline" data-size="sm"`).
   Respect its structural contracts — e.g. `.sidebar + *` applies the content
   margin, so the content wrapper must stay the sidebar's immediate next sibling.
9. **No htmx.** Removed by design; gone from dependencies, `INSTALLED_APPS`, and
   `MIDDLEWARE`. Turbo Drive covers navigation.
10. **Empty states are the default view** on a fresh install, not an edge case.
    Build them as real states.

### Smells

- A `fetch` in a component that could have been a prop → move it to the view.
- A hardcoded `/path/` in a `.svelte` file → resolve it in Django.
- A new `.css` file, or a `<style>` block reimplementing Basecoat → delete it.
- A Svelte component rendering navigation or page chrome → that is Django's job.
- Two payload shapes for the same data (view + API) → share one function.
- A store or `setContext` to talk between islands → give one root the state, or
  ask whether they should be one island.

## API (DMR)
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
7. **Never let Svelte own URLs, navigation, or page chrome** — Django resolves
   URLs and renders structure; islands receive data. See **Frontend Formula**.
8. **Never enable Turbo form handling** without giving every form a
   redirect-or-422 response — Django returns HTTP 200 on invalid forms.

## Dependency Management

- Python: `uv add <pkg>` / `uv sync`
- JS: `cd frontend && pnpm add <pkg>`
- Python min: 3.14

## Testing

- `make test` — runs pytest with `DJANGO_SETTINGS_MODULE=config.settings.test`
- Write tests per app in `apps/<name>/tests/`
