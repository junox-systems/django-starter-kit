from .base import *  # noqa: F403
from .base import env, DMR_SETTINGS

from dmr.settings import Settings

# Performance: disable response validation in production.
# Docs: "Keep it on in development, but disable it in production
# to get the best of both worlds."
DMR_SETTINGS.update({Settings.validate_responses: False})

# Production-specific settings
# ------------------------------------------------------------------------------
DEBUG = False

# base.py falls back to a public dev key; never serve production with it.
if SECRET_KEY.startswith("django-insecure"):  # noqa: F405
    from django.core.exceptions import ImproperlyConfigured

    raise ImproperlyConfigured("SECRET_KEY must be set in production.")

# ALLOWED_HOSTS configuration for production
# This is required when DEBUG is set to False
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

# Behind a TLS proxy Django sees http (until SECURE_PROXY_SSL_HEADER is on), so
# the browser's https Origin must be trusted explicitly or every POST gets 403.
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

# Postmark rejects unverified senders; the webmaster@localhost fallback would
# silently break signup (email verification is mandatory). No default on purpose.
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL")
SERVER_EMAIL = env("SERVER_EMAIL", default=DEFAULT_FROM_EMAIL)

# Security Settings
# ------------------------------------------------------------------------------
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# SSL/TLS: Enable these AFTER configuring your reverse proxy to set
# X-Forwarded-Proto. Do NOT enable without the proxy header — it
# causes infinite redirect loops. prod/nginx/nginx.conf (the nginx
# service in docker-stack.yml) sets the header.
# SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
# SECURE_SSL_REDIRECT = True
# SECURE_HSTS_SECONDS = 31536000  # 1 year
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# SECURE_HSTS_PRELOAD = True
