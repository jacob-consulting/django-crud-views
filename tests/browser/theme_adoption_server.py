"""Isolated real Tabler source preparation and authenticated loopback acceptance server."""

import argparse
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
import theme_adoption_sources as sources  # noqa: E402

PARITY_METHODS = """
    def assert_message_parity(self, plain, themed):
        from html.parser import HTMLParser
        class Hooks(HTMLParser):
            def __init__(self):
                super().__init__()
                self.alerts = 0
                self.buttons = []
            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                if attrs.get("role") == "alert":
                    self.alerts += 1
                if tag == "button":
                    self.buttons.append(attrs)
        native, crud = Hooks(), Hooks()
        native.feed(plain)
        crud.feed(themed)
        self.assertGreater(native.alerts, 0)
        self.assertEqual(native.alerts, crud.alerts)
        self.assertEqual(len(native.buttons), native.alerts)
        self.assertEqual(len(crud.buttons), crud.alerts)
        for button in native.buttons:
            self.assertEqual(button.get("data-bs-dismiss"), "alert")
            self.assertNotIn("data-cv-alert-dismiss", button)
        for button in crud.buttons:
            self.assertEqual(button.get("data-cv-alert-dismiss"), "")
            self.assertNotIn("data-bs-dismiss", button)
        def normalized(value):
            return re.sub(r">\\s+<", "><", re.sub(r"\\s+", " ", value)).strip()
        self.assertEqual(normalized(plain.replace('data-bs-dismiss="alert"', 'data-cv-alert-dismiss=""')),
                         normalized(themed))

    def test_parity_rejects_wrong_missing_dual_hooks_and_unrelated_changes(self):
        messages = [Message(constants.INFO, "unchanged body")]
        native = render_to_string("django_tabler/includes/messages.html", {"messages": messages})
        crud = Template("{% load crud_views %}{% cv_messages %}").render(Context({"messages": messages}))
        self.assert_message_parity(native, crud)
        for changed in (
            crud.replace('data-cv-alert-dismiss=""', 'data-cv-alert-dismiss="wrong"'),
            crud.replace('data-cv-alert-dismiss=""', ''),
            crud.replace('data-cv-alert-dismiss=""', 'data-cv-alert-dismiss="" data-bs-dismiss="alert"'),
            crud.replace('role="alert"', 'role="status"'),
            crud.replace('unchanged body', 'changed body'),
        ):
            with self.subTest(changed=changed), self.assertRaises(AssertionError):
                self.assert_message_parity(native, changed)
"""

ADOPTION_TESTS = '''

class ThemeAdoptionTests(TestCase):
    """Native form floor, exact registrations and real action rendering contracts."""
    @classmethod
    def setUpTestData(cls):
        cls.actor = get_user_model().objects.create_superuser("adoption", "adoption@example.invalid", None)
        cls.customer = Customer.objects.create(name="Adoption")

    def setUp(self):
        self.client.force_login(self.actor)

    def controls(self, markup):
        from html.parser import HTMLParser
        class Controls(HTMLParser):
            def __init__(self):
                super().__init__()
                self.rows = []
                self.current = None
            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                if tag in ("button", "a"):
                    self.current = {"tag": tag, "attrs": attrs, "paths": [], "text": "", "hidden": False}
                elif self.current is not None and tag == "path" and attrs.get("stroke") != "none":
                    self.current["paths"].append(attrs.get("d"))
                elif self.current is not None and tag == "span" and "visually-hidden" in attrs.get("class", ""):
                    self.current["hidden"] = True
            def handle_data(self, data):
                if self.current is not None:
                    self.current["text"] += data
            def handle_endtag(self, tag):
                if tag in ("button", "a") and self.current is not None:
                    self.rows.append(self.current)
                    self.current = None
        parser = Controls()
        parser.feed(str(markup))
        return parser.rows

    def render_actions(self, mode=None, owner_mode=None, kind_mode=None, destination="absent", tag="button"):
        from crispy_forms.bootstrap import FormActions
        from crispy_forms.helper import FormHelper
        from crispy_forms.layout import Layout
        from crispy_forms.utils import render_crispy_form
        from crud_views.lib.crispy.buttons import Button, Submit
        from crud_views.lib.views.list import ListViewFilterFormHelper
        from crud_views.lib.view import CrudView
        class Owner(CrudView):
            cv_abstract = True
            cv_form_actions_label_mode = ({key: owner_mode for key in
                ("submit", "delete", "cancel", "filter-submit", "filter-reset")} if owner_mode else {}) | (
                {"cancel": kind_mode} if kind_mode else {})
        owner = Owner()
        form = ProbeForm(initial={"x": "initial"})
        form.cv_view = owner
        helper = FormHelper()
        helper.form_tag = False
        kwargs = {} if destination == "absent" else {"data_cv_cancel_url": None if destination == "none" else ""}
        helper.layout = Layout("x", FormActions(Submit("save", "Save"), Submit("delete", "Delete", slot="form:delete"),
                                               Button("cancel", "Cancel", tag=tag, **kwargs)))
        filtered = ProbeForm(initial={"x": "initial"})
        filtered.helper = ListViewFilterFormHelper(view=owner, request=RequestFactory().get("/"))
        filtered.helper.layout = Layout("x")
        with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={} if mode is None else {"form": mode}):
            markup = render_crispy_form(form, helper) + render_crispy_form(filtered, filtered.helper)
        return self.controls(markup), str(markup)

    def test_registered_floor_exact_maps_and_native_action_modes(self):
        from crud_views.lib.view.label_mode import default_label_mode
        with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={}):
            self.assertEqual(default_label_mode("form"), "both")
        self.assertEqual({name: TABLER_ICONS[name] for name in ("save", "cancel", "filter-reset")},
                         {"save": "tabler:check", "cancel": "tabler:arrow-left", "filter-reset": "tabler:filter-x"})
        self.assertEqual({name: TABLER_BUTTON_CLASSES[name] for name in
                          ("form:actions", "form:filter-actions", "alert:dismissible", "alert:close")},
                         {"form:actions": "d-flex flex-wrap gap-2", "form:filter-actions": "d-flex flex-wrap gap-1",
                          "alert:dismissible": "alert-dismissible fade show", "alert:close": "btn-close"})
        for mode in ("both", "icon", "label"):
            rows, markup = self.render_actions(mode)
            self.assertEqual(len(rows), 5)
            self.assertNotIn("fa-solid", markup)
            for row, name in zip(rows, ("check", "trash", "arrow-left", "filter", "filter-x"), strict=True):
                self.assertEqual(row["paths"], [] if mode == "label" else ICONS[name])
                self.assertTrue(row["text"].strip())
                self.assertEqual(row["hidden"], mode == "icon")
            self.assertEqual(rows[-1]["attrs"]["type"], "reset")
            self.assertTrue(rows[-1]["attrs"]["value"])
        rows, _ = self.render_actions("label", "icon", "both")
        self.assertTrue(rows[0]["hidden"])
        self.assertFalse(rows[2]["hidden"])
        self.assertEqual(rows[2]["paths"], ICONS["arrow-left"])
        self.assertEqual(self.render_actions()[0][0]["paths"], ICONS["check"])

    def test_missing_each_new_mapping_fails_native_render_assertion(self):
        from crud_views.lib import icons
        mappings = (("save", 0, "check"), ("cancel", 2, "arrow-left"), ("filter-reset", 4, "filter-x"))
        for name, position, glyph in mappings:
            with self.subTest(name=name), mock.patch.dict(icons._THEME_ICONS), override_settings(CRUD_VIEWS_ICONS={}):
                icons._THEME_ICONS.pop(name)
                icons.reset_icon_cache()
                rows, _ = self.render_actions("both")
                with self.assertRaises(AssertionError):
                    self.assertEqual(rows[position]["paths"], ICONS[glyph])

    def test_cancel_absent_none_empty_all_modes_and_requested_tags(self):
        for destination in ("absent", "none", "empty"):
            for tag in ("button", "a"):
                for mode in ("both", "icon", "label"):
                    with self.subTest(destination=destination, tag=tag, mode=mode):
                        rows, _ = self.render_actions(mode, destination=destination, tag=tag)
                        cancel = rows[2]
                        self.assertEqual(cancel["tag"], "button")
                        self.assertEqual(cancel["attrs"]["type"], "button")
                        self.assertNotIn("href", cancel["attrs"])
                        self.assertEqual("data-cv-cancel-url" in cancel["attrs"], destination == "empty")
                        self.assertEqual(cancel["attrs"].get("data-cv-cancel-url"),
                                         "" if destination == "empty" else None)
                        self.assertEqual(cancel["text"].strip(), "Cancel")
                        self.assertEqual(cancel["paths"], [] if mode == "label" else ICONS["arrow-left"])

    def test_real_create_update_delete_and_filter_pages_have_native_controls(self):
        for name, args in (("customer-create", []), ("customer-update", [self.customer.pk]),
                           ("customer-delete", [self.customer.pk]), ("customer-list", [])):
            with self.subTest(name=name):
                response = self.client.get(reverse(name, args=args))
                self.assertEqual(response.status_code, 200)
                markup = response.content.decode()
                self.assertNotIn("fa-solid", markup)
                self.assertNotIn("fa-regular", markup)
                glyph = "filter" if name == "customer-list" else "trash" if name == "customer-delete" else "check"
                self.assertTrue(any(row["paths"] == ICONS[glyph] for row in self.controls(markup)))
'''


def adapt(files):
    """Exact bounded candidate delta; original tracked source is never written."""
    files = dict(files)

    def replace(name, before, after):
        text = files[name].decode()
        sources.require(before in text, f"adaptation anchor changed: {name}")
        files[name] = text.replace(before, after, 1).encode()

    replace(
        "src/crud_views_tabler/apps.py",
        "        register_button_classes(TABLER_BUTTON_CLASSES)",
        "        from crud_views.lib.view.label_mode import register_label_mode_defaults\n\n"
        '        register_label_mode_defaults({"form": "both"})\n'
        "        register_button_classes(TABLER_BUTTON_CLASSES)",
    )
    for name in ("src/crud_views_tabler/buttons.py", "src/crud_views_tabler/tests.py"):
        indent = "            " if name.endswith("tests.py") else "    "
        anchor = indent + '"form:delete": "btn btn-danger",'
        entries = "\n".join(
            indent + json.dumps(k) + ": " + json.dumps(v) + "," for k, v in sources.ADOPTION_CLASSES.items()
        )
        replace(name, anchor, anchor + "\n" + entries)
    replace(
        "src/crud_views_tabler/icons.py",
        '    "delete": "tabler:trash",',
        '    "delete": "tabler:trash",\n'
        + "\n".join("    " + json.dumps(k) + ": " + json.dumps(v) + "," for k, v in sources.ADOPTION_ICONS.items()),
    )
    alert = "src/crud_views_tabler/templates/crud_views/tags/alert.html"
    replace(alert, " alert-dismissible fade show", ' {% cv_button_class "alert" "dismissible" %}')
    replace(
        alert,
        'class="btn-close" data-bs-dismiss="alert"',
        "class=\"{% cv_button_class 'alert' 'close' %}\" data-cv-alert-dismiss=\"\"",
    )
    tests = "src/crud_views_tabler/tests.py"
    replace(
        tests,
        "class MessagesParityTests(SimpleTestCase):",
        "class MessagesParityTests(SimpleTestCase):" + PARITY_METHODS,
    )
    replace(
        tests,
        "        self.assertEqual(normalized(plain), normalized(themed))",
        "        self.assert_message_parity(plain, themed)",
    )
    files[tests] += ADOPTION_TESTS.encode()
    return files


def current_core():
    return {
        p.relative_to(ROOT).as_posix(): p.read_bytes()
        for base in (ROOT / "src", ROOT / "tests", ROOT / "docs")
        for p in base.rglob("*")
        if p.is_file() and not p.is_symlink() and not set(p.parts) & sources.RUNTIME_EXCLUDES
    } | {
        name: (ROOT / name).read_bytes()
        for name in ("pyproject.toml", "package.json", "package-lock.json")
        if (ROOT / name).is_file()
    }


def prepare(target, delivered=None, full=False):
    baseline = sources.load_json(ROOT / sources.PHASE_DIR / sources.BASELINE_NAME)
    sources.check_baseline(baseline)
    original = sources.resolve_recorded_source(delivered or "recorded", manifest=baseline)
    before = sources.preservation(original)
    files = sources.archive_files(original, baseline["revision"])
    base_files = dict(files)
    patch_commands = []
    if delivered:
        # Read only tracked public bytes; private settings always come from the pinned archive.
        for name in files:
            if name != "example/config/settings.py":
                files[name] = (original / name).read_bytes()
    elif "CV_THEME_REPLAY_PATCH" in os.environ:
        patch_path = sources.absolute_path(os.environ["CV_THEME_REPLAY_PATCH"], "CV_THEME_REPLAY_PATCH")
        files = sources.patched_files(files, patch_path.read_text(), commands=patch_commands)
    else:
        files = adapt(files)
    core_files = current_core()
    core = Path(target) / "django-crud-views"
    companion = Path(target) / "tabler-test"
    sources.write_tree(core_files, core)
    sources.write_tree(files, companion)
    executable = sources.resolve_companion_python(baseline)
    origins, command = sources.probe_origins(executable, companion, core, files, core_files)
    focused = sources.command_record(
        [str(executable), "example/manage.py", "test", *sources.FOCUSED_TESTS, "--verbosity", "2"],
        companion,
        env=sources.isolated_env(companion, core),
    )
    focused_result = sources.suite_result(focused)
    nodes = [
        {"id": match[1], "outcome": "passed" if match[2] == "ok" else "failed"}
        for match in re.findall(r"^(test_\w+) \(([^)]+)\) \.\.\. (ok|FAIL|ERROR)$", focused["stderr"], re.M)
    ]
    suites = []
    if full:
        for argv in sources.suite_commands(executable):
            env = sources.isolated_env(companion, core)
            if "pytest" in argv:
                env.pop("DJANGO_SETTINGS_MODULE")
            result = sources.command_record(argv, companion, env=env)
            suites.append({"command": result, **sources.suite_result(result)})
    sources.require(sources.preservation(original) == before, "original changed during preparation")
    base_core = sources.archive_files(ROOT, baseline["core_revision"])
    source_inventory = sources.classify_tree(files, base_core)
    comparison = sources.compare_purposes(baseline["inventory"], source_inventory, base_files, files, base_core)
    return {
        "core": str(core),
        "companion": str(companion),
        "env": {
            key: value
            for key, value in sources.isolated_env(companion, core).items()
            if key
            in {"PYTHONPATH", "DJANGO_SETTINGS_MODULE", "DJANGO_SECRET_KEY", "DJANGO_DEBUG", "DJANGO_ALLOWED_HOSTS"}
        },
        "source_sha256": sources.digest(sources.inventory(files)),
        "bindings": {
            "source_sha256": sources.digest(sources.inventory(files)),
            "preserved_dirty_sha256": sources.digest(baseline["preserved"]),
            "index_preserved": sources.preservation(original) == before,
            "runtime_sha256": sources.digest(baseline["runtime"]),
            "config_sha256": sources.digest(baseline["test_configuration"]),
            "core_sha256": sources.digest(sources.inventory(core_files)),
        },
        "core_inventory": sources.inventory(core_files),
        "origins": origins,
        "origin_command": command,
        "preserved": before,
        "baseline_sha256": sources.digest(baseline),
        "inventory": source_inventory,
        "purpose_comparison": comparison,
        "patch_commands": patch_commands,
        "retired_purposes": {},
        "suite_comparison": [
            sources.compare_suite_failures(suite, baseline["suites"][index], base_files, files)
            for index, suite in enumerate(suites)
        ],
        "shadow_probes": {
            name: {"before_sha256": sources.digest(base_files[name]), "after_sha256": sources.digest(files[name])}
            for name in base_files
            if name
            in {
                "src/crud_views_tabler/templates/crud_views/tags/alert.html",
                "src/crud_views_tabler/templates/crud_views/snippets/form_frame.html",
                "src/crud_views_tabler/templates/crud_views/tags/list_filter.html",
                "src/crud_views_tabler/templates/crud_views/tags/list_filter.inner.html",
            }
        },
        "inherited_absent_copies": [
            name
            for name in (
                "src/crud_views_tabler/templates/crud_views/tags/form.html",
                "src/crud_views_tabler/templates/crud_views_workflow/view_workflow.action.html",
            )
            if name not in files
        ],
        "runtime": baseline["runtime"],
        "native_icons": sources.literal_assignment(files["src/django_tabler/icons.py"], "ICONS"),
        "focused_command": focused,
        "focused_result": focused_result,
        "test_nodes": nodes,
        "suites": suites,
        "isolated_roots": {"companion": str(companion), "core": str(core)},
        "adoption": {
            "label_modes": {"form": "both"},
            "classes": sources.ADOPTION_CLASSES,
            "icons": sources.ADOPTION_ICONS,
        },
    }


def serve():
    sys.path.insert(0, str(ROOT))
    os.environ.pop("DJANGO_SETTINGS_MODULE", None)
    text = os.environ.get("CV_THEME_PORT", "8145")
    if not re.fullmatch(r"[0-9]+", text) or not 1024 <= int(text) <= 65535 or int(text) in (8143, 8144):
        raise SystemExit("CV_THEME_PORT must be decimal 1024..65535; reserved ports: 8143, 8144")
    import signal
    import tempfile
    from html.parser import HTMLParser
    from unittest.mock import patch
    from wsgiref.simple_server import make_server

    from django.conf import settings

    temporary = tempfile.TemporaryDirectory(prefix="dcv-theme-db-")
    configure = settings.configure

    def themed_configure(self, **kwargs):
        kwargs["INSTALLED_APPS"][0:0] = ["django_tabler", "crud_views_tabler", "django.contrib.humanize"]
        kwargs["INSTALLED_APPS"] += ["dashboard", "catalog", "customers"]
        kwargs["CRUD_VIEWS_EXTENDS"] = "crud_views_tabler/page.html"
        kwargs["CRISPY_TEMPLATE_PACK"] = "crispy_tabler"
        kwargs["CRISPY_ALLOWED_TEMPLATE_PACKS"] = ["crispy_tabler"]
        kwargs["DATABASES"]["default"]["NAME"] = str(Path(temporary.name) / "db.sqlite3")
        kwargs["ALLOWED_HOSTS"] = ["127.0.0.1", "testserver"]
        kwargs["ROOT_URLCONF"] = __name__
        kwargs["TEMPLATES"][0]["DIRS"] = []
        configure(**kwargs)

    from tests.test1.conftest import pytest_configure

    with patch.object(type(settings), "configure", themed_configure):
        pytest_configure()

    from django import forms
    from django.contrib.auth import login
    from django.contrib.auth.models import User
    from django.contrib.messages import constants
    from django.contrib.messages.storage.base import Message
    from django.contrib.staticfiles.handlers import StaticFilesHandler
    from django.core.management import call_command
    from django.core.wsgi import get_wsgi_application
    from django.db import connection
    from django.http import HttpResponse, JsonResponse
    from django.middleware.csrf import get_token
    from django.template import RequestContext, Template
    from django.template.loader import get_template
    from django.test import override_settings
    from django.urls import include, path

    from crud_views.lib.conditional import ConditionalGroup, ConditionalGroupFormMixin, ModelFieldToggle, ToggleGroup
    from crud_views.lib.formsets import Formsets
    from crud_views_workflow.models import WorkflowInfo
    from tests.test1.app.models import Author, Book, Campaign, Publisher
    from tests.test1.app.views import (
        AuthorCreateView,
        AuthorForm,
        AuthorModalContactView,
        AuthorModalDeleteView,
        AuthorUpdateView,
        CampaignWorkflowView,
        PublisherListView,
        PublisherModalProtectedDeleteView,
    )
    from tests.test1.app.views_formset import (
        PublisherFormSetCreateView,
        PublisherFormSetForm,
        PublisherFormSetUpdateView,
    )

    call_command("migrate", run_syncdb=True, verbosity=0)
    actor = User.objects.create_superuser(username="theme-browser", password=None, email="")
    denied = User.objects.create_user(username="theme-denied", password=None)
    author = Author.objects.create(first_name="Native", last_name="Owner")
    campaign = Campaign.objects.create(name="Workflow with choices")
    no_choice = Campaign.objects.create(name="Workflow no choices")
    no_choice.wf_cancel_new(by=actor, comment="No choices fixture")
    no_choice.save()
    publisher = Publisher.objects.create(name="Parent")
    Book.objects.create(publisher=publisher, title="Protected child")
    CampaignWorkflowView.cv_modal = True
    mode_support = []
    for view in (AuthorCreateView, AuthorUpdateView):
        supported = view.cv_modal_supported
        with patch.object(view, "cv_modal", True):
            checks = [message.id for check in view.checks() for message in check.messages()]
        mode_support.append({"view": view.__name__, "supported": supported, "opt_in_checks": checks})

    class CancelForm(AuthorForm):
        def get_cancel_button_kwargs(self):
            query = self.cv_view.request.GET
            result = {"name": "cancel", "value": "Cancel", "tag": query.get("tag", "button")}
            if query.get("destination") in ("none", "empty"):
                result["data_cv_cancel_url"] = None if query["destination"] == "none" else ""
            return result

    class ConditionalParentForm(ConditionalGroupFormMixin, PublisherFormSetForm):
        enabled = forms.BooleanField(initial=True, required=False)
        contact = forms.CharField(initial="default contact", required=False)
        cv_conditional_groups = [ConditionalGroup(ModelFieldToggle("enabled"), ["contact"])]

        def get_layout_fields(self):
            return ["name", "enabled", ToggleGroup("enabled", "contact", legend="Contact"), Formsets()]

    observations = {"last": None, "history": []}

    class Forms(HTMLParser):
        def __init__(self):
            super().__init__()
            self.forms = []
            self.stack = []
            self.nested = []

        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            if tag == "form":
                if self.stack:
                    self.nested.append(attrs)
                form = {"attrs": attrs, "tokens": 0}
                self.forms.append(form)
                self.stack.append(form)
            if tag == "input" and attrs.get("name") == "csrfmiddlewaretoken" and self.stack:
                self.stack[-1]["tokens"] += 1

        def handle_endtag(self, tag):
            if tag == "form" and self.stack:
                self.stack.pop()

    def observed(request, view, **kwargs):
        templates = []
        render = Template._render

        def record(template, context):
            templates.append({"name": template.name, "origin": template.origin.name})
            return render(template, context)

        from contextlib import ExitStack

        with ExitStack() as stack:
            stack.enter_context(patch.object(Template, "_render", record))
            mode = request.GET.get("mode")
            project = {} if mode is None else {"form": mode}
            classes = {}
            if request.GET.get("classes") == "custom":
                classes = {
                    "form:actions": "ordinary-native",
                    "form:filter-actions": "filter-native",
                    "alert:dismissible": "native-dismissible",
                    "alert:close": "native-close",
                }
            elif request.GET.get("classes") == "empty":
                classes = dict.fromkeys(sources.ADOPTION_CLASSES, "")
            stack.enter_context(
                override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS=project, CRUD_VIEWS_BUTTON_CLASSES=classes)
            )
            if "owner" in request.GET:
                stack.enter_context(patch.object(view, "cv_form_actions_label_mode", {"submit": request.GET["owner"]}))
            if request.GET.get("pinned") == "1" and view is PublisherListView:
                stack.enter_context(patch.object(view, "cv_filter_pinned", True))
            if request.path == "/cancel/":
                stack.enter_context(patch.object(view, "form_class", CancelForm))
            if request.path.startswith("/parent-"):
                stack.enter_context(patch.object(view, "form_class", ConditionalParentForm))
            response = view.as_view()(request, **kwargs)
            if hasattr(response, "render"):
                response.render()
        if response.status_code in (200, 422) and "text/html" in response.get("Content-Type", ""):
            html = response.content.decode()
            if request.path.startswith("/parent-") and "</head>" in html:
                fixture_base = (ROOT / "tests/test1/app/templates/app/base.html").read_text()
                jquery = re.search(
                    r'<script\s+src="https://code.jquery.com/jquery-3.7.1.js".*?</script>', fixture_base, re.S
                ).group(0)
                html = html.replace("</head>", jquery + "</head>")
            token = get_token(request)
            auxiliary = "".join(
                f'<form id="aux-{name}" method="post"><input name="csrfmiddlewaretoken" value="{token}">'
                f'<input name="{name}"><button>{name}</button></form>'
                for name in ("search", "action")
            )
            launch = '<button id="launch" type="button" data-cv-modal="true" data-cv-url="/custom/">Open form</button>'
            response.content = html.replace("</body>", auxiliary + launch + "</body>")
            parsed = Forms()
            parsed.feed(response.content.decode())
            row = {
                "route": request.path,
                "method": request.method,
                "templates": templates,
                "modal": request.headers.get("X-CV-Modal") == "true",
                "status": response.status_code,
                "has_workflow_choices": getattr(response, "context_data", {}).get("has_workflow_choices"),
                "forms": parsed.forms,
                "nested": parsed.nested,
            }
            observations["last"] = row
            observations["history"].append(row)
        return response

    def signin(request):
        login(
            request, denied if request.GET.get("denied") else actor, backend="django.contrib.auth.backends.ModelBackend"
        )
        from crud_views.lib.button_classes import get_button_classes
        from crud_views.lib.icons import get_icons
        from crud_views.lib.view.label_mode import default_label_mode

        return JsonResponse(
            {
                "signed_in": True,
                "author": str(author.pk),
                "publisher": publisher.pk,
                "mode_support": mode_support,
                "adoption": {
                    "label_modes": {"form": default_label_mode("form")},
                    "classes": {key: get_button_classes()[key] for key in sources.ADOPTION_CLASSES},
                    "icons": {key: get_icons()[key] for key in sources.ADOPTION_ICONS},
                },
            }
        )

    def alerts(request):
        native = request.GET.get("native") == "1"
        body = (
            (
                '{% extends "django_tabler/layouts/app.html" %}{% block messages %}'
                '{% include "django_tabler/includes/messages.html" %}{% endblock %}'
            )
            if native
            else (
                '{% extends "crud_views_tabler/page.html" %}{% load crud_views %}{% block title %}Alerts{% endblock %}'
                "{% block page_title %}Alerts{% endblock %}{% block breadcrumb %}{% endblock %}"
                "{% block subtitle %}{% endblock %}{% block actions %}{% endblock %}"
            )
        )
        classes = (
            {}
            if request.GET.get("classes") not in ("custom", "empty")
            else {
                "alert:dismissible": "native-dismissible" if request.GET["classes"] == "custom" else "",
                "alert:close": "native-close" if request.GET["classes"] == "custom" else "",
            }
        )
        with override_settings(CRUD_VIEWS_BUTTON_CLASSES=classes):
            context = RequestContext(request)
            messages = [Message(constants.INFO, "First notice"), Message(constants.SUCCESS, "Second notice")]
            templates = []
            original_render = Template._render

            def record(template, context):
                templates.append({"name": template.name, "origin": template.origin.name})
                return original_render(template, context)

            with context.push(messages=messages), patch.object(Template, "_render", record):
                response = HttpResponse(Template(body).render(context))
            observations["last"] = {"route": request.path, "native": native, "templates": templates}
            return response

    def pack_probe(request):
        from crispy_forms.bootstrap import FormActions
        from django.template import Context

        from crud_views.lib.crispy.actions import _ThemedFormActions

        template = get_template("crispy_tabler/layout/formactions.html")
        ordinary = FormActions()
        with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"form:actions": "", "form:filter-actions": ""}):
            original = ordinary.render(forms.Form(), Context({}), template_pack="crispy_tabler")
            empty = _ThemedFormActions().render(forms.Form(), Context({}), template_pack="crispy_tabler")
        sentinel = 'native" & <class>'
        with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"form:actions": sentinel}):
            escaped = _ThemedFormActions().render(forms.Form(), Context({}), template_pack="crispy_tabler")
        return JsonResponse(
            {
                "origin": template.origin.name,
                "before_empty": original,
                "after_empty": empty,
                "sentinel": sentinel,
                "escaped": escaped,
            }
        )

    globals()["urlpatterns"] = [
        path("signin/", signin),
        path("create/", lambda request: observed(request, AuthorCreateView)),
        path("cancel/", lambda request: observed(request, AuthorCreateView)),
        path("update/", lambda request: observed(request, AuthorUpdateView, pk=author.pk)),
        path("custom/", lambda request: observed(request, AuthorModalContactView, pk=author.pk)),
        path("delete/", lambda request: observed(request, AuthorModalDeleteView, pk=author.pk)),
        path("workflow/", lambda request: observed(request, CampaignWorkflowView, pk=campaign.pk)),
        path("workflow-none/", lambda request: observed(request, CampaignWorkflowView, pk=no_choice.pk)),
        path("protected/", lambda request: observed(request, PublisherModalProtectedDeleteView, pk=publisher.pk)),
        path("filter/", lambda request: observed(request, PublisherListView)),
        path("parent-create/", lambda request: observed(request, PublisherFormSetCreateView)),
        path("parent-update/", lambda request: observed(request, PublisherFormSetUpdateView, pk=publisher.pk)),
        path("alerts/", alerts),
        path("pack-probe/", pack_probe),
        path(
            "snapshot/",
            lambda request: JsonResponse(
                {
                    "authors": list(Author.objects.values("first_name", "last_name")),
                    "books": list(Book.objects.values("title")),
                    "campaigns": list(Campaign.objects.values("name", "state")),
                    "workflow_history": list(WorkflowInfo.objects.values("transition", "workflow_object_pk")),
                }
            ),
        ),
        path("observations/", lambda request: JsonResponse(observations)),
        path("favicon.ico", lambda request: HttpResponse(status=204)),
        path("", include("tests.test1.project.urls")),
        path("", include("config.urls")),
    ]
    try:
        with make_server("127.0.0.1", int(text), StaticFilesHandler(get_wsgi_application())) as server:

            def stop(signum, frame):
                raise SystemExit(0)

            signal.signal(signal.SIGTERM, stop)
            print(json.dumps({"ready": int(text)}), flush=True)
            server.serve_forever()
    finally:
        connection.close()
        temporary.cleanup()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare")
    parser.add_argument("--delivered-source")
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--full", action="store_true")
    parser.add_argument("--preservation", action="store_true")
    args = parser.parse_args()
    if args.prepare:
        print(json.dumps(prepare(args.prepare, args.delivered_source, args.full)))
    elif args.serve:
        serve()
    elif args.preservation:
        print(json.dumps(sources.preservation(sources.resolve_recorded_source())))


if __name__ == "__main__":
    main()
