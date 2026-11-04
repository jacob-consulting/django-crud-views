"""Single-threaded source-bound tooltip fixture with request-local recipe overrides."""

# ruff: noqa: E402 -- configure the isolated project before Django model imports.
import copy
import hashlib
import json
import os
import re
import signal
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
from django.template.loaders.locmem import Loader as MemoryLoader
from django.test import override_settings
from django.urls import include, path

import crud_views
from crud_views.lib.view import CardAction, ContextButton
from tests.test1.app.models import Author
from tests.test1.app.views import (
    AuthorCardListView,
    AuthorDeleteView,
    AuthorDetailView,
    AuthorListView,
    AuthorModalContactForm,
    AuthorModalContactView,
    AuthorModalDetailView,
    AuthorModalListView,
    AuthorUpdateView,
)

ROOT = Path(__file__).resolve().parents[2]
assert Path(crud_views.__file__).resolve().is_relative_to(ROOT / "src"), "Refuse installed wheel"
custom_mode = ContextVar("tooltip_custom", default=False)
PAYLOAD = '"quoted" & <img src=x onerror=alert(1)> — Zürich'
MODAL_ORIGINAL = AuthorModalContactView.cv_content_template
SUBMIT_KWARGS_ORIGINAL = AuthorModalContactForm.get_submit_button_kwargs


def submit_kwargs(form):
    return {**SUBMIT_KWARGS_ORIGINAL(form), "title": "Application submit hint", "data_cv_tooltip": "form"}


def recipe(name):
    text = (ROOT / "docs/reference/buttons.md").read_bytes().decode("utf-8")
    marker = f"<!-- tooltip-recipe: {name} -->"
    assert text.splitlines().count(marker) == 1
    matches = re.findall(rf"^{re.escape(marker)}\n```django\n(.*?)\n```(?=\n|$)", text, re.M | re.S)
    assert len(matches) == 1
    body = matches[0]
    if name != "raw-context":
        assert f'data-tooltip-recipe="{name}"' in body
        assert not re.search(r"tags/button/(?:action|menu_item)\.html|{%\s*cv_(?:button|render_button)\s", body)
    return body


recipes = {name: recipe(name) for name in ("action-leaf", "menu-leaf", "raw-context")}
recipe_hashes = {name: hashlib.sha256(body.encode()).hexdigest() for name, body in recipes.items()}


class NativeLoader(MemoryLoader):
    def get_template_sources(self, template_name):
        if custom_mode.get():
            yield from super().get_template_sources(template_name)


class FixtureMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        mode = request.COOKIES.get("tooltip_mode", "stock")
        token = custom_mode.set(mode == "custom")
        try:
            with ExitStack() as stack:
                scenario = request.COOKIES.get("tooltip_scenario", "smoke")
                if scenario in {"missing-icon", "failed-render"}:
                    stack.enter_context(override_settings(CRUD_VIEWS_STRICT=False))
                for cls, name, value in scenario_patches(request):
                    stack.enter_context(patch.object(cls, name, value))
                response = self.get_response(request)
                if hasattr(response, "render"):
                    response.render()
                response["X-Tooltip-Mode"] = mode
                response["X-Tooltip-Strict"] = str(settings.CRUD_VIEWS_STRICT)
                return response
        finally:
            custom_mode.reset(token)


def scenario_patches(request):
    scenario = request.COOKIES.get("tooltip_scenario", "smoke")
    patches = [
        (AuthorDetailView, "cv_context_actions", ["detail", "update", "delete"]),
        (AuthorDetailView, "cv_context_actions_inline", ["detail", "update", "delete"]),
        (AuthorListView, "cv_list_actions_inline", ["detail", "update", "delete"]),
        (AuthorUpdateView, "cv_action_label_template_code", "Update author {{ object }}"),
        (AuthorUpdateView, "cv_action_short_label_template_code", "Update"),
    ]
    mixed = {"detail": "label", "update": "icon", "delete": "both"}
    for cls, location in [(AuthorDetailView, "context"), (AuthorListView, "list")]:
        patches.append((cls, f"cv_{location}_actions_label_mode", mixed))
    if scenario.startswith("menu-"):
        mode = scenario.split("-")[1]
        for cls, location in [(AuthorDetailView, "context"), (AuthorListView, "list")]:
            patches += [
                (cls, f"cv_{location}_actions_inline", ["update"]),
                (cls, f"cv_{location}_actions_label_mode", dict.fromkeys(mixed, mode)),
            ]
        patches += [
            (
                AuthorCardListView,
                "cv_card_actions",
                [CardAction(key=key, label=key.title(), label_mode=mode) for key in mixed],
            ),
            (AuthorCardListView, "cv_card_actions_inline", ["update"]),
        ]
    if scenario == "permissions":
        patches += [
            (AuthorUpdateView, "cv_inaccessible_actions", "disable"),
            (AuthorDeleteView, "cv_inaccessible_actions", "hide"),
        ]
    if scenario.endswith("-denied"):
        patches += [
            (AuthorUpdateView, "cv_inaccessible_actions", "disable"),
            (AuthorDeleteView, "cv_inaccessible_actions", "hide"),
            (AuthorDetailView, "cv_context_actions_inline", ["detail"]),
            (AuthorListView, "cv_list_actions_inline", ["detail"]),
            (AuthorCardListView, "cv_card_actions_inline", ["detail"]),
        ]
    if scenario == "missing-icon":
        patches.append((AuthorUpdateView, "cv_icon_action", None))
    if scenario in {"empty-short", "both-empty", "empty-full"}:
        patches += [
            (AuthorUpdateView, "cv_action_label_template", None),
            (AuthorUpdateView, "cv_action_short_label_template", None),
            (
                AuthorUpdateView,
                "cv_action_label_template_code",
                "{% if False %}x{% endif %}" if scenario != "empty-short" else "Full fallback",
            ),
            (
                AuthorUpdateView,
                "cv_action_short_label_template_code",
                "Short only" if scenario == "empty-full" else "{% if False %}x{% endif %}",
            ),
        ]
    if scenario == "escaping":
        patches += [
            (AuthorUpdateView, "cv_action_label_template_code", "Full {{ object.pseudonym }} end"),
            (AuthorUpdateView, "cv_action_short_label_template_code", "{{ object.pseudonym }}"),
        ]
    if scenario == "post":
        patches += [
            (AuthorDetailView, "cv_context_actions", ["detail", "update", "ping"]),
            (AuthorDetailView, "cv_context_actions_inline", ["detail", "update", "ping"]),
        ]
    if scenario == "custom-label":
        patches += [
            (
                AuthorDetailView,
                "cv_context_buttons",
                [
                    ContextButton(
                        key="custom",
                        key_target="update",
                        label_template_code="Custom caption",
                        template_code=recipes["raw-context"],
                        label_mode="icon",
                    )
                ],
            ),
            (AuthorDetailView, "cv_context_actions", ["custom"]),
            (AuthorDetailView, "cv_context_actions_inline", ["custom"]),
        ]
    patches += [
        (AuthorModalContactForm, "get_submit_button_kwargs", submit_kwargs),
        (AuthorModalListView, "cv_list_actions", ["detail", "delete", "contact"]),
        (AuthorModalListView, "cv_list_actions_inline", ["detail", "delete", "contact"]),
        (AuthorModalContactView, "cv_content_template", "tooltip/modal.html"),
        (AuthorModalContactView, "cv_context_actions_label_mode", {"detail": "icon"}),
        (AuthorModalDetailView, "cv_action_label_template_code", "Full modal author {{ object }}"),
        (AuthorModalDetailView, "cv_action_short_label_template_code", "Inspect"),
    ]
    return patches


def signin(request):
    login(
        request,
        limited if request.GET.get("limited") == "1" else actor,
        backend="django.contrib.auth.backends.ModelBackend",
    )
    return JsonResponse({"author": str(author.pk), "name": str(author), "payload": PAYLOAD, "recipes": recipe_hashes})


def failed_render(request):
    raise ValueError("Intentional fixture render failure for strict-scope restoration")


urlpatterns = [
    path("__signin/", signin),
    path("__failed/", failed_render),
    path("favicon.ico", lambda request: HttpResponse(status=204)),
    path("", include("tests.test1.project.urls")),
]


def main():
    global actor, limited, author
    with tempfile.TemporaryDirectory(prefix="cv-tooltip-") as temporary:
        settings.DATABASES["default"]["NAME"] = str(Path(temporary) / "db.sqlite3")
        settings.MEDIA_ROOT = str(Path(temporary) / "media")
        templates = copy.deepcopy(settings.TEMPLATES)
        templates[0]["APP_DIRS"] = False
        templates[0]["OPTIONS"]["loaders"] = [
            (
                "__main__.NativeLoader",
                {
                    "crud_views/tags/button/action.html": recipes["action-leaf"],
                    "crud_views/tags/button/menu_item.html": recipes["menu-leaf"],
                    "tooltip/raw-context.html": recipes["raw-context"],
                },
            ),
            (
                "django.template.loaders.locmem.Loader",
                {
                    "tooltip/modal.html": '{% load crud_views %}{% cv_context_button "detail" %}'
                    '<button id="app-owned" title="Application hint" data-cv-tooltip="context">Custom visible</button>'
                    '{% include "' + MODAL_ORIGINAL + '" %}'
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
                actor = User.objects.create_superuser(username="tooltip-browser", password=None, email="")
                limited = User.objects.create_user(username="tooltip-view-only", password=None)
                limited.user_permissions.add(
                    Permission.objects.get(codename="view_author", content_type__app_label="app")
                )
                author = Author.objects.create(first_name="Browser", last_name="Author", pseudonym=PAYLOAD)
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
                                "recipes": recipe_hashes,
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
