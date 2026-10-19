from allauth.account.decorators import reauthentication_required
from auditlog.context import disable_auditlog
from auditlog.models import LogEntry
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView

from apps.orgs.models import release_user


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "users/profile.html"


def user_export(user):
    """Everything this kit stores about a user. No secrets: no password hash, no tokens."""
    return {
        "email": user.email,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "date_joined": user.date_joined.isoformat(),
        "last_login": user.last_login.isoformat() if user.last_login else None,
        "avatar": user.avatar.name or None,
        "email_addresses": [
            {"email": e.email, "verified": e.verified, "primary": e.primary}
            for e in user.emailaddress_set.all()
        ],
        "organizations": [
            {"name": m.organization.name, "role": m.role}
            for m in user.memberships.select_related("organization")
        ],
        "social_accounts": [
            {"provider": a.provider, "uid": a.uid} for a in user.socialaccount_set.all()
        ],
    }


@login_required
@reauthentication_required
def export_data(request):
    response = JsonResponse(user_export(request.user), json_dumps_params={"indent": 2})
    response["Content-Disposition"] = 'attachment; filename="my-data.json"'
    return response


@login_required
@require_http_methods(["GET", "POST"])
@reauthentication_required(allow_get=True)
def delete_account(request):
    if request.method == "POST":
        if request.POST.get("confirm", "").strip().lower() != request.user.email:
            messages.error(request, "Type your email address to confirm.")
            return redirect("delete_account")
        user = request.user
        logout(request)
        release_user(user)
        # Erase the user's own change history too (it holds their old values);
        # entries they authored elsewhere keep the change with actor=NULL.
        with disable_auditlog():
            LogEntry.objects.get_for_object(user).delete()
            user.delete()
        messages.success(request, "Your account has been deleted.")
        return redirect("home")
    return render(request, "users/delete_account.html")
