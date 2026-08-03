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

# ALLOWED_HOSTS configuration for production
# This is required when DEBUG is set to False
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

# Security Settings
# ------------------------------------------------------------------------------
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# SSL/TLS: Enable these AFTER configuring your reverse proxy to set
# X-Forwarded-Proto. Do NOT enable without the proxy header — it
# causes infinite redirect loops.
# SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
# SECURE_SSL_REDIRECT = True
# SECURE_HSTS_SECONDS = 31536000  # 1 year
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# SECURE_HSTS_PRELOAD = True
