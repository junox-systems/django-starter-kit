"""
ASGI config for config project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
import sys

# Initialize OpenTelemetry BEFORE Django loads
# DjangoInstrumentor must patch middleware before Django is imported
from config.otel import initialize_opentelemetry
initialize_opentelemetry()

import logging

from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from opentelemetry.instrumentation.asgi import OpenTelemetryMiddleware

logger = logging.getLogger(__name__)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

# Warn if production environment but settings still at dev default
if (
    os.environ.get("ENVIRONMENT") == "production"
    and "config.settings.dev" in os.environ.get("DJANGO_SETTINGS_MODULE", "")
):
    logger.warning(
        "DJANGO_SETTINGS_MODULE is '%s' but ENVIRONMENT=production. "
        "Set DJANGO_SETTINGS_MODULE=config.settings.production explicitly.",
        os.environ["DJANGO_SETTINGS_MODULE"],
    )

django_asgi_app = get_asgi_application()

print(f"DEBUG: Django ASGI app created: {django_asgi_app}", file=sys.stderr)

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AllowedHostsOriginValidator(
            AuthMiddlewareStack(
                URLRouter(
                    [
                        # Add WebSocket URL routes here
                    ]
                )
            )
        ),
    }
)

print(f"DEBUG: Application created (no OpenTelemetryMiddleware wrapper)", file=sys.stderr)
