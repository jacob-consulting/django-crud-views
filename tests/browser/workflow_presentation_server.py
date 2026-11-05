"""Owned loopback workflow fixture; real source/templates, disposable SQLite only."""

import argparse
import json
import os
import signal
import sys
import tempfile
from contextlib import ExitStack
from html.parser import HTMLParser
from importlib import metadata
from pathlib import Path
from unittest.mock import patch
from wsgiref.simple_server import make_server

ROOT = Path(__file__).resolve().parents[2]


class Forms(HTMLParser):
    def __init__(self):
        super().__init__()
        self.depth = self.maximum = self.forms = self.tokens = 0

    def handle_starttag(self, tag, attrs):
        if tag == "form":
            self.forms += 1
            self.depth += 1
            self.maximum = max(self.maximum, self.depth)
        if tag == "input" and dict(attrs).get("name") == "csrfmiddlewaretoken":
            self.tokens += 1

    def handle_endtag(self, tag):
        if tag == "form":
            self.depth -= 1


def serve(theme, companion, directory):
    sys.path[:0] = [str(ROOT / "src"), str(ROOT), str(companion / "src")]
    os.environ.pop("DJANGO_SETTINGS_MODULE", None)
    import django
    from django.conf import settings

    configure = settings.configure
    database = str(Path(directory) / "workflow.sqlite3")
    # Only the stock host is supplied here. Workflow markup comes from production templates.
    authority = (ROOT / "tests/browser/templates/conditional_formsets/page.html").read_text()
    import re

    assets = "\n".join(
        match.group(0)
        for match in re.finditer(
            r"<(?:link|script)\b[^>]*(?:bootstrap@5\.3\.3|font-awesome)[^>]*>(?:</script>)?", authority
        )
    )
    stock = (
        '{% load crud_views %}<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        + assets
        + "{% cv_css %}</head><body><main class='container'>{% block cv_content %}{% endblock %}</main>"
        "</body></html>"
    )

    def fixture_settings(self, **kwargs):
        if theme == "tabler":
            kwargs["INSTALLED_APPS"][0:0] = ["django_tabler", "crud_views_tabler", "django.contrib.humanize"]
        kwargs["CRUD_VIEWS_EXTENDS"] = "crud_views_tabler/page.html" if theme == "tabler" else "workflow-host.html"
        kwargs["CRISPY_TEMPLATE_PACK"] = "crispy_tabler" if theme == "tabler" else "bootstrap5"
        kwargs["CRISPY_ALLOWED_TEMPLATE_PACKS"] = [kwargs["CRISPY_TEMPLATE_PACK"]]
        kwargs["DATABASES"] = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": database}}
        kwargs["ALLOWED_HOSTS"] = ["127.0.0.1"]
        kwargs["ROOT_URLCONF"] = __name__
        templates = kwargs["TEMPLATES"][0]
        templates["DIRS"] = []
        templates["APP_DIRS"] = False
        templates["OPTIONS"]["loaders"] = [
            ("django.template.loaders.locmem.Loader", {"workflow-host.html": stock}),
            "django.template.loaders.app_directories.Loader",
        ]
        configure(**kwargs)

    from tests.test1.conftest import pytest_configure

    with patch.object(type(settings), "configure", fixture_settings):
        pytest_configure()

    from django.contrib import admin
    from django.contrib.auth import login
    from django.contrib.auth.models import User
    from django.contrib.contenttypes.models import ContentType
    from django.contrib.staticfiles.handlers import StaticFilesHandler
    from django.core.management import call_command
    from django.core.wsgi import get_wsgi_application
    from django.db import connections
    from django.http import HttpResponse, JsonResponse
    from django.template import Template
    from django.template.loader import get_template
    from django.test import override_settings
    from django.urls import include, path

    import crud_views
    import crud_views_workflow
    from crud_views_workflow.models import WorkflowInfo
    from tests.test1.app.models import Campaign
    from tests.test1.app.views import CampaignWorkflowView

    call_command("migrate", run_syncdb=True, verbosity=0)
    actor = User.objects.create_superuser(username="workflow-browser", first_name="Ada", password=None, email="")
    objects = {}
    for name in ("normal", "wide", "no-history", "terminal", "neither"):
        obj = Campaign.objects.create(
            name="Workflow fixture", state="canceled" if name in ("terminal", "neither") else "new"
        )
        objects[name] = obj
        if name not in ("no-history", "neither"):
            for index in range(3 if name == "wide" else 1):
                WorkflowInfo.objects.create(
                    transition="wf_activate",
                    state_old="new",
                    state_new="active",
                    user=actor,
                    comment=("LongHistoryValue" * 30 + str(index)) if name == "wide" else "Checked",
                    workflow_object_content_type=ContentType.objects.get_for_model(obj),
                    workflow_object_pk=str(obj.pk),
                )
    CampaignWorkflowView.cv_modal = True
    observed = {}

    def workflow(request, scenario):
        origins = {}
        original = Template._render

        def record(template, context):
            origins[template.name or "inline"] = template.origin.name
            return original(template, context)

        mode = request.GET.get("badge", "normal")
        classes = {}
        if mode in ("empty", "none"):
            classes = {"workflow:badge-light": "" if mode == "empty" else None}
        elif mode == "custom":
            classes = {"workflow:badge-purple": 'badge custom-purple " <unsafe> {{literal}}'}
        with ExitStack() as stack:
            stack.enter_context(override_settings(CRUD_VIEWS_BUTTON_CLASSES=classes))
            stack.enter_context(patch.object(Template, "_render", record))
            if mode in ("custom", "missing"):
                stack.enter_context(patch.object(Campaign, "STATE_BADGES", {**Campaign.STATE_BADGES, "new": "purple"}))
            if mode == "custom":
                stack.enter_context(
                    patch.object(Campaign, "get_state_name", lambda self, state: '<b>State & "quoted"</b>')
                )
            response = CampaignWorkflowView.as_view()(request, pk=objects[scenario].pk)
            response.render()
            raw = Forms()
            raw.feed(response.content.decode())
            current = str(Campaign.objects.get(pk=objects[scenario].pk).state_badge)
        observed.clear()
        observed.update(origins=origins, current_badge=current)
        # HTMLParser internals are intentionally excluded from the JSON receipt.
        observed["raw"] = {key: getattr(raw, key) for key in ("forms", "tokens", "maximum", "depth")}
        return response

    def signin(request):
        login(request, actor, backend="django.contrib.auth.backends.ModelBackend")
        return JsonResponse({"authenticated": True})

    dummy = lambda request: HttpResponse("Fixture navigation destination")  # noqa: E731
    globals()["urlpatterns"] = [
        path("admin/", admin.site.urls),
        path("signin/", signin),
        path("observations/", lambda request: JsonResponse(observed)),
        path("workflow/<str:scenario>/", workflow),
        path("dashboard/", include(([path("", dummy, name="index")], "dashboard"))),
        path("logout/", dummy, name="logout"),
        path("login/", dummy, name="login"),
        path("favicon.ico", lambda request: HttpResponse(status=204)),
        path("", include("tests.test1.project.urls")),
    ]
    versions = {name: metadata.version(name) for name in ("Django", "django-crispy-forms", "crispy-bootstrap5")}
    modules = {"crud_views": crud_views.__file__, "crud_views_workflow": crud_views_workflow.__file__}
    if theme == "tabler":
        import crud_views_tabler
        import django_tabler

        modules.update(
            crud_views_tabler=crud_views_tabler.__file__,
            django_tabler=django_tabler.__file__,
        )
    origins = {
        name: get_template(name).origin.name
        for name in (
            "crud_views_workflow/badge.html",
            "crud_views/snippets/form_frame.html",
            "crud_views_workflow/view_workflow.action.html",
            "crud_views_workflow/view_workflow.history.html",
            f"{settings.CRISPY_TEMPLATE_PACK}/layout/formactions.html",
        )
    }
    try:
        with make_server("127.0.0.1", 0, StaticFilesHandler(get_wsgi_application())) as server:
            print(
                json.dumps(
                    {
                        "ready": server.server_port,
                        "database": database,
                        "python": sys.version,
                        "django": django.get_version(),
                        "versions": versions,
                        "modules": modules,
                        "origins": origins,
                        "theme": theme,
                    }
                ),
                flush=True,
            )
            server.serve_forever()
    finally:
        connections.close_all()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--theme", choices=("stock", "tabler"), required=True)
    parser.add_argument("--companion", type=Path, required=True)
    parser.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args()

    def stop(signum, frame):
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, stop)
    # Parent owns this directory too, so SIGKILL/startup failures have a cleanup backstop.
    with tempfile.TemporaryDirectory(prefix="database-", dir=args.directory) as directory:
        serve(args.theme, args.companion, directory)


if __name__ == "__main__":
    main()
