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
