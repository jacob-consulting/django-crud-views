from django.test import TestCase, override_settings
from django.urls import reverse

from project.settings import MIDDLEWARE as BASE_MIDDLEWARE

BOOT_MIDDLEWARE = [*BASE_MIDDLEWARE, "project.boot.BootIdMiddleware"]


class BootIdTest(TestCase):
    """The reset workflow tells a restarted demo instance from the old one by this header."""

    def test_no_header_locally(self):
        self.assertNotIn("X-Demo-Boot", self.client.get(reverse("login")).headers)

    @override_settings(MIDDLEWARE=BOOT_MIDDLEWARE)
    def test_header_is_a_stable_process_id(self):
        first = self.client.get(reverse("login")).headers["X-Demo-Boot"]
        second = self.client.get(reverse("home")).headers["X-Demo-Boot"]
        self.assertEqual(first, second)
        self.assertRegex(first, r"^[0-9a-f]{32}$")

    @override_settings(MIDDLEWARE=BOOT_MIDDLEWARE)
    def test_header_on_error_responses_too(self):
        self.assertIn("X-Demo-Boot", self.client.get("/no-such-page/").headers)
