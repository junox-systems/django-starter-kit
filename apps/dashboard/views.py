# apps/dashboard/views.py

from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.views.generic import TemplateView

from .panels import account_payload, activity_payload


class DashboardView(LoginRequiredMixin, TemplateView):
    """Authenticated home. Panels are Svelte children of one Dashboard root."""

    template_name = "dashboard/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        # One payload dict -> one json_script node -> props of the Svelte root.
        context["payload"] = {
            "activity": activity_payload(user),
            "account": account_payload(user),
            # Resolved server-side so no island ever hardcodes a URL.
            "urls": {"activity": reverse("dashboard-activity")},
        }
        return context
