import os
import subprocess
import sys

from django.conf import settings
from django.test import SimpleTestCase


def load_settings(module, expr="s.AWS_S3_CUSTOM_DOMAIN", **env):
    """Import a settings module in a fresh interpreter; settings are module-level."""
    return subprocess.run(
        [sys.executable, "-c", f"import {module} as s; print({expr})"],
        cwd=settings.BASE_DIR,
        env={**os.environ, **env},
        capture_output=True,
        text=True,
    )


class ProductionSecretKeyTests(SimpleTestCase):
    def test_refuses_dev_default_key(self):
        result = load_settings(
            "config.settings.production", SECRET_KEY="django-insecure-whatever"
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SECRET_KEY must be set in production", result.stderr)

    def test_accepts_real_key(self):
        result = load_settings(
            "config.settings.production",
            SECRET_KEY="a-real-key",
            DEFAULT_FROM_EMAIL="hello@example.com",
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_requires_from_email(self):
        env = {k: v for k, v in os.environ.items() if k != "DEFAULT_FROM_EMAIL"}
        result = subprocess.run(
            [sys.executable, "-c", "import config.settings.production"],
            cwd=settings.BASE_DIR,
            env={**env, "SECRET_KEY": "a-real-key"},
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DEFAULT_FROM_EMAIL", result.stderr)


class S3CustomDomainTests(SimpleTestCase):
    def test_custom_endpoint_drops_amazonaws_domain(self):
        result = load_settings(
            "config.settings.base",
            AWS_S3_ENDPOINT_URL="http://s3:9000",
            AWS_STORAGE_BUCKET_NAME="media",
        )
        self.assertEqual(result.stdout.strip(), "None", result.stderr)

    def test_real_aws_uses_bucket_domain(self):
        result = load_settings(
            "config.settings.base",
            AWS_S3_ENDPOINT_URL="",
            AWS_STORAGE_BUCKET_NAME="media",
        )
        self.assertEqual(result.stdout.strip(), "media.s3.amazonaws.com", result.stderr)


class EmailBackendTests(SimpleTestCase):
    expr = "s.EMAIL_BACKEND, getattr(s, 'EMAIL_HOST', None)"

    def test_resend_key_selects_resend(self):
        result = load_settings(
            "config.settings.base", self.expr, RESEND_API_KEY="re_x", EMAIL_URL=""
        )
        self.assertIn(
            "anymail.backends.resend.EmailBackend", result.stdout, result.stderr
        )

    def test_email_url_configures_smtp(self):
        result = load_settings(
            "config.settings.base",
            self.expr,
            RESEND_API_KEY="",
            EMAIL_URL="smtp+tls://u:p@smtp.example.com:587",
        )
        self.assertEqual(
            result.stdout.strip(),
            "django.core.mail.backends.smtp.EmailBackend smtp.example.com",
            result.stderr,
        )

    def test_empty_email_url_falls_back_to_localhost(self):
        result = load_settings(
            "config.settings.base", self.expr, RESEND_API_KEY="", EMAIL_URL=""
        )
        self.assertEqual(
            result.stdout.strip(),
            "django.core.mail.backends.smtp.EmailBackend localhost",
            result.stderr,
        )
