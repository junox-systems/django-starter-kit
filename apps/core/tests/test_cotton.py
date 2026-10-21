from django.test import TestCase
from django.urls import reverse

from apps.orgs.models import Organization
from apps.users.models import User


class CottonPagesTests(TestCase):
    """Every page built from Cotton components renders, with no <c-*> tag left uncompiled."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="dana@example.com", username="dana", password="s3cret-pw"
        )

    def assertCompiled(self, url):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "<c-")
        return response

    def test_public_pages(self):
        for name in ("home", "account_login", "account_signup", "account_inactive"):
            with self.subTest(name=name):
                self.assertCompiled(reverse(name))

    def test_app_pages(self):
        self.client.force_login(self.user)
        self.client.post(reverse("orgs"), {"name": "Acme"})
        org = Organization.objects.get(name="Acme")
        for url in (
            reverse("profile"),
            reverse("delete_account"),
            reverse("orgs"),
            reverse("org_detail", args=[org.pk]),
            reverse("account_email"),
            reverse("mfa_index"),
        ):
            with self.subTest(url=url):
                self.assertCompiled(url)

    def test_form_errors_render_through_fields_component(self):
        response = self.client.post(
            reverse("account_login"), {"login": "dana@example.com", "password": "wrong"}
        )
        self.assertContains(response, 'data-variant="destructive" role="alert"')
        self.assertContains(response, 'name="csrfmiddlewaretoken"')
