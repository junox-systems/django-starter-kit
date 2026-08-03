"""
ASGI config for config project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
import logging

from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator

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
