"""Disposable loopback fixture host; run with checkout imports and the cached Django 6.0 Python.

Not a product endpoint. Uses only a new temporary SQLite database; never points at an application database.
The custom BookNote handler is genuine unknown metadata, not a substituted inspection result.
"""

# ruff: noqa: E402 -- Django must be configured before importing app models/views.

import json
import tempfile
from pathlib import Path
from wsgiref.simple_server import make_server

from tests.test1.conftest import pytest_configure

pytest_configure()
from django.conf import settings

temporary = tempfile.TemporaryDirectory(prefix="dcv-063-review-")
settings.DATABASES["default"]["NAME"] = str(Path(temporary.name) / "db.sqlite3")
settings.ALLOWED_HOSTS = ["127.0.0.1", "localhost"]
settings.ROOT_URLCONF = __name__
from django.contrib.auth import login
from django.contrib.auth.models import Permission, User
from django.core.management import call_command
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.template import engines
from django.urls import include, path
from django.utils.translation import override
from django.views.decorators.csrf import csrf_exempt

from crud_views.lib.deletion import DeletePreviewContribution
from tests.test1.app.models import Book, BookNote, Contract, Publisher
from tests.test1.app.views import PublisherCascadeDeleteView

call_command("migrate", run_syncdb=True, verbosity=0)
events = []


def custom_notes(collector, field, rows, using):
    events.append({"kind": "custom_notes", "using": using})
    collector.collect(rows, source=field.remote_field.model, source_attr=field.name)


BookNote._meta.get_field("book").remote_field.on_delete = custom_notes
PublisherCascadeDeleteView.cv_modal = True


def partial_provider(self, boundaries, *, using):
    return [
        DeletePreviewContribution(
            boundary,
            deleted=tuple(BookNote.objects.using(using).filter(book_id__in=boundary.source_pks)),
            complete=False,
        )
        for boundary in boundaries
        if boundary.field_model is BookNote
    ]


PublisherCascadeDeleteView.cv_get_delete_preview = partial_provider
actor = User.objects.create_user(username="reviewer")
actor.user_permissions.add(
    *Permission.objects.filter(
        content_type__app_label="app",
        codename__in=["view_publisher", "delete_publisher", "view_book", "view_booknote"],
    )
)
cases = []
for language in ("en", "de"):
    for mode in ("partial", "blocked", "stale", "success"):
        root = Publisher.objects.create(name=f"{language} {mode} — München 東京")
        for i in range(2):
            book = Book.objects.create(publisher=root, title=f"{i} — München 東京 <escaped> — " + "Long label " * 8)
            BookNote.objects.create(book=book, note=f"Nested {i} — 雪 — " + "Readable nested text " * 5)
        if mode == "blocked":
            Contract.objects.create(publisher=root, title="HIDDEN-CONTRACT")
        cases.append(
            {"language": language, "mode": mode, "pk": root.pk, "url": f"/publisher_cascade/{root.pk}/delete/"}
        )


def signin(request):
    login(request, actor, backend="django.contrib.auth.backends.ModelBackend")
    return redirect("/harness/")


def harness(request):
    template = engines["django"].from_string(
        '{% extends "app/base.html" %}{% block content %}<h1>Phase 06.3 fixture review</h1>'
        '<a id="launch" data-cv-modal="true" href="{{ target }}">Open delete modal</a>{% endblock %}'
    )
    return HttpResponse(template.render({"target": request.GET.get("target", "/")}, request))


@csrf_exempt
def protect(request, pk):
    if request.method != "POST":
        return HttpResponse(status=405)
    Contract.objects.get_or_create(publisher_id=pk, title="HIDDEN-CONTRACT")
    return JsonResponse({"protected": True})


def state(request, pk):
    return JsonResponse({"exists": Publisher.objects.filter(pk=pk).exists(), "events": events})


urlpatterns = [
    path("signin/", signin),
    path("harness/", harness),
    path("cases/", lambda request: JsonResponse(cases, safe=False)),
    path("protect/<int:pk>/", protect),
    path("state/<int:pk>/", state),
    path("", include("tests.test1.project.urls")),
]
from django.contrib.staticfiles.handlers import StaticFilesHandler
from django.core.wsgi import get_wsgi_application

application = StaticFilesHandler(get_wsgi_application())


def localized(environ, start_response):
    with override("de" if "review_language=de" in environ.get("HTTP_COOKIE", "") else "en"):
        return application(environ, start_response)


print(json.dumps({"ready": "http://127.0.0.1:8143", "database": "disposable temporary SQLite"}), flush=True)
make_server("127.0.0.1", 8143, localized).serve_forever()
