### config/settings/dev.py

import socket

from .base import *  # noqa: F403
from .base import env

# Development-specific settings

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool("DEBUG", default=True)

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0", "django-app"]

# CORS settings for development
CORS_ALLOW_ALL_ORIGINS = True

# Install Django Debug Toolbar
INSTALLED_APPS.append("debug_toolbar")  # noqa: F405
MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")  # noqa: F405

# Allow debug toolbar to show for Docker container requests

hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
INTERNAL_IPS = ["127.0.0.1", "10.0.2.2"] + [ip[:-1] + "1" for ip in ips]

# Use console for emails
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Hot-reload templates (dev only).
#
# Since Django 4.1, templates are cached by default even with DEBUG=True —
# Django wraps the default loaders in the "cached.Loader", which NEVER checks
# the file's mtime. Result: you edit a .html, save, refresh — nothing changes.
# Only a process restart picks it up.
#
# Django docs bless an override: specify OPTIONS["loaders"] explicitly and the
# cache wrapper is skipped, so templates re-read from disk on every request.
#
# Why TEMPLATES[0]? The TEMPLATES setting is a LIST of engines. base.py defines
# exactly one entry (the DjangoTemplates engine) — index 0. We mutate that
# entry in place; production.py inherits base.py untouched, so prod keeps the
# fast cached loader.
#
# Why APP_DIRS = False? "app_dirs" and "loaders" are mutually exclusive —
# Django raises ImproperlyConfigured if both are set. We flip APP_DIRS off and
# list the app_directories loader explicitly, keeping identical lookup order:
# project templates first, then each app's templates/.
#
# Reference: https://docs.djangoproject.com/en/5.2/ref/templates/api/#loader-types
TEMPLATES[0]["APP_DIRS"] = False  # noqa: F405  (was True in base.py)
TEMPLATES[0]["OPTIONS"]["loaders"] = [  # noqa: F405
    "django.template.loaders.filesystem.Loader",
    "django.template.loaders.app_directories.Loader",
]

# Debug Toolbar Configuration
DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": lambda request: DEBUG,
}

# Debug Toolbar Panels Configuration
DEBUG_TOOLBAR_PANELS = [
    'debug_toolbar.panels.versions.VersionsPanel',
    'debug_toolbar.panels.timer.TimerPanel',
    'debug_toolbar.panels.settings.SettingsPanel',
    'debug_toolbar.panels.headers.HeadersPanel',
    'debug_toolbar.panels.request.RequestPanel',
    'debug_toolbar.panels.sql.SQLPanel',
    'debug_toolbar.panels.staticfiles.StaticFilesPanel',
    'debug_toolbar.panels.templates.TemplatesPanel',
    'debug_toolbar.panels.cache.CachePanel',
    'debug_toolbar.panels.signals.SignalsPanel',
    'debug_toolbar.panels.logging.LoggingPanel',
    'debug_toolbar.panels.redirects.RedirectsPanel',
    'debug_toolbar.panels.profiling.ProfilingPanel',
]
