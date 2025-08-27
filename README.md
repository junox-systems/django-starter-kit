# Django 5.2 LTS Starter Kit

A modern, production-ready Django starter kit that helps you build web applications faster.

## What is this?

This is a complete Django development environment that gives you everything you need to start building web applications right away. Think of it as your project's foundation - all the boring setup work is already done.

## What's Inside?

### Backend

- **Django 5.2 LTS** - The latest stable version of the popular Python web framework
- **PostgreSQL 17** - A reliable database (with ParadeDB for search features)
- **Redis 7 (valkey)** - For caching and session storage
- **RabbitMQ 4** - Message broker for background tasks
- **MinIO** - S3-compatible file storage for dev

### Frontend

- **Hotwire (Turbo 8 + Stimulus 3)** - Make your pages feel fast and modern without complex JavaScript
- **Vite 5** - Super fast development server and build tool
- **Tailwind CSS v4** - Utility-first CSS framework for styling
- **Daisy UI 5** - Beautiful UI components that work with Tailwind

### Developer Tools

- **Docker** - Consistent development environment that works everywhere
- **uv** - Ultra-fast Python package manager
- **Ruff** - Code formatting and linting
- **Pytest** - Testing framework
- **OpenTelemetry** - Distributed tracing and monitoring (see [OPENTELEMETRY.md](OPENTELEMETRY.md))

## Quick Start

### Prerequisites

- Docker and Docker Compose
- [OrbStack](https://orbstack.dev/) (recommended for macOS) or Docker Desktop

### Get Started

1. **Clone the repository:**

   ```bash
   git clone <repository-url>
   cd django-starter-kit
   ```

2. **Start everything:**

   ```bash
   make dev-up
   ```

3. **Watch the logs:**

   ```bash
   make dev-logs
   ```

4. **Open your browser:**

   - Django app: http://localhost:8000
   - Frontend dev server: http://localhost:5173

5. **Set up the database (first time only):**
   ```bash
   make dev-shell
   # Inside the container:
   python manage.py migrate
   python manage.py createsuperuser
   ```

## How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│     http://localhost:8000    http://localhost:5173          │
└─────────────┬─────────────────────────┬─────────────────────┘
              │                         │
    ┌─────────▼──────────┐       ┌───────────▼───────────┐
    │     Django App     │       │    Vite Dev Server    │
    │                    │◄─────►│                       │
    │  - Python Logic    │       │  - Hot Reload CSS/JS  │
    │  - HTML Templates  │       │  - Fast Updates       │
    └─────────┬──────────┘       └───────────────────────┘
              │
              │                  ┌───────────────────────┐
              │                  │    Background Jobs    │
              │◄────────────────►│                       │
              │                  │     - dramatiq        │
              │                  │     - RabbitMQ        │
              │                  └───────────────────────┘
              │
    ┌─────────▼──────────┐       ┌───────────────────────┐
    │      Database      │       │    Cache & Storage    │
    │                    │       │                       │
    │    - PostgreSQL    │       │     - Redis           │
    │    - Search        │       │     - MinIO (S3)      │
    └────────────────────┘       └───────────────────────┘
```

Everything runs in Docker containers, so you don't need to install anything on your computer except Docker.

## Development Commands

```bash
make dev-up      # Start everything in the background
make dev-down    # Stop everything
make dev-logs    # Watch logs from all services
make dev-clean   # Clean up everything (including data)
make dev-shell   # Get a command line inside the Django container
```

## Project Structure

```
├── apps/           # Your Django applications
│   ├── core/      # Shared code (models, utilities)
│   ├── users/     # User accounts and profiles
│   ├── api/       # REST API endpoints
│   └── pages/     # Simple web pages
├── frontend/      # CSS, JavaScript, images
├── config/        # Django settings
├── templates/     # HTML templates
└── dev/           # Docker development files
```

## Learn More

For detailed development guidelines and best practices, see [DEVELOPMENT.md](DEVELOPMENT.md).

## License

MIT License - see LICENSE file for details.
