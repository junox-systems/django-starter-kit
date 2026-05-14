from .base import *  # noqa: F403
from .base import env, DMR_SETTINGS

from dmr.settings import Settings

# Disable DMR response validation in production for performance.
# Docs: "Keep it on in development, but disable it in production
# to get the best of both worlds."
DMR_SETTINGS = {
    **DMR_SETTINGS,
    Settings.validate_responses: False,
}

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
# SECURE_SSL_REDIRECT = True
# SECURE_HSTS_SECONDS = 31536000  # 1 year
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
# SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
