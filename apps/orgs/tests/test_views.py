from datetime import timedelta

from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.orgs.models import (
    INVITATION_TTL,
    Invitation,
    Membership,
    Organization,
    release_user,
)
from apps.users.models import User

OWNER, MEMBER = Membership.Role.OWNER, Membership.Role.MEMBER


def make_user(name):
    user = User.objects.create_user(
        email=f"{name}@example.com", username=name, password="s3cret-pw"
    )
    user.emailaddress_set.create(email=user.email, verified=True, primary=True)
    return user


class OrgTestCase(TestCase):
    def setUp(self):
        self.owner = make_user("olga")
        self.member = make_user("milo")
        self.outsider = make_user("otto")
        self.org = Organization.objects.create(name="Acme")
        self.owner_m = Membership.objects.create(
            organization=self.org, user=self.owner, role=OWNER
        )
        self.member_m = Membership.objects.create(
            organization=self.org, user=self.member, role=MEMBER
        )
        self.detail = reverse("org_detail", args=[self.org.pk])


class OrgListTests(OrgTestCase):
    def test_empty_state(self):
        self.client.force_login(self.outsider)
        response = self.client.get(reverse("orgs"))
        self.assertContains(response, "not in any organization yet")

    def test_create_makes_requester_owner(self):
        self.client.force_login(self.outsider)
        response = self.client.post(reverse("orgs"), {"name": "Globex"})
        org = Organization.objects.get(name="Globex")
        self.assertRedirects(response, reverse("org_detail", args=[org.pk]))
        self.assertEqual(org.memberships.get().role, OWNER)


class OrgDetailTests(OrgTestCase):
    def test_non_member_gets_404(self):
        self.client.force_login(self.outsider)
        self.assertEqual(self.client.get(self.detail).status_code, 404)

    def test_owner_invites_by_email(self):
        self.client.force_login(self.owner)
        self.client.post(self.detail, {"email": " Otto@Example.com "})
        invitation = Invitation.objects.get(organization=self.org)
        self.assertEqual(invitation.email, "otto@example.com")
        self.assertEqual(mail.outbox[-1].to, ["otto@example.com"])
        self.assertIn(invitation.token, mail.outbox[-1].body)

    def test_member_cannot_invite(self):
        self.client.force_login(self.member)
        response = self.client.post(self.detail, {"email": "otto@example.com"})
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Invitation.objects.exists())

    def test_inviting_existing_member_is_rejected(self):
        self.client.force_login(self.owner)
        response = self.client.post(self.detail, {"email": "milo@example.com"})
        self.assertContains(response, "Already a member.")


class InvitationAcceptTests(OrgTestCase):
    def setUp(self):
        super().setUp()
        self.invitation = Invitation.objects.create(
            organization=self.org, email="otto@example.com", invited_by=self.owner
        )
        self.url = reverse("invitation_accept", args=[self.invitation.token])

    def test_matching_verified_email_joins(self):
        self.client.force_login(self.outsider)
        response = self.client.post(self.url)
        self.assertRedirects(response, self.detail)
        self.assertTrue(self.org.memberships.filter(user=self.outsider).exists())
        self.assertFalse(Invitation.objects.exists())

    def test_expired_invitation_is_refused(self):
        Invitation.objects.filter(pk=self.invitation.pk).update(
            created_at=timezone.now() - INVITATION_TTL - timedelta(minutes=1)
        )
        self.client.force_login(self.outsider)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 410)
        self.assertContains(response, "expired", status_code=410)
        self.assertFalse(self.org.memberships.filter(user=self.outsider).exists())

    def test_reinvite_rotates_token(self):
        self.client.force_login(self.owner)
        self.client.post(self.detail, {"email": "otto@example.com"})
        fresh = Invitation.objects.get(organization=self.org)
        self.assertNotEqual(fresh.token, self.invitation.token)
        self.client.force_login(self.outsider)
        self.assertEqual(self.client.post(self.url).status_code, 404)

    def test_other_account_cannot_use_token(self):
        self.client.force_login(make_user("eve"))
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.org.memberships.count(), 2)


class MembershipRemoveTests(OrgTestCase):
    def remove_url(self, membership):
        return reverse("membership_remove", args=[self.org.pk, membership.pk])

    def test_member_can_leave_but_not_remove_others(self):
        self.client.force_login(self.member)
        response = self.client.post(self.remove_url(self.owner_m))
        self.assertEqual(response.status_code, 403)
        self.client.post(self.remove_url(self.member_m))
        self.assertFalse(Membership.objects.filter(pk=self.member_m.pk).exists())

    def test_last_owner_cannot_leave(self):
        self.client.force_login(self.owner)
        self.client.post(self.remove_url(self.owner_m))
        self.assertTrue(Membership.objects.filter(pk=self.owner_m.pk).exists())

    def test_owner_deletes_org(self):
        self.client.force_login(self.member)
        delete = reverse("org_delete", args=[self.org.pk])
        self.assertEqual(self.client.post(delete).status_code, 403)
        self.client.force_login(self.owner)
        self.assertRedirects(self.client.post(delete), reverse("orgs"))
        self.assertFalse(Organization.objects.exists())


class ReleaseUserTests(OrgTestCase):
    def test_promotes_heir_and_deletes_solo_orgs(self):
        solo = Organization.objects.create(name="Solo")
        Membership.objects.create(organization=solo, user=self.owner, role=OWNER)
        release_user(self.owner)
        self.member_m.refresh_from_db()
        self.assertEqual(self.member_m.role, OWNER)
        self.assertFalse(Organization.objects.filter(pk=solo.pk).exists())


class MembershipRoleTests(OrgTestCase):
    def role_url(self, membership):
        return reverse("membership_role", args=[self.org.pk, membership.pk])

    def test_owner_promotes_and_demotes(self):
        self.client.force_login(self.owner)
        self.client.post(self.role_url(self.member_m), {"role": "owner"})
        self.member_m.refresh_from_db()
        self.assertEqual(self.member_m.role, OWNER)
        self.client.post(self.role_url(self.owner_m), {"role": "member"})
        self.owner_m.refresh_from_db()
        self.assertEqual(self.owner_m.role, MEMBER)

    def test_member_cannot_change_roles(self):
        self.client.force_login(self.member)
        response = self.client.post(self.role_url(self.member_m), {"role": "owner"})
        self.assertEqual(response.status_code, 403)
        self.member_m.refresh_from_db()
        self.assertEqual(self.member_m.role, MEMBER)

    def test_last_owner_cannot_be_demoted(self):
        self.client.force_login(self.owner)
        self.client.post(self.role_url(self.owner_m), {"role": "member"})
        self.owner_m.refresh_from_db()
        self.assertEqual(self.owner_m.role, OWNER)

    def test_unknown_role_is_ignored(self):
        self.client.force_login(self.owner)
        self.client.post(self.role_url(self.member_m), {"role": "admin"})
        self.member_m.refresh_from_db()
        self.assertEqual(self.member_m.role, MEMBER)
