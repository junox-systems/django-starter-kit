from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST
from django_q.tasks import async_task

from .forms import InviteForm, OrganizationForm
from .models import Invitation, Membership

OWNER = Membership.Role.OWNER


def _membership(request, pk):
    """The requester's membership in org `pk`; 404 for non-members so org ids don't leak."""
    return get_object_or_404(
        Membership.objects.select_related("organization"),
        organization_id=pk,
        user=request.user,
    )


def _owner_membership(request, pk):
    membership = _membership(request, pk)
    if not membership.is_owner:
        raise PermissionDenied
    return membership


@login_required
@require_http_methods(["GET", "POST"])
def org_list(request):
    form = OrganizationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            org = form.save()
            Membership.objects.create(organization=org, user=request.user, role=OWNER)
        return redirect("org_detail", pk=org.pk)
    memberships = request.user.memberships.select_related("organization")
    return render(request, "orgs/list.html", {"memberships": memberships, "form": form})


@login_required
@require_http_methods(["GET", "POST"])
def org_detail(request, pk):
    membership = _membership(request, pk)
    org = membership.organization
    form = InviteForm(request.POST or None)
    if request.method == "POST":
        if not membership.is_owner:
            raise PermissionDenied
        if form.is_valid():
            email = form.cleaned_data["email"]
            if org.members.filter(email=email).exists():
                form.add_error("email", "Already a member.")
            else:
                # Re-inviting replaces the old invite: fresh token, fresh expiry.
                Invitation.objects.filter(organization=org, email=email).delete()
                invitation = Invitation.objects.create(
                    organization=org, email=email, invited_by=request.user
                )
                accept_url = request.build_absolute_uri(
                    reverse("invitation_accept", args=[invitation.token])
                )
                async_task(
                    "apps.orgs.tasks.send_invitation_email", invitation.id, accept_url
                )
                messages.success(request, f"Invitation sent to {email}.")
                return redirect("org_detail", pk=pk)
    return render(
        request,
        "orgs/detail.html",
        {
            "org": org,
            "membership": membership,
            "memberships": org.memberships.select_related("user"),
            "invitations": org.invitations.all() if membership.is_owner else [],
            "form": form,
        },
    )


@login_required
@require_POST
def org_delete(request, pk):
    _owner_membership(request, pk).organization.delete()
    messages.success(request, "Organization deleted.")
    return redirect("orgs")


@login_required
@require_POST
def membership_remove(request, pk, membership_pk):
    """Owners remove anyone; members can only remove themselves (leave)."""
    me = _membership(request, pk)
    target = get_object_or_404(Membership, pk=membership_pk, organization_id=pk)
    if target != me and not me.is_owner:
        raise PermissionDenied
    if (
        target.is_owner
        and not target.organization.memberships.filter(role=OWNER)
        .exclude(pk=target.pk)
        .exists()
    ):
        messages.error(
            request,
            "An organization needs an owner. Delete it instead, or ask the admin to promote someone.",
        )
        return redirect("org_detail", pk=pk)
    target.delete()
    if target == me:
        return redirect("orgs")
    return redirect("org_detail", pk=pk)


@login_required
@require_POST
def invitation_revoke(request, pk, invitation_pk):
    _owner_membership(request, pk)
    get_object_or_404(Invitation, pk=invitation_pk, organization_id=pk).delete()
    return redirect("org_detail", pk=pk)


@login_required
@require_http_methods(["GET", "POST"])
def invitation_accept(request, token):
    invitation = get_object_or_404(
        Invitation.objects.select_related("organization"), token=token
    )
    # The token alone is not enough: it was emailed, so require the account
    # to own that address (verified) before joining.
    email_matches = request.user.emailaddress_set.filter(
        email__iexact=invitation.email, verified=True
    ).exists()
    if invitation.is_expired:
        return render(
            request, "orgs/accept.html", {"invitation": invitation}, status=410
        )
    if request.method == "POST" and email_matches:
        with transaction.atomic():
            Membership.objects.get_or_create(
                organization=invitation.organization, user=request.user
            )
            invitation.delete()
        return redirect("org_detail", pk=invitation.organization_id)
    return render(
        request,
        "orgs/accept.html",
        {"invitation": invitation, "email_matches": email_matches},
        status=200 if email_matches else 403,
    )
