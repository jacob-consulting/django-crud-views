"""Stock-only, authenticated loopback fixture with an owned disposable database."""

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

ROOT = Path(__file__).resolve().parents[2]
HOST = "workflow_validation/page.html"


def serve(directory):
    sys.path[:0] = [str(ROOT / "src"), str(ROOT)]
    os.environ.pop("DJANGO_SETTINGS_MODULE", None)
    import django
    from django.conf import settings

    configure = settings.configure
    database = str(Path(directory) / "workflow.sqlite3")

    def fixture_settings(self, **kwargs):
        kwargs.update(
            CRUD_VIEWS_EXTENDS=HOST,
            CRUD_VIEWS_BUTTON_CLASSES={"form:cancel-tag": "a"},
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": database}},
            ALLOWED_HOSTS=["127.0.0.1"],
            ROOT_URLCONF=__name__,
        )
        kwargs["TEMPLATES"][0]["DIRS"] = [ROOT / "tests/browser/templates"]
        configure(**kwargs)

    from tests.test1.conftest import pytest_configure

    with patch.object(type(settings), "configure", fixture_settings):
        pytest_configure()

    from django.contrib.auth import login
    from django.contrib.auth.models import User
    from django.contrib.staticfiles.handlers import StaticFilesHandler
    from django.core.management import call_command
    from django.core.wsgi import get_wsgi_application
    from django.db import connections
    from django.http import HttpResponseForbidden, HttpResponseRedirect, JsonResponse
    from django.template.loader import get_template
    from django.template.response import SimpleTemplateResponse
    from django.urls import include, path

    import crud_views
    import crud_views_workflow
    from tests.test1.app.models import Campaign
    from tests.test1.app.views import CampaignWorkflowView

    call_command("migrate", run_syncdb=True, verbosity=0)
    actor = User.objects.create_superuser(username="workflow-browser", password=None, email="")
    objects = {name: Campaign.objects.create(name=name) for name in ("native-first-page", "required-recovery-page")}
    observations = {}

    class BrowserWorkflowView(CampaignWorkflowView):
        cv_modal = True
        cv_transition_presentation = "buttons"

        def get_success_url(self):
            return self.request.path

    def signin(request):
        if request.META["REMOTE_ADDR"] != "127.0.0.1":
            return HttpResponseForbidden()
        login(request, actor, backend="django.contrib.auth.backends.ModelBackend")
        return JsonResponse({"authenticated": True})

    def observe(request, scenario):
        if not request.user.is_authenticated:
            return HttpResponseForbidden()
        obj = Campaign.objects.get(pk=objects[scenario].pk)
        return JsonResponse(
            {
                "state": obj.state,
                "name": obj.name,
                "history": list(
                    obj.get_workflow_info_queryset().values("transition", "comment", "state_old", "state_new")
                ),
                "request": observations.get(scenario),
            }
        )

    def workflow(request, scenario):
        response = BrowserWorkflowView.as_view()(request, pk=objects[scenario].pk)
        if isinstance(response, SimpleTemplateResponse):
            response.render()
        if request.method == "POST":
            observations[scenario] = {"fields": dict(request.POST.items()), "status": response.status_code}
        return response

    def launch(request, scenario):
        return SimpleTemplateResponse(HOST, {"fixture_target": f"/workflow/{scenario}/"})

    globals()["urlpatterns"] = [
        path("signin/", signin),
        path("observe/<str:scenario>/", observe),
        path("workflow/<str:scenario>/", workflow),
        path("launch/<str:scenario>/", launch),
        path("", include("tests.test1.project.urls")),
        path("destination/", lambda request: HttpResponseRedirect("/campaign/")),
    ]
    versions = {name: metadata.version(name) for name in ("Django", "django-crispy-forms", "crispy-bootstrap5")}
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
                        "modules": {
                            "crud_views": crud_views.__file__,
                            "crud_views_workflow": crud_views_workflow.__file__,
                        },
                        "host": get_template(HOST).origin.name,
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
