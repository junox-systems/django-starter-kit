# Starter Kit: Harden & Slim

**Date:** 2026-07-28
**Status:** Draft (per user instructions — approved in conversation, written for record)

## Rationale

The Django starter kit has architectural soundness but ships with several production-blocking issues and a frontend stack heavier than needed for its "HTML-first, interactive islands" philosophy. This spec addresses the 80/20: ship-blockers, dead code removal, and the core Stimulus+Svelte bridge pattern.

## Scope

### 1. Fix Ship-Blockers

| File | Change | Why |
|------|--------|-----|
| `Dockerfile` line 3 | `FROM python:3.14-slim` | Match `pyproject.toml` `requires-python = ">=3.14"`. 3.12 + 3.14 deps = build failure. |
| `config/asgi.py` | After `setdefault`, log warning if `ENVIRONMENT=production` but `DJANGO_SETTINGS_MODULE` still `.dev` | Prevent silent prod-with-dev-settings |
| `Makefile prod-start` | Add `DJANGO_SETTINGS_MODULE=config.settings.production` to the env prefix | Currently only sets `ENVIRONMENT`, not `DJANGO_SETTINGS_MODULE` |
| `config/settings/production.py` | Add comment block documenting when to enable `SECURE_SSL_REDIRECT` and HSTS. Leave them commented. | Prevent redirect loops in unknown proxy topology. Documented, not auto-enabled. |
| `config/settings/base.py` | Add warning log when AWS_S3 config is partial (1-2 of 3 vars set) + fallback note | Silent filesystem fallback is confusing during debugging |

**Non-goal:** No re-architecture of settings inheritance. No Docker Compose changes.

### 2. Remove htmx

| File | Change |
|------|--------|
| `frontend/package.json` | Remove `"htmx.org"` from dependencies |
| `frontend/src/js/main.js` | Remove `import htmx from "htmx.org"` + `window.htmx = htmx` |

**Rationale:** htmx not used in templates (confirmed via grep). Only imported in main.js and package.json. Removal is mechanical.

**Non-goal:** No replacement library. Django forms + full page loads + Stimulus+Svelte islands cover htmx's cases.

### 3. Generic Stimulus Controller for Svelte Mounting

Replace the per-component `welcome-svelte` controller with a single reusable controller.

**New file:** `frontend/src/js/controllers/svelte-bridge.js`

```
Stimulus values:
  - component (String, required) — name of Svelte component file (without .svelte)
  - props (Object, optional) — props passed to Svelte component on mount

connect(): dynamically import the component from ../svelte/{component}.svelte and mount
disconnect(): unmount
```

**Usage in template:**
```html
<div data-controller="svelte-bridge"
     data-svelte-bridge-component-value="Counter"
     data-svelte-bridge-props-value='{"initial": 42}'>
</div>
```

**Existing controller retained:** `welcome-svelte.js` kept as reference example but with comment noting it's replaced by the generic bridge.

**Non-goal:** No build-time Svelte SSR. No SvelteKit. Vite handles Svelte compilation for islands.

### 4. Fix Remaining Issues

| # | Issue | File | Change |
|---|-------|------|--------|
| 4a | `immutable_file_test` regex too narrow (`{8,12}`) | `config/settings/base.py` | Widen to `{8,}` — Vite/rollup hashes vary |
| 4b | `CONN_MAX_AGE` no strategy | `config/settings/base.py` | Add comment: set `CONN_MAX_AGE_STRATEGY = "max_lifetime"` for psycopg3 when needed |
| 4c | `username` in `REQUIRED_FIELDS` with email as `USERNAME_FIELD` | `apps/users/models.py` | Add comment explaining why username is kept (allauth compat). No code change — removing would break allauth signup flow |
| 4d | `User.save()` double normalization | `apps/users/models.py` | Add comment noting allauth also normalizes email. Keep current normalization as belt-and-suspenders |
| 4e | `DMR_SETTINGS` re-declared in `production.py` | `config/settings/production.py` | Replace full re-declaration with `DMR_SETTINGS.update({Settings.validate_responses: False})` — inherits base, only overrides what differs |

### 5. Update README

Rewrite `README.md` to reflect current state:

- **Stack table:** remove htmx row. Add Stimulus row. Keep GSAP.
- **Quickstart:** verify all commands work, update if needed
- **Production section:** new "Production Checklist" subsection documenting:
  - SSL/HSTS enablement steps
  - DMR pre-1.0 maturity note
  - Granian ecosystem note (mature, but smaller than Gunicorn)
  - Python 3.14 package compatibility note
  - Redis single-node limits
  - SECURE_PROXY_SSL_HEADER config for reverse proxies
- **Architecture section:** briefly describe the Django-forms-primary + Stimulus-mounts-Svelte pattern
- **Document future additions pattern:** "To add feature X, do Y"

## Out of Scope

- **HSTS auto-enable** — must be manual per deployment topology
- **django-channels** real-world usage — boilerplate stays, add routes per-app
- **Cacheops tuning** — starter kit doesn't have scale where this matters
- **Auditlog async offloading** — fine for starter kit traffic
- **guardian object permission perf** — documented in BRIEF.md, fix when hit
- **Svelte ecosystem migration** — not moving to SvelteKit
- **CI/CD pipeline** — not part of this sprint
- **Testing** — existing tests pass, no new test debt added

## Risks

| Risk | Mitigation |
|------|------------|
| python:3.14-slim may not have wheels for all deps | `uv pip install --system` handles source builds. Monitor upstream build status. |
| Stimulus dynamic import of Svelte may tree-shake poorly | Vite handles code-splitting. Each Svelte component becomes own chunk, loaded lazily. |
| DMR 0.x breaking changes on upgrade | Pin DMR version in pyproject.toml. Add upgrade guide in README. |

## Success Criteria

1. `make dev-up` builds and runs without error
2. `make dev-shell` + `python manage.py check --deploy` passes with only expected warnings
3. htmx not present in `package.json` lockfile or JS bundle
4. Svelte component mounts via generic Stimulus controller
5. README accurately describes current stack
