"""Disposable authenticated loopback fixture for presentation acceptance."""

# ruff: noqa: E402 -- validate port before Django configuration and imports.
import os
import re

port_text = os.environ.get("CV_PRESENTATION_PORT", "8145")
if not re.fullmatch(r"[0-9]+", port_text) or not 1024 <= int(port_text) <= 65535 or int(port_text) in (8143, 8144):
    raise SystemExit("CV_PRESENTATION_PORT must be decimal 1024..65535; reserved ports: 8143, 8144")
PORT = int(port_text)

from tests.test1.conftest import pytest_configure

pytest_configure()

import json
import signal
import tempfile
from contextvars import ContextVar
from pathlib import Path
from unittest.mock import patch
from wsgiref.simple_server import make_server

import django
from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.staticfiles.handlers import StaticFilesHandler
from django.core.management import call_command
from django.core.wsgi import get_wsgi_application
from django.db import connection
from django.http import HttpResponse, JsonResponse
from django.template.loaders.locmem import Loader as MemoryLoader
from django.test import override_settings
from django.urls import path
from django.utils.translation import gettext_lazy, override

from crud_views.lib.settings import crud_views_settings
from crud_views.lib.view.base import cv_is_modal_request
from crud_views.lib.viewset import ViewSet
from crud_views_object_detail.lib.resolvers import ResolvedGroup, ResolvedProperty
from crud_views_object_detail.lib.views import ObjectDetailViewPermissionRequired
from tests.test1.app.models import Author

ROOT = Path(__file__).resolve().parents[2]
temporary = tempfile.TemporaryDirectory(prefix="dcv-presentation-")
settings.DATABASES["default"]["NAME"] = str(Path(temporary.name) / "db.sqlite3")
settings.MEDIA_ROOT = str(Path(temporary.name) / "media")
settings.ALLOWED_HOSTS = ["127.0.0.1"]
settings.ROOT_URLCONF = __name__
settings.TEMPLATES[0]["DIRS"] = [str(ROOT / "tests/browser/templates")]
settings.TEMPLATES[0]["APP_DIRS"] = False
native_theme = ContextVar("presentation_native", default=False)


class NativeLoader(MemoryLoader):
    """Native template overrides exist only inside the current request context."""

    def get_template_sources(self, template_name):
        if native_theme.get():
            yield from super().get_template_sources(template_name)


settings.TEMPLATES[0]["OPTIONS"]["loaders"] = [
    (
        "__main__.NativeLoader",
        {
            "crud_views_object_detail/layouts/native/group.html": '{% include "presentation/native.html" %}',
            "crud_views_object_detail/types/default/badge.html": (
                "<span class=\"status{% if prop.badge_color == 'brand-custom' %} status-brand{% endif %}"
                '{% if prop.badge_pill %} status-pill{% endif %}" data-color="{{ prop.badge_color }}" '
                'data-pill="{{ prop.badge_pill }}" data-value="{{ value }}" data-path="{{ prop.path }}" '
                'data-newline="{{ od_settings.property_text_newline }}">'
                "{% if prop.badge_label %}{{ prop.badge_label }}{% else %}{{ value }}{% endif %}</span>"
            ),
        },
    ),
    (
        "django.template.loaders.locmem.Loader",
        {
            "presentation/content.html": '{% include "crud_views_object_detail/view_detail.content.html" %}'
            '<button id="modal-after-tabs">After tabs</button>',
        },
    ),
    "django.template.loaders.filesystem.Loader",
    "django.template.loaders.app_directories.Loader",
]
settings.CRUD_VIEWS_ICON_LIBRARIES = {"host": {"renderer": "font", "placement": "host", "class": "fa-solid fa-{name}"}}
settings.CRUD_VIEWS_ICONS = {"presentation-disabled": None}
call_command("migrate", run_syncdb=True, verbosity=0)
actor = User.objects.create_superuser(username="presentation-browser", password=None, email="")
HOSTILE = '<script>window.presentationAttack=1</script> & "value"'
author = Author.objects.create(first_name=HOSTILE, last_name="Author")
cv_presentation = ViewSet(model=Author, name="presentation", namespace=None)


class PresentationDetail(ObjectDetailViewPermissionRequired):
    cv_viewset = cv_presentation
    template_name = "presentation/stock.html"
    cv_object_detail_layout = "tabs-vertical"
    cv_modal_supported = True
    cv_modal = True
    cv_content_template = "presentation/content.html"

    def cv_get_header_icon(self):
        return {"element": "fas:user", "empty": "", "disabled": "presentation-disabled"}.get(
            self.request.GET.get("icon"), "host:user"
        )

    def get_template_names(self):
        if native_theme.get():
            return ["presentation/native.html"]
        return super().get_template_names()

    def cv_get_object_detail_id(self):
        return "author-modal" if cv_is_modal_request(self.request) else "author-page"

    def get_property_display(self):
        from crud_views_object_detail.lib.config import PropertyGroupConfig

        names = [(gettext_lazy("January"), "january"), (gettext_lazy("February"), "february")]
        if native_theme.get():
            return [
                PropertyGroupConfig(
                    title=HOSTILE,
                    id="native",
                    properties=[
                        {"path": "first_name", "badge": {"color": "brand-custom", "pill": True}},
                        {"path": "first_name", "badge": {"color": 'custom" onclick="attack', "pill": False}},
                        {"path": "last_name"},
                    ],
                )
            ]
        if self.request.GET.get("reverse") == "1":
            names.reverse()
        if self.request.GET.get("count") == "1":
            names = names[:1]
        properties = (
            [{"path": "first_name", "link": {"url": "panel-link", "args": []}}]
            if self.request.GET.get("links") == "1"
            else ["first_name"]
        )
        return [
            PropertyGroupConfig(
                title=title, id=key, icon="host:user" if index == 0 else "fas:user", properties=properties
            )
            for index, (title, key) in enumerate(names)
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["expanded"] = self.request.GET.get("expanded") == "1"
        context["object_detail_layout"] = "native" if native_theme.get() else "tabs-vertical"
        context["accordion_groups"] = [
            ResolvedGroup(title=title, icon=icon, properties=[ResolvedProperty("first_name", "Name", HOSTILE)])
            for title, icon in [
                ("Repeated", "host:user"),
                ("Repeated", "fas:user"),
                ("", ""),
                ("A !?", None),
                ("日本語", "presentation-disabled"),
            ]
        ]
        context["modal_url"] = f"/detail/{author.pk}/?{self.request.GET.urlencode()}"
        return context


def detail(request, pk):
    language = request.GET.get("lang", "en")
    if language not in ("en", "de"):
        return HttpResponse("Allowed lang values: en, de", status=400)
    token = native_theme.set(request.GET.get("theme") == "native")
    classes = {}
    if request.GET.get("size") in ("replace", "remove"):
        value = "native-title-size" if request.GET["size"] == "replace" else ""
        classes = {"heading:size-3": value, "heading:size-5": value}
    try:
        with (
            override(language),
            override_settings(CRUD_VIEWS_BUTTON_CLASSES=classes),
            patch.object(crud_views_settings, "header_level", 2 if request.GET.get("heading") == "2" else None),
        ):
            response = PresentationDetail.as_view()(request, pk=pk)
            if hasattr(response, "render"):
                response.render()
            return response
    finally:
        native_theme.reset(token)


def signin(request):
    login(request, actor, backend="django.contrib.auth.backends.ModelBackend")
    return JsonResponse({"detail": f"/detail/{author.pk}/", "django": django.get_version()})


urlpatterns = [
    path("signin/", signin),
    path("health/", lambda request: JsonResponse({"ready": PORT, "django": django.get_version()})),
    path("detail/<uuid:pk>/", detail, name="presentation-detail"),
    path("panel-link/", lambda request: HttpResponse("Panel link target"), name="panel-link"),
    path("favicon.ico", lambda request: HttpResponse(status=204)),
]


def main():
    try:
        with make_server("127.0.0.1", PORT, StaticFilesHandler(get_wsgi_application())) as server:

            def stop(signum, frame):
                raise SystemExit(0)

            signal.signal(signal.SIGTERM, stop)
            print(json.dumps({"ready": PORT, "database": "temporary SQLite", "media": "temporary"}), flush=True)
            server.serve_forever()
    finally:
        connection.close()
        temporary.cleanup()


if __name__ == "__main__":
    main()
