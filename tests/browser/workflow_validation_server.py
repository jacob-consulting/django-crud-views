"""Stock-only, authenticated loopback fixture with an owned disposable database."""

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

    from django import forms
    from django.contrib.auth import login
    from django.contrib.auth.models import User
    from django.contrib.staticfiles.handlers import StaticFilesHandler
    from django.core.exceptions import ValidationError
    from django.core.management import call_command
    from django.core.wsgi import get_wsgi_application
    from django.db import connections
    from django.http import HttpResponseForbidden, JsonResponse
    from django.template.loader import get_template
    from django.template.response import SimpleTemplateResponse, TemplateResponse
    from django.urls import include, path
    from django_fsm import transition

    import crud_views
    import crud_views_workflow
    from crud_views_workflow.lib.enums import WorkflowComment
    from tests.test1.app.models import Campaign
    from tests.test1.app.views import CampaignWorkflowForm, CampaignWorkflowView

    call_command("migrate", run_syncdb=True, verbosity=0)
    actor = User.objects.create_superuser(username="workflow-browser", password=None, email="")
    objects = {}
    observations = {}
    checks = []
    label = 'Choose <action> & "state"'
    long_text = "<b>Vollständige Prüfung & {{ Vorlage }}</b> " + "Genehmigung erforderlich. " * 8
    token = "DurchgängigerPrüfungsbeleg" * 18
    cancel_caption = "Abbrechen und zur vollständigen Übersicht aller verfügbaren Arbeitsabläufe zurückkehren"
    reasons = ["First <blocker> & {{ literal }}", "Second blocker: approval missing"]

    # Fixture-only proxy transitions add many real FSM actions without new tables.
    def extra_transition(name, secret=False):
        def action(self, by=None, comment=None):
            return {"fixture_action": name}

        action.__name__ = name
        return transition(
            field=Campaign._meta.get_field("state"),
            source="new",
            target="active",
            conditions=[lambda obj: obj.name.startswith("long-")],
            permission=(lambda obj, user: False) if secret else None,
            custom={
                "label": f"{long_text}{name} {token}",
                "comment": WorkflowComment.OPTIONAL,
                "help_text": long_text + token,
            },
        )(action)

    proxy_attrs = {"__module__": __name__, "Meta": type("Meta", (), {"proxy": True, "app_label": "app"})}
    proxy_attrs.update({f"wf_extra_{index}": extra_transition(f"wf_extra_{index}") for index in range(6)})
    proxy_attrs["wf_secret"] = extra_transition("wf_secret", secret=True)
    BrowserCampaign = type("BrowserCampaign", (Campaign,), proxy_attrs)
    Campaign._meta.get_field("state").protected = True

    def business(obj, name, *, user):
        assert name != "wf_secret", "Unauthorized blocker disclosure"
        checks.append({"pk": obj.pk, "name": name})
        if "blocked" in obj.name or obj.name.startswith("long-") or ("mixed-" in obj.name and name == "wf_activate"):
            raise ValidationError([long_text + token, reasons[1] + token] if obj.name.startswith("long-") else reasons)

    BrowserCampaign.workflow_check_transition = business

    class CustomForm(CampaignWorkflowForm):
        extra = forms.CharField(label="Additional required input")

        def __init__(self, data=None, files=None, *, initial, prefix, cv_view, choices, transition_comments):
            super().__init__(
                data=data,
                files=files,
                initial=initial,
                prefix=prefix,
                cv_view=cv_view,
                choices=choices,
                transition_comments=transition_comments,
            )
            self.clean_calls = 0
            self.constructor_ids = {name: self[name].auto_id for name in self.fields}
            self.cached_transition = list(self["transition"].subwidgets)

        def clean(self):
            self.clean_calls += 1
            cleaned = super().clean()
            assert isinstance(cleaned, dict)
            return cleaned

        def get_layout_fields(self):
            return ["extra", *super().get_layout_fields()]

    class BrowserWorkflowView(CampaignWorkflowView):
        cv_modal = True
        cv_transition_presentation = "buttons"
        cv_transition_label = label

        def get_queryset(self):
            return BrowserCampaign.objects.all()

        def get_success_url(self):
            return self.request.path

        def cv_form_valid(self, context):
            if self.object.name.startswith("late-"):
                self.object.name += ":blocked"
                self.object.save()
            return super().cv_form_valid(context)

    def object_for(scenario):
        if scenario not in objects:
            assert scenario.replace("-", "").isalnum() and len(scenario) < 100
            objects[scenario] = BrowserCampaign.objects.create(
                name=scenario + (":blocked" if scenario.startswith("initial-blockers-") else ""),
                state="canceled" if scenario.startswith("empty-") else "new",
            )
        return BrowserCampaign.objects.get(pk=objects[scenario].pk)

    def signin(request):
        if request.META["REMOTE_ADDR"] != "127.0.0.1":
            return HttpResponseForbidden()
        login(request, actor, backend="django.contrib.auth.backends.ModelBackend")
        return JsonResponse({"authenticated": True})

    def observe(request, scenario):
        if not request.user.is_authenticated:
            return HttpResponseForbidden()
        obj = object_for(scenario)
        return JsonResponse(
            {
                "state": obj.state,
                "name": obj.name,
                "history": list(
                    obj.get_workflow_info_queryset().values("transition", "comment", "state_old", "state_new")
                ),
                "request": observations.get(scenario),
                "checks": [check for check in checks if check["pk"] == obj.pk],
            }
        )

    def workflow(request, scenario):
        obj = object_for(scenario)
        custom = any(part in scenario for part in ("custom", "late-"))
        with ExitStack() as stack:
            stack.enter_context(
                patch.object(BrowserWorkflowView, "form_class", CustomForm if custom else CampaignWorkflowForm)
            )
            stack.enter_context(
                patch.object(
                    BrowserWorkflowView,
                    "cv_transition_presentation",
                    "radio" if scenario.startswith("radio-") else "buttons",
                )
            )
            if scenario.startswith("cancel-omitted-"):
                stack.enter_context(
                    patch.object(BrowserWorkflowView, "cv_get_cancel_url", lambda *args, **kwargs: None)
                )
            if scenario.startswith("long-"):
                for name in (
                    "cv_transition_label",
                    "cv_transition_help_text",
                    "cv_comment_help_text",
                    "cv_comment_label",
                ):
                    stack.enter_context(patch.object(BrowserWorkflowView, name, long_text + token))
                original_cancel_kwargs = CampaignWorkflowForm.get_cancel_button_kwargs

                def long_cancel_kwargs(form):
                    return {**original_cancel_kwargs(form), "value": cancel_caption}

                stack.enter_context(patch.object(CampaignWorkflowForm, "get_cancel_button_kwargs", long_cancel_kwargs))
            for step in obj.get_all_state_transitions():
                custom_meta = dict(step.custom)
                if scenario.startswith(("all-none-", "optional-", "textarea-enter-")):
                    custom_meta["comment"] = (
                        WorkflowComment.NONE if scenario.startswith("all-none-") else WorkflowComment.OPTIONAL
                    )
                if scenario.startswith("long-"):
                    custom_meta.update(label=long_text + step.name + token, help_text=long_text + token)
                stack.enter_context(patch.object(step, "custom", custom_meta))
                if scenario.startswith("one-") and step.name == "wf_cancel_new":
                    stack.enter_context(patch.object(step, "conditions", [lambda obj: False]))
            response = BrowserWorkflowView.as_view()(request, pk=obj.pk)
            if isinstance(response, SimpleTemplateResponse):
                response.render()
        if request.method == "POST":
            form = getattr(response, "context_data", {}).get("form")
            observations[scenario] = {
                "fields": dict(request.POST.items()),
                "status": response.status_code,
                "errors": dict(form.errors) if form else {},
                "clean_calls": getattr(form, "clean_calls", None),
                "context_state": getattr(getattr(response, "context_data", {}).get("object"), "state", None),
            }
        return response

    def launch(request, scenario):
        object_for(scenario)
        return TemplateResponse(request, HOST, {"fixture_target": f"/workflow/{scenario}/"})

    def change(request, scenario):
        if request.META["REMOTE_ADDR"] != "127.0.0.1" or not request.user.is_authenticated or request.method != "POST":
            return HttpResponseForbidden()
        obj = object_for(scenario)
        obj.name += ":blocked"
        obj.save()
        return JsonResponse({"changed": True})

    def repeated(request):
        obj = object_for("repeated-forms-page")
        view = BrowserWorkflowView()
        view.setup(request)
        view.object = obj
        forms = [view.get_form(), view.get_form()]
        view.prefix = "prefixed"
        forms.append(view.get_form())
        return TemplateResponse(request, HOST, {"fixture_forms": forms, "view": view})

    globals()["urlpatterns"] = [
        path("signin/", signin),
        path("observe/<str:scenario>/", observe),
        path("workflow/<str:scenario>/", workflow),
        path("launch/<str:scenario>/", launch),
        path("change/<str:scenario>/", change),
        path("repeated/", repeated),
        path("", include("tests.test1.project.urls")),
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
                        "label": label,
                        "long_text": long_text,
                        "token": token,
                        "cancel_caption": cancel_caption,
                        "reasons": reasons,
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
