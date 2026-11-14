"""Loopback-only stock ManageView fixture. Parent owns all temporary data/processes."""

import argparse
import json
import os
import signal
import sys
import tempfile
from contextlib import ExitStack
from importlib import metadata
from pathlib import Path
from unittest.mock import patch
from wsgiref.simple_server import make_server

ROOT = Path(__file__).resolve().parents[2]
CSP = (
    "default-src 'none'; script-src 'self' https://cdn.jsdelivr.net; "
    "style-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
    "font-src https://cdnjs.cloudflare.com; img-src 'self' data:; connect-src 'self'; "
    "form-action 'self'; base-uri 'none'; object-src 'none'; frame-ancestors 'none'"
)
LONG = "Berechtigungsverwaltungszuständigkeitsüberprüfung" * 3


def serve(directory):
    sys.path[:0] = [str(ROOT / "src"), str(ROOT)]
    os.environ.pop("DJANGO_SETTINGS_MODULE", None)
    from django.conf import settings

    configure = settings.configure
    database = str(Path(directory) / "manage.sqlite3")

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
    from django.core.checks import Warning
    from django.core.management import call_command
    from django.core.wsgi import get_wsgi_application
    from django.db import connections
    from django.http import HttpResponse, JsonResponse
    from django.middleware.csrf import get_token
    from django.template.loader import get_template
    from django.test import override_settings
    from django.urls import include, path
    from django.utils import translation
    from guardian.shortcuts import assign_perm

    import crud_views
    import crud_views_guardian
    from crud_views.lib.resource import Resource
    from crud_views.lib.settings import crud_views_settings
    from crud_views.lib.view.buttons import ContextButton
    from crud_views.lib.views import ListViewPermissionRequired
    from crud_views.lib.viewset import ParentViewSet, ViewSet
    from crud_views_guardian.lib.views import GuardianListViewPermissionRequired
    from crud_views_guardian.lib.viewset import GuardianViewSet
    from tests.test1.app.models import Author, Book, BookNote, Publisher

    call_command("migrate", run_syncdb=True, verbosity=0, skip_checks=True)
    developer = User.objects.create_user(username="developer-" + LONG, password="fixture-only")
    User.objects.create_user(username="ordinary", password="fixture-only")
    developer.groups.add(Group.objects.create(name=crud_views_settings.manage_group))
    readers = Group.objects.create(name="Leseberechtigungsgruppe-" + LONG)
    developer.groups.add(readers)
    users = [User.objects.create_user(username=f"holder-{n:02d}-" + LONG) for n in range(21)]
    supers = [User.objects.create_user(username=f"super-{n}-" + LONG, is_superuser=True) for n in range(2)]
    author = Author.objects.create(first_name="Browser", last_name="Fixture")
    publisher = Publisher.objects.create(name="Browser parent")
    book = Book.objects.create(title="Nested browser book", publisher=publisher)
    BookNote.objects.create(note="Nested note", book=book)
    read = Permission.objects.get(content_type__app_label="app", codename="view_author")
    readers.permissions.add(read)
    developer.user_permissions.add(
        *Permission.objects.filter(content_type__app_label="app", codename__in=["view_publisher", "view_book"])
    )
    assign_perm("app.view_author", developer, author)
    assign_perm("app.change_author", developer, author)
    assign_perm("app.contact_author", readers, author)
    viewsets = {}
    for kind, cls in (("core", ViewSet), ("guardian", GuardianViewSet)):
        vs = cls(model=Author, name="browser_" + kind, prefix=kind)
        viewsets[kind] = vs
        type(
            "Berechtigungsdiagnose" + LONG,
            (GuardianListViewPermissionRequired if kind == "guardian" else ListViewPermissionRequired,),
            {
                "__module__": __name__,
                "cv_viewset": vs,
                "cv_browser_unknown": "x" * 250,
                "__annotations__": {"cv_browser_annotation": str},
            },
        )
    parent = ViewSet(model=Publisher, name="browser_parent", prefix="parent")
    child = ViewSet(
        model=Book, name="browser_child", prefix="child", parent=ParentViewSet(name=parent.name, attribute="publisher")
    )
    leaf = ViewSet(
        model=BookNote, name="browser_leaf", prefix="leaf", parent=ParentViewSet(name=child.name, attribute="book")
    )

    class BrowserResource(Resource):
        pk: str

    ViewSet(model=BrowserResource, name="browser_resource", parent=ParentViewSet(name=parent.name))
    viewsets.update(nested=leaf, hierarchy=parent)

    # Ordinary and Guardian views keep their actual dispatch, membership and ancestor gates.
    def signin(request):
        if request.method == "GET":
            return JsonResponse({"csrf": get_token(request), "username": developer.username})
        user = authenticate(request, username=request.POST.get("username"), password=request.POST.get("password"))
        if user is None:
            return HttpResponse(status=403)
        login(request, user)
        return JsonResponse({"authenticated": True, "developer": user.pk == developer.pk})

    class DiagnosticCheck:
        def messages(self):
            return [
                Warning(LONG + " <unsafe> & configuration", id="fixture.W001"),
                Warning("Must be silenced", id="fixture.W002"),
            ]

    def manage(request, kind, scenario):
        if kind not in viewsets or scenario not in {
            "normal",
            "errors",
            "empty",
            "holders0",
            "holders1",
            "holders20",
            "holders21",
            "hidden",
            "zero-defaults",
            "no-holders",
        }:
            return HttpResponse(status=404)
        vs = viewsets[kind]
        count = int(scenario[7:]) if scenario.startswith("holders") else 21
        User.user_permissions.through.objects.filter(user_id__in=[u.pk for u in users]).delete()
        for user in users[:count]:
            user.user_permissions.add(read)
        User.objects.filter(pk__in=[u.pk for u in supers]).update(is_active=False)
        User.objects.filter(pk__in=[u.pk for u in supers[: min(count, 2)]]).update(is_active=True)
        view = vs.get_view_class("manage")
        with ExitStack() as stack:
            stack.enter_context(translation.override(request.GET.get("language", "en")))
            stack.enter_context(patch.object(crud_views_settings, "manage_show_users", scenario != "hidden"))
            stack.enter_context(override_settings(SILENCED_SYSTEM_CHECKS=["fixture.W002", "viewset.W280"]))
            if scenario == "errors":
                stack.enter_context(patch.object(type(vs), "checks", lambda self: [DiagnosticCheck()]))
                stack.enter_context(
                    patch.object(vs, "context_buttons", [ContextButton(key="broken", key_target="absent")])
                )
            if scenario == "empty":
                stack.enter_context(patch.object(vs, "_default_permissions", {}))
                stack.enter_context(patch.object(vs, "context_buttons", []))
            if scenario == "no-holders":
                stack.enter_context(patch.object(vs, "_default_permissions", {"add": "app.add_author"}))
            kwargs = {"browser_parent_pk": publisher.pk, "browser_child_pk": book.pk} if kind == "nested" else {}
            response = view.as_view()(request, **kwargs)
            # Explicit template-contract boundary cases: zero registered display rows / no default rows.
            # Data and authorization still come from the real request; no mocked permissions or checks.
            if scenario == "empty":
                response.context_data["manage_views"] = []
            if scenario == "zero-defaults":
                for item in response.context_data["manage_views"]:
                    for section in item["sections"]:
                        section["default_count"] = 0
                        for entry in section["entries"]:
                            entry["is_default"] = False
                for section in response.context_data["manage_presentation"]["sections"]:
                    section["default_count"] = 0
                    for entry in section["entries"]:
                        entry["is_default"] = False
            response.render()
        return response

    globals()["urlpatterns"] = [
        path("signin/", signin),
        path("case/<str:kind>/<str:scenario>/", manage),
        path(
            "jquery.js",
            lambda request: HttpResponse(
                (ROOT / "node_modules/jquery/dist/jquery.min.js").read_bytes(), content_type="text/javascript"
            ),
        ),
        path("favicon.ico", lambda request: HttpResponse(status=204)),
        *[path("", include(vs.urlpatterns)) for vs in viewsets.values()],
        path("", include(child.urlpatterns)),
    ]
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
                                "manage/page.html",
                            )
                        },
                        "csp": CSP,
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
