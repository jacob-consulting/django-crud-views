"""Owned loopback fixture: current source, disposable database, real existing ViewSets."""

# ruff: noqa: E402 -- configure the existing isolated test project before model imports.
import hashlib
import json
import os
import signal
import sys
import tempfile
from pathlib import Path
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
from django.template import Context, Template
from django.test import override_settings
from django.urls import include, path, reverse

import crud_views
from tests.test1.app.models import Author, Book, Publisher
from tests.test1.app.views import AuthorModalListView, cv_publisher

ROOT = Path(__file__).resolve().parents[2]
assert Path(crud_views.__file__).resolve().is_relative_to(ROOT / "src"), "Refuse installed wheel"
temporary = tempfile.TemporaryDirectory(prefix="cv-cancel-")
settings.DATABASES["default"]["NAME"] = str(Path(temporary.name) / "db.sqlite3")
settings.MEDIA_ROOT = str(Path(temporary.name) / "media")
settings.ALLOWED_HOSTS = ["127.0.0.1"]
settings.ROOT_URLCONF = __name__
settings.MIDDLEWARE += ["__main__.AuditMiddleware"]
requests = []


class AuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        writes = []

        def observe(execute, sql, params, many, context):
            if sql.lstrip().split()[0].upper() in {"INSERT", "UPDATE", "DELETE", "REPLACE"} and '"app_' in sql:
                writes.append(sql.split("VALUES")[0])
            return execute(sql, params, many, context)

        with (
            connection.execute_wrapper(observe),
            override_settings(
                CRUD_VIEWS_BUTTON_CLASSES={"form:cancel-tag": request.COOKIES.get("cancel_tag", "button")}
            ),
        ):
            response = self.get_response(request)
            context = getattr(response, "context_data", {}) or {}
            if "form" in context and "view" in context:
                # Real copied-template recipe, independently rendered using the same public helper.
                response["X-Cancel-Copy"] = (
                    Template(
                        "{% load crud_views %}{% cv_cancel_url as url %}{% if url %}"
                        '<a href="{{ url }}">Cancel</a>{% endif %}'
                    )
                    .render(Context({"view": context["view"], "request": request}))
                    .encode()
                    .decode()
                )
        if not request.path.startswith("/__") and not request.path.startswith("/static/"):
            requests.append(
                {
                    "method": request.method,
                    "path": request.get_full_path(),
                    "status": response.status_code,
                    "writes": writes,
                }
            )
        return response


call_command("migrate", run_syncdb=True, verbosity=0)
actor = User.objects.create_superuser(username="cancel-browser", password=None, email="")
limited = User.objects.create_user(username="cancel-change-only", password=None)
limited.user_permissions.add(Permission.objects.get(codename="change_publisher", content_type__app_label="app"))
publisher = Publisher.objects.create(name="Alpha")
other_parent = Publisher.objects.create(name="Beta")
book = Book.objects.create(title="Nested", publisher=publisher)
other_book = Book.objects.create(title="Other", publisher=other_parent)
author = Author.objects.create(first_name="Browser", last_name="Author")
protected = Author.objects.create(first_name="Protected", last_name="Author", pseudonym="protected")
# Expose the already supported custom modal through the fixture's real row-action renderer.
AuthorModalListView.cv_list_actions = ["detail", "delete", "contact"]
# Parent context buttons use the ViewSet's icon; the unit fixtures normally supply it.
cv_publisher.icon_header = "fa-solid fa-book"


def signin(request):
    login(
        request,
        limited if request.GET.get("limited") == "1" else actor,
        backend="django.contrib.auth.backends.ModelBackend",
    )
    return JsonResponse(
        {
            "publisher": publisher.pk,
            "author": str(author.pk),
            "protected": str(protected.pk),
            "book": book.pk,
            "book_list": reverse("book-list", kwargs={"publisher_pk": publisher.pk}),
            "book_update": reverse("book-update", kwargs={"publisher_pk": publisher.pk, "pk": book.pk}),
            "other_book_list": reverse("book-list", kwargs={"publisher_pk": other_parent.pk}),
            "other_book_update": reverse("book-update", kwargs={"publisher_pk": other_parent.pk, "pk": other_book.pk}),
        }
    )


def snapshot(request):
    return JsonResponse(
        {
            "rows": {
                model.__name__: list(model.objects.order_by("pk").values()) for model in (Publisher, Author, Book)
            },
            "requests": requests,
        }
    )


urlpatterns = [
    path("__signin/", signin),
    path("__snapshot/", snapshot),
    path("favicon.ico", lambda request: HttpResponse(status=204)),
    path("", include("tests.test1.project.urls")),
]


def main():
    try:
        with make_server("127.0.0.1", 0, StaticFilesHandler(get_wsgi_application())) as server:

            def stop(signum, frame):
                raise SystemExit(0)

            signal.signal(signal.SIGTERM, stop)
            print(
                json.dumps(
                    {
                        "ready": server.server_port,
                        "database": str(temporary.name),
                        "runtime": {
                            "python": sys.version,
                            "django": django.get_version(),
                            "packagePath": crud_views.__file__,
                            "pythonPath": sys.executable,
                        },
                        "pid": os.getpid(),
                        "server_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    }
                ),
                flush=True,
            )
            server.serve_forever()
    finally:
        connection.close()
        temporary.cleanup()


if __name__ == "__main__":
    main()
