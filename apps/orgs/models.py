# apps/orgs/models.py
"""Teams. Users belong to organizations through Membership; attach billing,
quotas and shared data to Organization, not User."""

import secrets

from auditlog.registry import auditlog
from django.conf import settings
from django.db import models

from apps.core.models import BaseModel


class Organization(BaseModel):
    name = models.CharField(max_length=100)
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL, through="Membership", related_name="organizations"
    )

    def __str__(self):
        return self.name


class Membership(BaseModel):
    class Role(models.TextChoices):
        OWNER = "owner", "Owner"
        MEMBER = "member", "Member"

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="memberships"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships"
    )
    role = models.CharField(max_length=10, choices=Role, default=Role.MEMBER)

    class Meta:
        ordering = ["created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "user"], name="unique_org_member"
            )
        ]

    def __str__(self):
        return f"{self.user} in {self.organization} ({self.role})"

    @property
    def is_owner(self):
        return self.role == self.Role.OWNER


def invitation_token():
    return secrets.token_urlsafe(32)


class Invitation(BaseModel):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="invitations"
    )
    email = models.EmailField()
    token = models.CharField(max_length=64, unique=True, default=invitation_token)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "email"], name="unique_org_invitation"
            )
        ]

    def __str__(self):
        return f"{self.email} to {self.organization}"


auditlog.register(Organization)
auditlog.register(Membership)
auditlog.register(Invitation, exclude_fields=["token"])


def release_user(user):
    """Run before deleting a user so no organization is left empty or ownerless.

    Orgs where they are the only member are deleted; orgs left without an
    owner hand ownership to the longest-standing remaining member.
    """
    for membership in user.memberships.select_related("organization"):
        others = membership.organization.memberships.exclude(user=user)
        if not others.exists():
            membership.organization.delete()
        elif (
            membership.is_owner
            and not others.filter(role=Membership.Role.OWNER).exists()
        ):
            heir = others.order_by("created_at").first()
            heir.role = Membership.Role.OWNER
            heir.save(update_fields=["role", "updated_at"])
