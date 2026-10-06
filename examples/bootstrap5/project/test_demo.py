import importlib
import os
import sys
from unittest import mock

from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

DEMO_ENV = {"SECRET_KEY": "test-secret", "RENDER_EXTERNAL_HOSTNAME": "demo.example.org"}


def load_demo_settings(env):
    sys.modules.pop("project.settings_demo", None)
    with mock.patch.dict(os.environ, env, clear=False):
        for name in {"SECRET_KEY", "RENDER_EXTERNAL_HOSTNAME"} - env.keys():
            os.environ.pop(name, None)
        return importlib.import_module("project.settings_demo")


class DemoSettingsTest(SimpleTestCase):
    def test_hardened_values(self):
        demo = load_demo_settings(DEMO_ENV)
        self.assertFalse(demo.DEBUG)
        self.assertEqual(demo.SECRET_KEY, "test-secret")
        self.assertEqual(demo.ALLOWED_HOSTS, ["demo.example.org"])
        self.assertEqual(demo.CSRF_TRUSTED_ORIGINS, ["https://demo.example.org"])
        self.assertTrue(demo.SESSION_COOKIE_SECURE)
        self.assertTrue(demo.CSRF_COOKIE_SECURE)
        self.assertTrue(demo.DEMO_MODE)
        self.assertEqual(demo.DEMO_WRITE_RATES, ("30/m", "300/d"))
        self.assertEqual(demo.ROOT_URLCONF, "project.urls_demo")

    def test_middleware_order(self):
        demo = load_demo_settings(DEMO_ENV)
        self.assertEqual(demo.MIDDLEWARE[0], "django.middleware.security.SecurityMiddleware")
        self.assertEqual(demo.MIDDLEWARE[1], "whitenoise.middleware.WhiteNoiseMiddleware")
        self.assertEqual(demo.MIDDLEWARE[-2], "project.boot.BootIdMiddleware")
        self.assertEqual(demo.MIDDLEWARE[-1], "project.ratelimit.WriteRateLimitMiddleware")

    def test_base_middleware_is_not_mutated(self):
        from project import settings as base

        load_demo_settings(DEMO_ENV)
        self.assertNotIn("whitenoise.middleware.WhiteNoiseMiddleware", base.MIDDLEWARE)
        self.assertNotIn("project.ratelimit.WriteRateLimitMiddleware", base.MIDDLEWARE)
        self.assertFalse(base.DEMO_MODE)

    def test_missing_secret_key_fails(self):
        with self.assertRaises(KeyError):
            load_demo_settings({"RENDER_EXTERNAL_HOSTNAME": "demo.example.org"})

    def test_missing_hostname_allows_no_host(self):
        demo = load_demo_settings({"SECRET_KEY": "test-secret"})
        self.assertEqual(demo.ALLOWED_HOSTS, [])
        self.assertEqual(demo.CSRF_TRUSTED_ORIGINS, [])


class DemoUrlsTest(TestCase):
    def test_admin_mounted_locally(self):
        self.assertEqual(self.client.get("/admin/").status_code, 302)  # redirect to the admin login

    @override_settings(ROOT_URLCONF="project.urls_demo")
    def test_admin_not_mounted_on_demo(self):
        self.assertEqual(self.client.get("/admin/").status_code, 404)

    @override_settings(ROOT_URLCONF="project.urls_demo")
    def test_rest_of_site_still_routed(self):
        self.assertEqual(self.client.get(reverse("login")).status_code, 200)
        self.assertEqual(self.client.get(reverse("home")).status_code, 200)


class DemoBannerTest(TestCase):
    def test_no_banner_locally(self):
        self.assertNotContains(self.client.get(reverse("home")), 'id="demo-banner"')

    @override_settings(DEMO_MODE=True)
    def test_banner_on_demo(self):
        resp = self.client.get(reverse("login"))
        self.assertContains(resp, 'id="demo-banner"')
        self.assertContains(resp, "resets daily")
