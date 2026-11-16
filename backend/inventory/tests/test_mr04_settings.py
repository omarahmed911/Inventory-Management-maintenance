from django.test import TestCase
from django.conf import settings
import subprocess
import sys


class MR04SettingsTests(TestCase):
    def test_poke_removed_from_cors_methods(self):
        self.assertNotIn("POKE", settings.CORS_ALLOW_METHODS)

    def test_allowed_hosts_configured(self):
        self.assertTrue(len(settings.ALLOWED_HOSTS) > 0)
        self.assertTrue(any(h in settings.ALLOWED_HOSTS for h in ["testserver", "localhost", "127.0.0.1", "*"]))

    def test_production_env_enables_secure_flags(self):
        code = (
            "import os, sys\n"
            "os.environ['DEBUG'] = 'False'\n"
            "os.environ['DJANGO_SETTINGS_MODULE'] = 'inventory_system.settings'\n"
            "import django\n"
            "django.setup()\n"
            "from django.conf import settings\n"
            "assert settings.DEBUG is False, 'DEBUG should be False'\n"
            "assert settings.SESSION_COOKIE_SECURE is True, 'SESSION_COOKIE_SECURE should be True'\n"
            "assert settings.CSRF_COOKIE_SECURE is True, 'CSRF_COOKIE_SECURE should be True'\n"
            "assert 'POKE' not in settings.CORS_ALLOW_METHODS, 'POKE should not be in CORS_ALLOW_METHODS'\n"
        )
        proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd="backend")
        self.assertEqual(proc.returncode, 0, f"STDOUT: {proc.stdout}\nSTDERR: {proc.stderr}")
