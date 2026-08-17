from django.contrib import admin
from django.urls import path, include
from django.conf import settings

from dmr.openapi import build_schema
from dmr.openapi.views import SwaggerView, OpenAPIJsonView
from dmr.routing import Router

from apps.api.urls import urlpatterns as api_urlpatterns

# Build OpenAPI schema from the API router
_api_router = Router("api/v1/", api_urlpatterns)
schema = build_schema(_api_router)

# Core URL patterns
urlpatterns = [
    # DJ Control Room panel URLs — mounted under /admin/
    path("admin/dj-redis-panel/", include("dj_redis_panel.urls")),
    path("admin/dj-cache-panel/", include("dj_cache_panel.urls")),
    path("admin/dj-urls-panel/", include("dj_urls_panel.urls")),
    path("admin/dj-celery-panel/", include("dj_celery_panel.urls")),
    path("admin/dj-signals-panel/", include("dj_signals_panel.urls")),
    path("admin/dj-control-room/", include("dj_control_room.urls")),
    path("admin/", admin.site.urls),
    path("anymail/", include("anymail.urls")),
    path("api/v1/", include("apps.api.urls")),
    path("accounts/", include("allauth.urls")),
    path("dashboard/", include("apps.dashboard.urls")),
    path("dashboard/user/", include("apps.users.urls")),
    path("", include("apps.pages.urls")),
    # OpenAPI docs
    path(
        "docs/openapi.json",
        OpenAPIJsonView.as_view(schema=schema),
        name="openapi",
    ),
    path(
        "docs/swagger/",
        SwaggerView.as_view(schema=schema),
        name="swagger",
    ),
]

# Include debug toolbar URLs only in debug mode
if settings.DEBUG:
    try:
        import debug_toolbar
        urlpatterns.insert(0, path("__debug__/", include(debug_toolbar.urls)))
    except ImportError:
        pass
