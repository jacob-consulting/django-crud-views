from unittest import mock

from django.core.cache import cache
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from project.ratelimit import client_ip
from project.settings import MIDDLEWARE as BASE_MIDDLEWARE

RATELIMITED_MIDDLEWARE = [*BASE_MIDDLEWARE, "project.ratelimit.WriteRateLimitMiddleware"]
FIXED_NOW = 1_700_000_000  # pin django-ratelimit's window so a test never straddles a minute boundary


class ClientIpTest(SimpleTestCase):
    def test_prefers_true_client_ip(self):
        request = RequestFactory().get("/", HTTP_TRUE_CLIENT_IP="203.0.113.7", REMOTE_ADDR="10.0.0.1")
        self.assertEqual(client_ip(request), "203.0.113.7")

    def test_falls_back_to_remote_addr(self):
        request = RequestFactory().get("/", REMOTE_ADDR="198.51.100.2")
        self.assertEqual(client_ip(request), "198.51.100.2")

    def test_ignores_x_forwarded_for(self):
        request = RequestFactory().get("/", HTTP_X_FORWARDED_FOR="1.2.3.4", REMOTE_ADDR="198.51.100.2")
        self.assertEqual(client_ip(request), "198.51.100.2")


# a failed login still runs the password hasher; MD5 keeps ~100 logins per test fast
@override_settings(
    MIDDLEWARE=RATELIMITED_MIDDLEWARE,
    DEMO_WRITE_RATES=("30/m", "300/d"),
    PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
)
@mock.patch("django_ratelimit.core.time.time", return_value=FIXED_NOW)
class WriteRateLimitTest(TestCase):
    def setUp(self):
        cache.clear()
        self.url = reverse("login")

    def post(self, ip, **extra):
        return self.client.post(self.url, {"username": "x", "password": "y"}, HTTP_TRUE_CLIENT_IP=ip, **extra)

    def test_31st_write_in_a_minute_is_429(self, _time):
        for i in range(30):
            self.assertEqual(self.post("203.0.113.7").status_code, 200, f"write {i + 1}")
        resp = self.post("203.0.113.7")
        self.assertEqual(resp.status_code, 429)
        self.assertContains(resp, "Too many changes", status_code=429)

    def test_get_is_never_limited(self, _time):
        for _ in range(31):
            self.post("203.0.113.7")
        self.assertEqual(self.client.get(self.url, HTTP_TRUE_CLIENT_IP="203.0.113.7").status_code, 200)

    def test_other_client_ip_is_unaffected(self, _time):
        for _ in range(31):
            self.post("203.0.113.7")
        self.assertEqual(self.post("203.0.113.8").status_code, 200)

    def test_rotating_x_forwarded_for_does_not_escape_the_limit(self, _time):
        for i in range(30):
            self.post("203.0.113.7", HTTP_X_FORWARDED_FOR=f"10.9.9.{i}")
        self.assertEqual(self.post("203.0.113.7", HTTP_X_FORWARDED_FOR="10.9.9.250").status_code, 429)

    def test_logout_is_never_limited(self, _time):
        for _ in range(31):
            self.post("203.0.113.7")
        resp = self.client.post(reverse("logout"), HTTP_TRUE_CLIENT_IP="203.0.113.7")
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(self.post("203.0.113.7").status_code, 429)  # other writes stay limited

    @override_settings(DEMO_WRITE_RATES=("1000/m", "5/d"))
    def test_daily_limit_applies(self, _time):
        for _ in range(5):
            self.assertEqual(self.post("203.0.113.7").status_code, 200)
        self.assertEqual(self.post("203.0.113.7").status_code, 429)
