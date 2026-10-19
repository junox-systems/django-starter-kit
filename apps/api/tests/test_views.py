from django.test import TestCase
from django.urls import reverse

from apps.users.models import User


class UserAPIAccessTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="alice@example.com", username="alice", password="s3cret-pw"
        )
        self.other = User.objects.create_user(
            email="bob@example.com", username="bob", password="s3cret-pw"
        )
        self.staff = User.objects.create_user(
            email="staff@example.com",
            username="staff",
            password="s3cret-pw",
            is_staff=True,
        )

    def test_list_forbidden_for_non_staff(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("user-list"))
        self.assertEqual(response.status_code, 403)

    def test_list_allowed_for_staff(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("user-list"))
        self.assertEqual(response.status_code, 200)
        emails = {u["email"] for u in response.json()}
        self.assertTrue({"alice@example.com", "bob@example.com"} <= emails)

    def test_detail_allowed_for_self(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("user-detail", args=[self.user.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["email"], "alice@example.com")

    def test_detail_hides_other_users(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("user-detail", args=[self.other.id]))
        self.assertEqual(response.status_code, 404)

    def test_detail_allowed_for_staff(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("user-detail", args=[self.other.id]))
        self.assertEqual(response.status_code, 200)
