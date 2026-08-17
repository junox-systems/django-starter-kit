# apps/dashboard/panels.py
"""
Dashboard panel payloads.

One function per panel. Each returns a JSON-safe dict of primitives, consumed
by both DashboardView (rendered with `json_script` into Svelte props) and the
DMR refresh controllers in apps/api. Single source of truth for panel shape —
never serialize a panel twice.

To add a panel, add a function here, add its key to
DashboardView.get_context_data, and add the matching Svelte child.
"""

from auditlog.models import LogEntry
from django.urls import reverse


def activity_payload(user, limit=10) -> dict:
    """Recent audited changes made by this user.

    Only models passed to `auditlog.register()` are recorded — today that is
    just User (apps/users/models.py), so expect this to be sparse until an
    adopter registers their own models.
    """
    # LogEntry.Meta.ordering is ["-timestamp"], so no explicit order_by needed.
    entries = LogEntry.objects.filter(actor=user).select_related("content_type")[:limit]
    return {
        "entries": [
            {
                "id": entry.id,
                "action": entry.get_action_display(),
                "model": entry.content_type.name if entry.content_type else "",
                "object_repr": entry.object_repr,
                "timestamp": entry.timestamp.isoformat(),
                # Field NAMES only, never values — `changes` can carry password
                # hashes and other secrets straight out of the model.
                "fields": sorted(entry.changes or {}),
            }
            for entry in entries
        ]
    }


def account_payload(user) -> dict:
    """Account setup and security checklist, from allauth's own tables."""
    # Imported lazily so this module stays importable without allauth loaded.
    from allauth.account.models import EmailAddress
    from allauth.socialaccount.models import SocialAccount

    verified = EmailAddress.objects.filter(user=user, verified=True).exists()
    providers = sorted(
        SocialAccount.objects.filter(user=user).values_list("provider", flat=True)
    )

    return {
        "checks": [
            {
                "label": "Email verified",
                "done": verified,
                "detail": user.email,
                "href": reverse("account_email"),
                "action": "Manage email" if verified else "Verify now",
            },
            {
                "label": "Password set",
                "done": user.has_usable_password(),
                "detail": "",
                "href": reverse("account_change_password"),
                "action": "Change password",
            },
            {
                "label": "Connected accounts",
                "done": bool(providers),
                "detail": ", ".join(providers),
                "href": reverse("socialaccount_connections"),
                "action": "Manage" if providers else "Connect a provider",
            },
        ],
        "last_login": user.last_login.isoformat() if user.last_login else None,
    }
