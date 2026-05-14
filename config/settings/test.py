# config/settings/test.py
"""
Test settings for the Django project.

These settings are used when running tests to ensure a consistent and isolated
testing environment.
"""

from .base import *  # noqa: F403

# Use an in-memory SQLite database for faster tests
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}


# Disable migrations for faster tests
class DisableMigrations:
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None


MIGRATION_MODULES = DisableMigrations()

# Use a fast password hasher for tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Disable caching for tests
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}

# Disable cacheops during tests
CACHEOPS_ENABLED = False

# Disable logging during tests for cleaner output
LOGGING_CONFIG = None

# Use console email backend for tests
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Disable whitenoise during tests
WHITENOISE_AUTOREFRESH = True
WHITENOISE_USE_FINDERS = True

# Test-specific settings
SECRET_KEY = "test-secret-key-for-testing-only"
DEBUG = False

# Disable CSRF and non-essential middleware for tests
MIDDLEWARE = [
    middleware
    for middleware in MIDDLEWARE  # noqa: F405
    if middleware
    not in [
        "django.middleware.csrf.CsrfViewMiddleware",
        "corsheaders.middleware.CorsMiddleware",
        "django_htmx.middleware.HtmxMiddleware",
    ]
]

# Use local memory storage for tests
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.InMemoryStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# Disable dramatiq during tests
DRAMATIQ_BROKER = {
    "BROKER": "dramatiq.brokers.stub.StubBroker",
    "OPTIONS": {},
    "MIDDLEWARE": [
        "dramatiq.middleware.AgeLimit",
        "dramatiq.middleware.TimeLimit",
        "dramatiq.middleware.Callbacks",
        "dramatiq.middleware.Retries",
    ],
}