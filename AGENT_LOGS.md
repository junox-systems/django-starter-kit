# Agent Logs

This file documents the implementation of the Django 5.2 LTS Starter Kit.

## Project Setup

- Initialized a new Django project.
- Configured `django-environ` to manage environment variables.
- Set up the project structure with `apps`, `config`, `frontend`, and `templates` directories.

## Dependencies

- Added the following dependencies to `pyproject.toml`:
  - `django`
  - `djangorestframework`
  - `django-environ`
  - `django-allauth`
  - `django-vite`
  - `django-imagekit`
  - `django-storages`
  - `django-anymail`
  - `django-actioncable`
  - `django-cors-headers`
  - `django-redis`
  - `whitenoise`
  - `dramatiq`
  - `ruff`
  - `sentry-sdk`
  - `opentelemetry-sdk`
  - `opentelemetry-instrumentation-django`
  - `pytest`
  - `pytest-django`
  - `mypy`
  - `psycopg`
  - `pillow`
  - `boto3`
  - `requests`
  - `amqp`

## Backend

### Database

- Configured the project to use PostgreSQL with `psycopg2-binary`.
- Implemented ParadeDB search functionality with a custom `SearchManager` in `apps/core/search.py`.
- Added a placeholder for analytics in `apps/core/analytics.py`.

### Caching

- Configured Redis as the cache backend using `django-redis`.

### Task Queue

- Configured Dramatiq with RabbitMQ as the message broker.

### Email

- Configured `django-anymail` with Postmark as the email backend.

### File Storage

- Configured `django-storages` to use Amazon S3 for file storage.

### Observability

- Set up Sentry and OpenTelemetry for error tracking and performance monitoring.

### Security

- Implemented production security best practices in `config/settings/production.py`.

### Models

- Created abstract base models `BaseModel` and `SoftDeleteModel` for common fields and soft delete functionality.

## API

- Implemented the `api` app using Django REST Framework.
- Created `UserSerializer` and `UserViewSet` for user API endpoints.

## Authentication & Authorization

- Included `allauth.urls` for user registration, login/logout, and password reset.
- Configured OIDC-based SSO using `allauth.socialaccount.providers.openid_connect`.
- Implemented 2FA using `allauth.mfa`.

## Frontend

### Build Process

- Set up a Vite frontend build process with `vite.config.js` and `package.json`.

### Dependencies

- Added the following frontend dependencies:
  - `vite`
  - `@hotwired/stimulus`
  - `@hotwired/turbo`
  - `gsap`
  - `tailwindcss`
  - `postcss`
  - `autoprefixer`
  - `daisyui`

### Hotwire

- Implemented Hotwire (Turbo + Stimulus) for interactivity.

### Styling

- Set up Tailwind CSS v4 with Daisy UI for styling.

## Templates

- Created a base template structure with `base.html`, `_header.html`, and `_footer.html`.

## CI/CD

- Set up a GitHub Actions CI/CD pipeline to run tests on push and pull requests.
- Created a `Makefile` to standardize commands.

## Containerization

- Created a `docker-compose.yml` file to define the application stack (web, database, cache, broker, worker) for consistent local development.
- Created a `Dockerfile` to build the web service, including frontend build steps and optimized for Docker environment.

## Additional Implementations and Refinements

### Pages App Integration

- Moved the `pages` app to the `apps` directory.
- Added `apps.pages` to `INSTALLED_APPS` in `config/settings/base.py`.
- Updated `config/urls.py` to reference `apps.pages.urls` instead of `pages.urls`.

## Refactoring and Bug Fixes

- Fixed duplicated `DEFAULT_AUTO_FIELD` and `Allauth MFA Settings` in `config/settings/base.py`.
- Consolidated `STATIC_URL` and related static file settings in `config/settings/base.py`.

## Missing/Incomplete Items Implemented

### Real-time/WebSockets

- Implemented `django-channels` for WebSockets.

### Media Processing

- Configured `django-imagekit` usage with `UserProfile` model.

### API Authentication

- Set up DRF authentication using `rest_framework.authtoken`.

### Performance & Optimization

- Set up `django-debug-toolbar`.

### CI/CD Pipeline

- Integrated `ruff` and `mypy` into the CI pipeline via `Makefile` commands.
- Added Docker image build to the CI pipeline, with deployment steps as placeholders (commented out as per user's instruction for CI-only).

## OpenTelemetry Integration

- Added comprehensive OpenTelemetry instrumentation for Django, database, Redis, HTTP requests, logging, system metrics, asyncio, and threading
- Created detailed documentation in `OPENTELEMETRY.md` with instructions for using with SigNoz and other OpenTelemetry-compatible backends
- Added environment variables to `.env` to enable OpenTelemetry by default
- Updated README to include OpenTelemetry in the Developer Tools section

## What Changed Recently

- **Background Jobs**: Switched from Celery to Dramatiq for simpler job processing
- **Better DX**: Improved development commands and logging
- **Hot Reloading**: Code changes automatically reload in your browser
