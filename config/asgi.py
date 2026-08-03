"""
ASGI config for config project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

# Initialize OpenTelemetry before Django loads so the global tracer
# provider is available to the ASGI middleware below.
from config.otel import initialize_opentelemetry

initialize_opentelemetry()

import logging  # noqa: E402

from django.core.asgi import get_asgi_application  # noqa: E402
from channels.auth import AuthMiddlewareStack  # noqa: E402
from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402
from channels.security.websocket import AllowedHostsOriginValidator  # noqa: E402
from opentelemetry.instrumentation.asgi import OpenTelemetryMiddleware  # noqa: E402

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

# Create one server span per HTTP request and propagate W3C trace context
# between the browser (HyperDX) and the backend.
application = OpenTelemetryMiddleware(application)
