# BRIEF.md

### **1. Introduction**

#### **1.1. Purpose**

This document outlines the system architecture for a universal, modern, and efficient Django 5.2 LTS Starter Kit. Its primary purpose is to serve as a robust, secure, and flexible foundation for building high-performance web applications, from API services to content-driven sites.

#### **1.2. Scope**

The architecture covers the backend structure, data modeling, frontend integration, performance strategies, security considerations, and deployment. It is intended to guide development by providing a reusable boilerplate that prioritizes developer experience (DX), application performance, and long-term maintainability.

#### **1.3. Core Principles**

- **Modularity:** Functionality is built from independent, reusable Django apps.
- **Convention over Configuration:** A clear and logical project structure reduces cognitive overhead and ensures consistency.
- **Performance First:** The system is architected for speed, incorporating caching, asset optimization, and efficient data retrieval by default.
- **Decoupled Services:** The application, data, and message brokering layers are separated to enable independent scaling and improve resilience.
- **Streamlined Development (DX):** Provides a clean, well-documented, and modern development environment to maximize productivity.
- **Security by Default:** Integrates security best practices and tooling from the ground up.
- **Let Packages Do Their Job:** Avoid reimplementing what mature, well-tested packages already provide. Prefer thin integration over custom abstraction.

---

### **2. System Architecture Overview**

The system is a modular monolithic web application built on the Django framework. While monolithic in codebase, its dependencies (database, cache, message broker) are decoupled services, enabling flexible deployment and scaling.

- **Presentation Layer (Frontend):** Renders the user interface using Django's templating engine, styled with Tailwind CSS v4 + DaisyUI v5, and enhanced with htmx for in-place HTML updates and Svelte 5 for high-interactivity islands. Stimulus acts as the controller glue for mounting components.
- **Application Layer (Backend):** Contains the core business logic, managed by Django views. API endpoints will be served by **django-modern-rest (DMR)** (replacing DRF). Asynchronous tasks are handled by Dramatiq.
- **Data Layer:** Manages data persistence, caching, and search. This includes a primary relational database (**ParadeDB**) for structured data and full-text search, and an in-memory cache (**Redis / Valkey**) for high-speed data access via **django-cacheops**.

---

### **3. Technology Stack**

All Python dependencies are managed by **`uv`** via a single `pyproject.toml` file.

- **Backend Framework:** Django 5.2 LTS
- **API Framework:** django-modern-rest (DMR) *(DRF is present as a placeholder until DMR integration is complete)*
- **Database:** ParadeDB (PostgreSQL 17 with search & analytics extensions)
- **Cache:** Redis / Valkey 7 — `django-redis` + `django-cacheops`
- **Task Queue:** Dramatiq + Redis (as the message broker)
- **Python Tooling:** `uv` (package manager), `ruff` (linter/formatter), `pytest` (testing)
- **Configuration:** `django-environ` (env var management via `env.db()`, `env.bool()`, etc.)
- **Authentication:** `django-allauth` (social auth, OIDC, local accounts, email verification)
- **Audit Logging:** `django-auditlog` (automatic model change tracking)
- **Frontend Bundler:** Vite (`django-vite`)
- **Frontend Styling:** Tailwind CSS v4 + DaisyUI v5
- **Interactivity:** htmx 2 (in-place HTML) + Stimulus 3 (controller glue) + Svelte 5 (interactive islands) + GSAP 3 (animations)
- **Real-time/WebSockets:** `django-channels` + `channels-redis` (boilerplate ready; routes added per-app)
- **Email:** `django-anymail` (Postmark or AWS SES)
- **File Storage:** `django-storages` (S3-compatible backend) + `django-imagekit` (image processing)
- **Observability:** Sentry SDK (error tracking + 10% performance sampling) + OpenTelemetry (Django, psycopg, Redis instrumentors only; opt-in via `OTEL_ENABLED=true`)
- **Server:** Granian 2.5+ (Production ASGI) + Whitenoise (Static File Serving)

---

### **4. Application Structure (Django Apps)**

A modular structure is mandated to ensure a clean separation of concerns.

- **`config/`**: The core Django project directory containing `settings/`, `urls.py`, and `asgi.py`. Settings are split into `base.py`, `dev.py`, `production.py`, and `test.py`. The active settings file is selected via the `DJANGO_SETTINGS_MODULE` environment variable — there is no `__init__.py` routing logic.
- **`frontend/`**: Manages all frontend assets. Houses the Vite build process, source files (`src/`), and outputs compiled assets to `dist/` loaded into templates via `django-vite`.
- **`templates/`**: Global templates directory for all apps.
- **`apps/`**: A top-level directory containing all custom applications.
  - **`users`**: Custom `User` model (email-based login, UUID PK, avatar). Auth and email verification managed by `django-allauth`. Audit trail via `django-auditlog`.
  - **`core`**: Foundational, project-wide abstractions. Contains `BaseModel` (UUID + timestamps). Keep this lean — if code grows into a domain, extract it to its own app.
  - **`pages`**: Static/marketing pages.
  - **`api`**: API endpoints — *placeholder, will be replaced by DMR*.

---

### **5. Authentication & Authorization**

Authentication is handled by **`django-allauth`** to provide a comprehensive and secure solution.

- **Core Functionality:** Manages user registration, login/logout, password reset, and email verification.
- **OpenID Connect (OIDC):** Pre-configured for OIDC-based SSO via `allauth.socialaccount`, enabling integration with identity providers like Authentik, Keycloak, or Okta. OIDC provider data is stored in allauth's `SocialAccount` model — not duplicated on the `User` model.
- **Custom User Model:** The `users` app defines a custom `User` model (`settings.AUTH_USER_MODEL`) inheriting from `AbstractUser` and `BaseModel`. Email is the `USERNAME_FIELD`. UUID is the primary key.
- **API Authentication:** Will be handled by DMR when integrated.

---

### **6. Data & Content Model**

#### **6.1. Base Model**

All custom models inherit from `BaseModel` defined in `apps/core/models.py`:

- **`BaseModel` (Abstract):** Provides `id` (UUID), `created_at`, and `updated_at`.

There is no `SoftDeleteModel` in the starter kit. If soft-delete is needed, add `django-safedelete` per-app.

#### **6.2. User Model**

The `User` model is intentionally minimal:

- Fields: `email` (unique, `USERNAME_FIELD`), `username`, `first_name`, `last_name`, `avatar`, `avatar_thumbnail` (ImageSpecField via imagekit), plus all `AbstractUser` fields.
- No separate `UserProfile` model — profile fields live on `User` directly.
- Automatic audit trail via `auditlog.register(User)`.

#### **6.3. Search and Analytics (ParadeDB)**

ParadeDB provides BM25 full-text search and columnar analytics. Queries are written at the service/view layer using raw SQL or ParadeDB's native Django integration. There is no custom `SearchManager` in the starter kit — add search when you need it.

#### **6.4. Caching**

`django-cacheops` provides declarative ORM-level caching backed by Redis. Configure `CACHEOPS` in `settings/base.py` per model. `CACHEOPS_DEGRADE_ON_FAILURE = True` ensures the app degrades gracefully if Redis is unavailable.

#### **6.5. File & Media Management**

- **Static Files:** Served by Whitenoise in production. Managed by Vite.
- **Media Files:** User-uploaded content handled by `django-storages` with an S3-compatible backend (AWS S3, MinIO). Falls back to `FileSystemStorage` if no AWS credentials are set.
- **Image Processing:** `django-imagekit` — `ImageSpecField` on the `User` model generates avatar thumbnails on demand.

---

### **7. Frontend Architecture**

#### **7.1. Paradigm**

Three complementary layers — no framework overlap:

| Layer | Tool | When to use |
|-------|------|-------------|
| In-place HTML updates | **htmx 2** | Form submissions, partial page swaps, server-rendered fragments |
| Controller glue | **Stimulus 3** | Mounting Svelte components, minor DOM behavior |
| Interactive islands | **Svelte 5** | Complex client-side UI that requires state (uses the API) |
| Animations | **GSAP 3** | Transitions, entrance/exit effects |

htmx replaces Turbo. Svelte components are mounted via Stimulus controllers using the Svelte 5 `mount()` / `unmount()` imperative API.

#### **7.2. Template Structure**

- **`templates/base.html`**: Main site template, loads compiled assets via `django-vite` tags.
- HTMX partial responses are standard Django template fragments.
- Svelte islands are mounted into `data-controller` elements by Stimulus.

#### **7.3. Styling & Static Assets**

- Styling is defined in `frontend/src/css/styles.css`, importing Tailwind CSS v4 via `@import "tailwindcss"` and DaisyUI v5 via `@plugin "daisyui"`.
- **Vite** processes source files and outputs hashed assets to `frontend/dist/`.
- `{% vite_hmr_client %}` and `{% vite_asset 'src/js/main.js' %}` handle dev (HMR) and production asset loading automatically.

---

### **8. Performance & Optimization**

- **Caching:** `django-cacheops` for declarative ORM caching. `django-redis` for session and low-level cache API.
- **Database Queries:** Use `select_related` and `prefetch_related` to prevent N+1 problems. `django-debug-toolbar` is installed in development.
- **Asynchronous Tasks:** Offload long-running tasks to **Dramatiq** (Redis broker) to keep web requests fast.

---

### **9. Deployment & Operations (DevOps)**

- **Containerization:** The application stack (web, database, broker, worker) is defined in Docker Compose files for consistent, reproducible environments.
- **Environment Configuration:** All sensitive data is managed via environment variables using `django-environ`. No secrets in version control. Use `DJANGO_SETTINGS_MODULE` to select the active settings file.
- **CI/CD Pipeline:** GitHub Actions automates linting (`ruff`), testing (`pytest`), Docker image build, and deployment.
- **Observability:**
  - **Error Tracking:** Sentry SDK — initializes only if `SENTRY_DSN` is set. `traces_sample_rate=0.1` (10%). No PII sent.
  - **Performance Tracing:** OpenTelemetry — opt-in via `OTEL_ENABLED=true`. Instruments Django, psycopg, and Redis only.

---

### **NOTE:**

- **Modern Tooling:** This starter kit is built with modern, actively maintained, and stable tools. Outdated or unmaintained packages are strictly avoided.
- **High-Performance Server:** **Granian** is the recommended production server. Its Rust-based, async-native architecture provides exceptional speed and concurrency for modern ASGI Django applications.
- **API Layer:** DRF (`djangorestframework`) is present as a placeholder. It will be replaced by **django-modern-rest (DMR)** — a type-safe, async-capable, OpenAPI-first REST framework.
