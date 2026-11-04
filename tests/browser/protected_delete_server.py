"""Owned, single-threaded HTTP fixture for protected-blocker navigation."""

# ruff: noqa: E402 -- configure the isolated test project before model imports.
import copy
import hashlib
import json
import os
import re
import signal
import subprocess
import sys
import tempfile
from contextlib import ExitStack
from contextvars import ContextVar
from pathlib import Path
from unittest.mock import patch
from wsgiref.simple_server import make_server

from tests.test1.conftest import pytest_configure

pytest_configure()

import django
from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.models import Permission, User
from django.contrib.staticfiles.handlers import StaticFilesHandler
from django.core.management import call_command
from django.core.wsgi import get_wsgi_application
from django.db import connection
from django.http import HttpResponse, JsonResponse
from django.template.loaders.locmem import Loader
from django.test import override_settings
from django.urls import include, path

import crud_views
from tests.test1.app.models import Contract, Publisher
from tests.test1.app.views import ContractDetailView, PublisherCascadeDeleteView, PublisherModalProtectedDeleteView

ROOT = Path(__file__).resolve().parents[2]
assert Path(crud_views.__file__).resolve().is_relative_to(ROOT / "src"), "Refuse installed wheel"
CUSTOM = ContextVar("protected_custom", default=False)
PAYLOAD = '"quoted" & <img src=x onerror=alert(1)> — Zürich'
SOURCES = [PublisherCascadeDeleteView, PublisherModalProtectedDeleteView]


def recipes():
    source = (ROOT / "docs/migrating-1.0.md").read_bytes().decode("utf-8")
    assert "\r" not in source, "Recipes require LF newlines"
    bodies = {}
    for name in ("content", "related", "body"):
        marker = f"<!-- protected-delete-recipe: {name} -->"
        assert source.count(marker) == 1, f"Expected exactly one {name} marker"
        matches = re.findall(rf"^{re.escape(marker)}\n```django\n(.*?)^```$", source, re.M | re.S)
        assert len(matches) == 1, f"Expected adjacent django fence for {name}"
        bodies[name] = matches[0]
    return bodies


BODIES = recipes()
HASHES = {name: hashlib.sha256(body.encode()).hexdigest() for name, body in BODIES.items()}


def source_hashes():
    files = subprocess.check_output(
        ["git", "ls-files", "src", "tests/test1", "docs/migrating-1.0.md"], cwd=ROOT, text=True
    ).splitlines()
    files += [
        "tests/browser/protected-delete.cjs",
        "tests/browser/protected_delete_server.py",
        "tests/browser/protected-delete.test.cjs",
        "tests/browser/cancel-navigation.cjs",
    ]
    return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in sorted(set(files))}


class CustomLoader(Loader):
    def get_template_sources(self, template_name):
        if CUSTOM.get():
            yield from super().get_template_sources(template_name)


class FixtureMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        custom = request.COOKIES.get("protected_mode") == "custom"
        scenario = request.COOKIES.get("protected_scenario", "normal")
        token = CUSTOM.set(custom)
        try:
            with ExitStack() as stack:
                for cls in SOURCES:
                    original_filter = cls.cv_filter_related_objects

                    def filtered(self, user, related, original=original_filter):
                        visible = original(self, user, related)
                        return visible._replace(
                            protected=[obj for obj in visible.protected if obj.pk != hidden.pk and scenario != "hidden"]
                        )

                    values = {
                        "cv_show_related_objects": scenario != "preview-off",
                        "cv_link_related_objects": scenario != "link-off",
                        "cv_filter_related_objects": filtered,
                        "cv_check_delete_protection": lambda self: [],
                    }
                    if custom:
                        values["cv_content_template"] = "myapp/delete.content.html"
                    for name, value in values.items():
                        stack.enter_context(patch.object(cls, name, value))
                stack.enter_context(patch.object(ContractDetailView, "cv_modal", True))
                original_queryset = ContractDetailView.get_queryset
                stack.enter_context(
                    patch.object(
                        ContractDetailView,
                        "get_queryset",
                        lambda self: original_queryset(self).exclude(pk=denied.pk),
                    )
                )
                response = self.get_response(request)
                if hasattr(response, "render"):
                    response.render()
                response["X-Protected-Mode"] = "custom" if custom else "stock"
                response["X-Protected-Detail-Modal-Capable"] = "true"
                return response
        finally:
            CUSTOM.reset(token)


def signin(request):
    login(request, actor, backend="django.contrib.auth.backends.ModelBackend")
    return JsonResponse(
        {
            "publisher": publisher.pk,
            "allowed": allowed.pk,
            "allowedLabel": str(allowed),
            "denied": denied.pk,
            "deniedLabel": str(denied),
            "hidden": hidden.pk,
            "hiddenLabel": str(hidden),
            "payload": PAYLOAD,
            "detailPaths": {
                name: PublisherCascadeDeleteView().cv_get_related_object_url(obj)
                for name, obj in (("allowed", allowed), ("denied", denied), ("hidden", hidden))
            },
        }
    )


urlpatterns = [
    path("__signin/", signin),
    path("favicon.ico", lambda request: HttpResponse(status=204)),
    path("", include("tests.test1.project.urls")),
]


def main():
    global actor, publisher, allowed, denied, hidden
    with tempfile.TemporaryDirectory(prefix="cv-protected-") as temporary:
        settings.DATABASES["default"]["NAME"] = str(Path(temporary) / "db.sqlite3")
        settings.MEDIA_ROOT = str(Path(temporary) / "media")
        templates = copy.deepcopy(settings.TEMPLATES)
        templates[0]["APP_DIRS"] = False
        templates[0]["OPTIONS"]["loaders"] = [
            (
                "__main__.CustomLoader",
                {
                    "myapp/delete.content.html": BODIES["content"],
                    "myapp/delete_related.html": BODIES["related"],
                    "myapp/delete_protected.html": BODIES["body"],
                },
            ),
            "django.template.loaders.filesystem.Loader",
            "django.template.loaders.app_directories.Loader",
        ]
        with override_settings(
            TEMPLATES=templates,
            ROOT_URLCONF=__name__,
            ALLOWED_HOSTS=["127.0.0.1"],
            MIDDLEWARE=[*settings.MIDDLEWARE, "__main__.FixtureMiddleware"],
        ):
            try:
                call_command("migrate", run_syncdb=True, verbosity=0)
                actor = User.objects.create_user(username="protected-browser", password=None)
                actor.user_permissions.add(
                    *Permission.objects.filter(codename__in=["view_publisher", "delete_publisher", "view_contract"])
                )
                publisher = Publisher.objects.create(name="Browser Publisher")
                allowed = Contract.objects.create(publisher=publisher, title=PAYLOAD)
                denied = Contract.objects.create(publisher=publisher, title="Visible denied blocker")
                hidden = Contract.objects.create(publisher=publisher, title="Secret hidden blocker")
                with make_server("127.0.0.1", 0, StaticFilesHandler(get_wsgi_application())) as server:

                    def stop(signum, frame):
                        raise SystemExit(0)

                    signal.signal(signal.SIGTERM, stop)
                    print(
                        json.dumps(
                            {
                                "ready": server.server_port,
                                "database": temporary,
                                "pid": os.getpid(),
                                "recipeHashes": HASHES,
                                "sourceHashes": source_hashes(),
                                "runtime": {
                                    "python": sys.version,
                                    "pythonPath": sys.executable,
                                    "django": django.get_version(),
                                    "packagePath": crud_views.__file__,
                                },
                            }
                        ),
                        flush=True,
                    )
                    server.serve_forever()
            finally:
                connection.close()


if __name__ == "__main__":
    main()
