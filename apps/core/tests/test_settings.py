import os
import subprocess
import sys

from django.conf import settings
from django.test import SimpleTestCase


def load_settings(module, **env):
    """Import a settings module in a fresh interpreter; settings are module-level."""
    return subprocess.run(
        [
            sys.executable,
            "-c",
            f"import {module} as s; print(s.AWS_S3_CUSTOM_DOMAIN)",
        ],
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
        result = load_settings("config.settings.production", SECRET_KEY="a-real-key")
        self.assertEqual(result.returncode, 0, result.stderr)


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
