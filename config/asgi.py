"""
ASGI config for config project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os


from django.urls import path
from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator

# Print environment variables for debugging
print(
    f"DJANGO_SETTINGS_MODULE before: {os.environ.get('DJANGO_SETTINGS_MODULE', 'Not set')}"
)
print(f"ENVIRONMENT: {os.environ.get('ENVIRONMENT', 'Not set')}")

# Import ActionCableConsumer directly
try:
    from actioncable import ActionCableConsumer

    has_actioncable = True
except ImportError:
    has_actioncable = False


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# Print the actual settings module being used
print(f"DJANGO_SETTINGS_MODULE after: {os.environ.get('DJANGO_SETTINGS_MODULE')}")

# Initialize OpenTelemetry for the ASGI application
print("Attempting to initialize OpenTelemetry...")
try:
    from config.otel import initialize_opentelemetry
    result = initialize_opentelemetry()
    print(f"OpenTelemetry initialization result: {result}")
except ImportError as e:
    print(f"OpenTelemetry not available or configured: {e}")
except Exception as e:
    print(f"Warning: Failed to initialize OpenTelemetry: {e}")
    import traceback
    traceback.print_exc()

django_asgi_app = get_asgi_application()

if has_actioncable:
    application = ProtocolTypeRouter(
        {
            "http": django_asgi_app,
            "websocket": AllowedHostsOriginValidator(
                AuthMiddlewareStack(
                    URLRouter(
                        [
                            path("cable", ActionCableConsumer.as_asgi()),
                        ]
                    )
                )
            ),
        }
    )
else:
    application = ProtocolTypeRouter(
        {
            "http": django_asgi_app,
        }
    )
