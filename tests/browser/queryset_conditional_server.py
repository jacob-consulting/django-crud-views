"""Real example URLs on loopback with a runner-owned disposable SQLite/media directory.

Fixture endpoints require an authenticated superuser, loopback and the per-run secret.
All POSTs retain Django CSRF middleware. Never opens the developer database.
"""

# ruff: noqa: E402
import importlib
import json
import os
import platform
import sys
from pathlib import Path
from wsgiref.simple_server import make_server

import django

UPSTREAM = Path(os.environ["CV_QUERYSET_UPSTREAM"]).resolve()
TEMP = Path(os.environ["CV_QUERYSET_TEMP"]).resolve()
assert TEMP.name.startswith("cv-queryset-") and TEMP.is_dir()
os.environ["DJANGO_SETTINGS_MODULE"] = "project.settings"
from django.conf import settings

assert Path(importlib.import_module("project.settings").__file__).resolve() == (
    UPSTREAM / "examples/bootstrap5/project/settings.py"
)
settings.DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": str(TEMP / "db.sqlite3")}}
settings.MEDIA_ROOT = TEMP / "media"
settings.ALLOWED_HOSTS = ["127.0.0.1"]
settings.ROOT_URLCONF = __name__
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.staticfiles.handlers import StaticFilesHandler
from django.core.management import call_command
from django.core.wsgi import get_wsgi_application
from django.http import HttpResponseForbidden, JsonResponse
from django.urls import include, path, reverse
from queryset_conditional.models import RequestBatch, Service, ServiceCategory, ServiceRequest
from queryset_conditional.seed import seed

import crud_views

assert Path(crud_views.__file__).resolve() == UPSTREAM / "src/crud_views/__init__.py"
call_command("migrate", verbosity=0, interactive=False)
User = get_user_model()
User.objects.create_superuser(username="browser", password="browser-only-password", email="")
for name in ("alice", "bob"):
    User.objects.create_user(username=name)
seed()
services = {s.name: s.pk for s in Service.objects.all()}
fixtures = {}
for name in ("ordinary", "compact", "mutation", "unchanged"):
    batch = RequestBatch.objects.create(title=f"Browser {name}")
    for service, address, meeting in (
        ("Boiler inspection", "Original address", ""),
        ("Technical consultation", "", "https://example.com/original"),
    ):
        ServiceRequest.objects.create(
            batch=batch, service_id=services[service], visit_address=address, meeting_url=meeting
        )
    fixtures[name] = batch.pk


@login_required
def state(request):
    if (
        request.META.get("REMOTE_ADDR") != "127.0.0.1"
        or not request.user.is_superuser
        or request.headers.get("X-Fixture-Key") != os.environ["CV_QUERYSET_SECRET"]
    ):
        return HttpResponseForbidden()
    if request.method == "POST":
        data = json.loads(request.body)
        if data["operation"] == "category":
            # Only existing fixture category codes; restore with the captured original value.
            ServiceCategory.objects.filter(pk=data["pk"]).update(code=data["code"])
        elif data["operation"] == "stale":
            ServiceRequest.objects.filter(batch_id=fixtures["unchanged"]).update(
                service_id=services["Document review"], visit_address="stale", meeting_url="https://example.com/stale"
            )
        else:
            return HttpResponseForbidden()
    standalone = ServiceRequest.objects.get(batch=None)
    return JsonResponse(
        {
            "runtime": {
                "python": platform.python_version(),
                "django": django.get_version(),
                "pythonPath": sys.executable,
                "settings": "project.settings",
                "source": str(Path(crud_views.__file__).resolve()),
            },
            "urls": {
                "standalone": reverse("service_request-update", kwargs={"pk": standalone.pk}),
                "create": reverse("service_request-create"),
                **{
                    name: reverse(
                        "service_batch_compact-update" if name != "ordinary" else "service_batch-update",
                        kwargs={"pk": pk},
                    )
                    for name, pk in fixtures.items()
                },
            },
            "services": services,
            "fixtures": fixtures,
            "categories": list(ServiceCategory.objects.order_by("pk").values()),
            "requests": list(ServiceRequest.objects.order_by("pk").values()),
            "batches": list(RequestBatch.objects.order_by("pk").values()),
        }
    )


urlpatterns = [path("__fixture__/state/", state), path("", include("project.urls"))]
with make_server("127.0.0.1", 0, StaticFilesHandler(get_wsgi_application())) as server:
    print(json.dumps({"port": server.server_port, "temporary": str(TEMP)}), flush=True)
    server.serve_forever()
