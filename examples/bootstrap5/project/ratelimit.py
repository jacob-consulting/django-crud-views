"""Per-client-IP rate limit on writes for the public demo. Installed by ``settings_demo`` only."""

from django.conf import settings
from django.http import HttpRequest
from django.shortcuts import render
from django.urls import reverse
from django_ratelimit.core import is_ratelimited

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def client_ip(request: HttpRequest) -> str:
    """The visitor's IP address.

    On Render, Cloudflare and Render's proxy both append to X-Forwarded-For: its left entries are client-controlled
    and its right entry is an internal address shared by every visitor. Render sets True-Client-IP to the real
    client address and overwrites a client-sent one. REMOTE_ADDR covers local runs and tests.
    """
    return request.META.get("HTTP_TRUE_CLIENT_IP") or request.META.get("REMOTE_ADDR", "")


def _key(group, request):
    return client_ip(request)


class WriteRateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # logout is a POST since Django 5; a limited visitor must still be able to leave
        exempt = request.path == reverse("logout")
        if request.method not in SAFE_METHODS and not exempt and self._limited(request):
            return render(request, "project/429.html", status=429)
        return self.get_response(request)

    @staticmethod
    def _limited(request) -> bool:
        return any(
            is_ratelimited(request, group=f"demo-writes-{rate}", key=_key, rate=rate, increment=True)
            for rate in settings.DEMO_WRITE_RATES
        )
