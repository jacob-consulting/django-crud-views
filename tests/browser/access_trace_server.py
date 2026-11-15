"""Owned loopback fixture: real authentication, registered views and access traces."""

import argparse
import json
import os
import signal
import sys
import tempfile
from importlib import metadata
from pathlib import Path
from unittest.mock import patch
from wsgiref.simple_server import make_server

from manage_presentation_server import CSP

ROOT = Path(__file__).resolve().parents[2]
LONG = "Berechtigungszuständigkeitsüberprüfung" * 8
HOSTILE = '<unsafe>&"' + LONG


def serve(directory):
    sys.path[:0] = [str(ROOT / "src"), str(ROOT)]
    os.environ.pop("DJANGO_SETTINGS_MODULE", None)
    from django.conf import settings

    configure = settings.configure
    database = str(Path(directory) / "access.sqlite3")

    def fixture_settings(self, **kwargs):
        kwargs.update(
            DEBUG=False,
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": database}},
            ROOT_URLCONF=__name__,
            ALLOWED_HOSTS=["127.0.0.1"],
            CRUD_VIEWS_EXTENDS="manage/page.html",
            PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
        )
        kwargs["TEMPLATES"][0]["DIRS"] = [ROOT / "tests/browser/templates"]
        configure(**kwargs)

    from tests.test1.conftest import pytest_configure

    with patch.object(type(settings), "configure", fixture_settings):
        pytest_configure()

    from django.contrib.auth import authenticate, login
    from django.contrib.auth.models import Group, Permission, User
    from django.contrib.staticfiles.handlers import StaticFilesHandler
    from django.core.management import call_command
    from django.core.wsgi import get_wsgi_application
    from django.db import connections
    from django.http import HttpResponse, JsonResponse
    from django.middleware.csrf import get_token
    from django.template.loader import get_template
    from django.test import override_settings
    from django.urls import include, path, reverse
    from django.utils import translation
    from guardian.shortcuts import assign_perm

    import crud_views
    import crud_views_guardian
    from crud_views.lib.button_classes import DEFAULT_BUTTON_CLASSES
    from crud_views.lib.settings import crud_views_settings
    from crud_views.lib.views import (
        CreateView,
        DeleteViewPermissionRequired,
        DetailViewPermissionRequired,
        ListViewPermissionRequired,
    )
    from crud_views.lib.viewset import ParentViewSet, ViewSet
    from crud_views_guardian.lib.views import GuardianDetailViewPermissionRequired, GuardianListViewPermissionRequired
    from crud_views_guardian.lib.viewset import GuardianViewSet
    from tests.test1.app.models import Author, Book, Publisher

    call_command("migrate", run_syncdb=True, verbosity=0, skip_checks=True)
    developer = User.objects.create_user(username="developer", password="fixture-only")
    developer.groups.add(Group.objects.create(name=crud_views_settings.manage_group))
    nested_developer = User.objects.create_user(username="nested-developer", password="fixture-only")
    nested_developer.groups.add(developer.groups.get())
    nested_developer.user_permissions.add(Permission.objects.get(codename="view_publisher"))
    ordinary = User.objects.create_user(username="ordinary", password="fixture-only")
    actor = User.objects.create_user(pk=22, username="reader", password="fixture-only")
    collision = User.objects.create_user(username="22", password="fixture-only")
    hostile = User.objects.create_user(username=HOSTILE, password="fixture-only")
    actor.user_permissions.add(*Permission.objects.filter(codename__in=["view_author", "view_publisher", "view_book"]))
    author = Author.objects.create(first_name="PRIVATE_OBJECT_CONTENT", last_name="must_not_leak")
    Author.objects.create(first_name="PRIVATE_OTHER_CONTENT", last_name="must_not_leak")
    assign_perm("app.view_author", actor, author)
    publisher = Publisher.objects.create(name="PRIVATE_PARENT_CONTENT")
    book = Book.objects.create(publisher=publisher, title="PRIVATE_CHILD_CONTENT")

    def explode(self, request, *args, **kwargs):
        raise ValueError(HOSTILE)

    def handler(self, request, *args, **kwargs):
        raise AssertionError("Trace called a real handler")

    viewsets = {}
    for kind, cls in (("core", ViewSet), ("guardian", GuardianViewSet)):
        vs = cls(model=Author, name="trace_" + kind, prefix=kind + "/" + "long_path_" * 20)
        viewsets[kind] = vs
        bases = [
            ("list", GuardianListViewPermissionRequired if kind == "guardian" else ListViewPermissionRequired),
            ("detail", GuardianDetailViewPermissionRequired if kind == "guardian" else DetailViewPermissionRequired),
            ("delete", DeleteViewPermissionRequired),
            ("post_only", CreateView),
            ("extra", CreateView),
            ("error", CreateView),
        ]
        for key, base in bases:
            attrs = {"__module__": __name__, "cv_viewset": vs, "cv_key": key, "cv_path": key, "get": handler}
            if kind == "guardian" and key in {"list", "detail"}:
                attrs["cv_guardian_accept_global_perms"] = False
            if key == "post_only":
                attrs.update(http_method_names=["post"], cv_backend_only=True, post=handler)
            if key == "extra":
                attrs["cv_path_contribute"] = classmethod(lambda cls: "(?P<extra>[a-z]+)/")
            if key == "error":
                attrs["dispatch"] = explode
            type("BrowserTrace" + key + LONG, (base,), attrs)
    parent = ViewSet(model=Publisher, name="trace_parent", prefix="parent")
    child = ViewSet(
        model=Book,
        name="trace_child",
        prefix="child",
        parent=ParentViewSet(name=parent.name, attribute="publisher"),
    )
    type(
        "NestedTraceDetail",
        (DetailViewPermissionRequired,),
        {"cv_viewset": child, "__module__": __name__, "get": handler},
    )

    def signin(request):
        if request.method == "GET":
            return JsonResponse({"csrf": get_token(request), "username": developer.username})
        user = authenticate(request, username=request.POST.get("username"), password=request.POST.get("password"))
        if user is None:
            return HttpResponse(status=403)
        login(request, user)
        return JsonResponse({"authenticated": True, "pk": user.pk})

    def identity(request):
        return JsonResponse({"username": request.user.get_username(), "pk": request.user.pk})

    def manage(request, kind, enabled, language):
        if kind not in viewsets or enabled not in {"on", "off", "override"} or language not in {"en", "de"}:
            return HttpResponse(status=404)
        overrides = {
            key: value + " fixture-trace-override" for key, value in DEFAULT_BUTTON_CLASSES.items() if ":trace-" in key
        }
        with (
            translation.override(language),
            patch.object(crud_views_settings, "manage_access_trace", enabled != "off"),
            override_settings(CRUD_VIEWS_BUTTON_CLASSES=overrides if enabled == "override" else {}),
        ):
            response = viewsets[kind].get_view_class("manage").as_view()(request)
            if hasattr(response, "render"):
                response.render()
        return response

    def nested_manage(request, trace_parent_pk, language):
        with translation.override(language), patch.object(crud_views_settings, "manage_access_trace", True):
            response = child.get_view_class("manage").as_view()(request, trace_parent_pk=trace_parent_pk)
            if hasattr(response, "render"):
                response.render()
            return response

    globals()["urlpatterns"] = [
        path("signin/", signin),
        path("identity/", identity),
        path("case/<str:kind>/<str:enabled>/<str:language>/", manage),
        path("nested-case/<int:trace_parent_pk>/<str:language>/", nested_manage),
        path(
            "jquery.js",
            lambda request: HttpResponse(
                (ROOT / "node_modules/jquery/dist/jquery.min.js").read_bytes(), content_type="text/javascript"
            ),
        ),
        path("favicon.ico", lambda request: HttpResponse(status=204)),
        *[path("", include(vs.urlpatterns)) for vs in [*viewsets.values(), parent, child]],
    ]
    routes = {
        kind: {
            key: reverse(vs.get_router_name(key), kwargs={vs.pk_name: author.pk} if key in {"detail", "delete"} else {})
            for key in ("list", "detail", "delete", "error", "post_only")
        }
        for kind, vs in viewsets.items()
    }
    routes["nested"] = reverse(
        child.get_router_name("detail"), kwargs={child.parent.get_pk_name(): publisher.pk, child.pk_name: book.pk}
    )
    routes["nested_manage"] = reverse(
        child.get_router_name("manage"), kwargs={child.parent.get_pk_name(): publisher.pk}
    )
    routes["nested_form"] = f"/nested-case/{publisher.pk}/en/"
    application = StaticFilesHandler(get_wsgi_application())

    def csp_application(environ, start_response):
        def headers(status, values, exc_info=None):
            return start_response(status, [*values, ("Content-Security-Policy", CSP)], exc_info)

        return application(environ, headers)

    try:
        with make_server("127.0.0.1", 0, csp_application) as server:
            print(
                json.dumps(
                    {
                        "ready": server.server_port,
                        "database": database,
                        "python": sys.version,
                        "versions": {name: metadata.version(name) for name in ("Django", "django-guardian")},
                        "modules": {
                            "crud_views": crud_views.__file__,
                            "crud_views_guardian": crud_views_guardian.__file__,
                        },
                        "origins": {
                            name: get_template(name).origin.name
                            for name in (
                                "crud_views/view_manage.html",
                                "crud_views/view_guardian_manage.html",
                                "crud_views/includes/access_trace.html",
                                "manage/page.html",
                            )
                        },
                        "csp": CSP,
                        "routes": routes,
                        "object_pk": str(author.pk),
                        "actors": {u.username: u.pk for u in (developer, ordinary, actor, collision, hostile)},
                        "hostile": HOSTILE,
                        "view_keys": {kind: list(vs.get_all_views()) for kind, vs in viewsets.items()},
                    }
                ),
                flush=True,
            )
            server.serve_forever()
    finally:
        connections.close_all()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args()

    def stop(signum, frame):
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, stop)
    with tempfile.TemporaryDirectory(prefix="database-", dir=args.directory) as directory:
        serve(directory)


if __name__ == "__main__":
    main()
