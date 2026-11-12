"""Execute the published theme and ownership migrations through real renderers."""

import re
import subprocess
import sys
from pathlib import Path

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.template import Context, Template
from django.test import RequestFactory, override_settings
from lxml import html

from crud_views.lib import button_classes as bc
from crud_views.lib.view.label_mode import default_label_mode, register_label_mode_defaults
from tests.test1.test_form_frame import THEME_FRAME, _theme_templates
from tests.test1.test_heading_docs import recipe
from tests.test1.test_theme_action_groups import OrdinaryForm, filter_helper, render_filter, render_group
from tests.test1.test_theme_form_ownership import _library_form, assert_owned_form_markup

ROOT = Path(__file__).resolve().parents[2]
THEME = ROOT / "docs/reference/theme.md"
MIGRATION = ROOT / "docs/migrating-1.0.md"
WORKFLOW = ROOT / "docs/reference/workflow_view.md"
BUTTONS = ROOT / "docs/reference/buttons.md"


@pytest.fixture(autouse=True)
def isolate_class_registry():
    snapshot = dict(bc._THEME_BUTTON_CLASSES)
    bc.reset_button_classes_cache()
    yield
    bc._THEME_BUTTON_CLASSES.clear()
    bc._THEME_BUTTON_CLASSES.update(snapshot)
    bc.reset_button_classes_cache()


def _python(section, path=THEME):
    namespace = {}
    exec(compile(recipe(path, section, "python"), str(path), "exec"), namespace)
    return namespace


def _context(form):
    return Context(
        {
            "form": form,
            "csrf_token": "docs-token",
            "request": RequestFactory().get("/save/?from=docs"),
            "form_id": 'owner" onmouseover="bad',
            "view": None,
        }
    )


def test_theme_registration_recipe():
    namespace = _python("### Register theme defaults")
    namespace["ready"](None)
    assert default_label_mode("form") == "both"
    for key, value in {
        "form:actions": "d-flex flex-wrap gap-2",
        "form:filter-actions": "d-flex flex-wrap gap-1",
        "alert:dismissible": "notice-dismissible",
        "alert:close": "notice-close",
    }.items():
        assert bc.get_button_class(*key.split(":")) == value
    rendered = render_group(OrdinaryForm(None).get_form_actions())
    tree = html.fromstring(rendered)
    assert tree.cssselect("button[name=submit] i")
    assert "gap-2" in tree.classes
    register_label_mode_defaults({"form": "icon"})
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"form": "label"}):
        assert default_label_mode("form") == "label"
    assert default_label_mode("form") == "icon"
    with pytest.raises(ValueError):
        register_label_mode_defaults({"form": "label", "unknown": "icon"})
    assert default_label_mode("form") == "icon"
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"form": "bad"}, CRUD_VIEWS_STRICT=False):
        assert default_label_mode("form") == "icon"
    with (
        override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"form": "bad"}, CRUD_VIEWS_STRICT=True),
        pytest.raises(ValueError, match="CRUD_VIEWS_LABEL_MODE_DEFAULTS"),
    ):
        default_label_mode("form")


@pytest.mark.parametrize("strict", [False, True])
def test_page_owned_form_recipe(strict, monkeypatch):
    form_class = _python("### Computed helper recipe")["ContactForm"]
    original = form_class.helper.fget
    helpers = []

    def selected(self):
        helper = original(self)
        helpers.append((helper, dict(helper.__dict__), list(helper.layout.fields)))
        return helper

    monkeypatch.setattr(form_class, "helper", property(selected))
    form = form_class(initial={"name": '<img src=x onerror="bad"> & literal'})
    with (
        override_settings(CRUD_VIEWS_STRICT=strict),
        _theme_templates({"crud_views/tags/form.html": recipe(THEME, "### Copied inner form template")}),
    ):
        output = Template(recipe(THEME, "### Page-owned form recipe")).render(_context(form))
    owner = assert_owned_form_markup(output)
    assert owner["attrs"]["action"] == "/save/?from=docs"
    assert owner["attrs"]["enctype"] == "multipart/form-data"
    assert owner["attrs"]["id"] == 'owner" onmouseover="bad'
    tree = html.fromstring(output)
    assert not tree.cssselect("img, [onerror], [onmouseover]")
    assert tree.cssselect("input[name=name]")[0].get("value") == '<img src=x onerror="bad"> & literal'
    assert len(helpers) == 1
    helper, before, fields = helpers[0]
    assert helper.__dict__ == before and helper.layout.fields == fields
    assert helper.disable_csrf is False


@pytest.mark.parametrize("strict", [False, True])
@pytest.mark.parametrize("configuration", ["wrapping", "unused-action"])
def test_published_renderer_rejects_or_warns_helper_configuration(strict, configuration, caplog):
    form = _python("### Computed helper recipe")["ContactForm"]()
    helper = form.helper
    if configuration == "wrapping":
        helper.form_tag = True
    else:
        helper.form_action = "/ignored/"

    # A fixed application helper exercises the same published renderer as a computed helper.
    class FixedForm(type(form)):
        pass

    FixedForm.helper = helper
    form = FixedForm()
    template = Template(recipe(THEME, "### Page-owned form recipe"))
    with override_settings(CRUD_VIEWS_STRICT=strict):
        if strict or configuration == "wrapping":
            with pytest.raises(ImproperlyConfigured, match=r"form_tag=False|form_action"):
                template.render(_context(form))
        else:
            owner = assert_owned_form_markup(template.render(_context(form)))
            assert owner["attrs"]["action"] == "/save/?from=docs"
            assert "form_action" in caplog.text


def test_standalone_library_form_recipe():
    form = _library_form()
    output = Template(recipe(THEME, "### Standalone library form recipe")).render(_context(form))
    assert_owned_form_markup(output)
    assert 'name="first_name"' in output


@pytest.mark.parametrize("choices", [False, True])
@pytest.mark.parametrize("modal", [False, True])
@pytest.mark.parametrize(
    "path,section", [(THEME, "### Copied workflow action template"), (MIGRATION, "### Workflow action body")]
)
def test_copied_workflow_recipe(choices, modal, path, section):
    hostile = '<img src=x onerror="bad"> & literal'
    context = _context(_python("### Computed helper recipe")["ContactForm"](initial={"name": hostile}))
    context["request"] = RequestFactory().get("/save/?from=docs", headers={"X-CV-Modal": str(modal).lower()})
    context["has_workflow_choices"] = choices
    with _theme_templates({"crud_views/snippets/form_frame.html": THEME_FRAME}):
        output = Template(recipe(path, section)).render(context)
    tree = html.fragment_fromstring(output, create_parent="div")
    frames = tree.cssselect(".theme-card")
    assert len(frames) == (0 if modal else 1)
    region = tree if modal else frames[0]
    assert not tree.cssselect("img, [onerror]")
    if choices:
        owner = assert_owned_form_markup(output)
        assert "action" not in owner["attrs"]  # Preserve the workflow's implicit current-page target.
        assert len(region.cssselect("form")) == 1
        assert len(region.cssselect("input[name=csrfmiddlewaretoken]")) == 1
        assert len(region.cssselect("h5")) == 1
        assert "Workflow Action" in region.cssselect("h5")[0].text_content()
        assert region.cssselect("input[name=name]")[0].get("value") == hostile
    else:
        assert "<form" not in output and "csrfmiddlewaretoken" not in output
        assert not region.cssselect("h5, button, input")
        assert "There are no workflow steps available" in region.text_content()


def test_workflow_presentation_docs():
    from django.db import models

    from crud_views_workflow.apps import CrudViewsWorkflowConfig
    from crud_views_workflow.lib import WorkflowModelMixin

    class States(models.TextChoices):
        SUCCESS = "success", '<img src=x onerror="bad"> & success'
        PURPLE = "purple", "Purple"
        WARNING = "warning", "Warning"
        DARK = "dark", "Dark"
        UNMAPPED = "unmapped", "Unmapped"

    class Example(WorkflowModelMixin):
        STATE_CHOICES = States
        STATE_BADGES = {state: state.value for state in States if state != States.UNMAPPED}

    model = Example()

    def badge(state):
        return html.fromstring(model.get_state_badge(state))

    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={}):
        assert badge(States.PURPLE).get("class") == "badge rounded-pill text-bg-purple"
        assert badge(States.UNMAPPED).get("class") == "badge rounded-pill text-bg-info"
        _python("### Optional workflow classes")["ready"](None)
        assert badge(States.SUCCESS).get("class") == "badge bg-success-lt"
        assert badge(States.PURPLE).get("class") == "badge custom-purple"
        assert badge(States.UNMAPPED).get("class") == "badge bg-info-lt"
        overrides = _python("### Project workflow classes", WORKFLOW)["CRUD_VIEWS_BUTTON_CLASSES"]
        with override_settings(CRUD_VIEWS_BUTTON_CLASSES=overrides):
            for state, classes in (
                (States.SUCCESS, "badge project-success"),
                (States.PURPLE, "badge project-purple"),
                (States.WARNING, ""),
                (States.DARK, ""),
            ):
                node = badge(state)
                assert node.get("class") == classes
                assert node.text_content() == state.label
                assert len(node) == 0
            assert bc.get_button_class("workflow", "history-table") == "table table-striped"
        assert badge(States.SUCCESS).get("class") == "badge bg-success-lt"

    text = BUTTONS.read_text()
    section = text.split("### Optional workflow defaults\n", 1)[1].split("\n### ", 1)[0]
    documented = dict(re.findall(r"^\| `(workflow:[^`]+)` \| `([^`]+)` \|$", section, re.M))
    assert documented == CrudViewsWorkflowConfig.crud_views_button_class_defaults
    assert len(bc.DEFAULT_BUTTON_CLASSES) == 102
    assert len(bc._get_default_button_classes()) == 112
    assert "112 effective default keys" in section
    precedence = text.split("### Precedence\n", 1)[1].split("\n## ", 1)[0]
    assert "core defaults + installed-app defaults + theme registrations + CRUD_VIEWS_BUTTON_CLASSES" in precedence
    assert "collisions with core or another app's defaults are rejected" in precedence
    row = next(line for line in text.splitlines() if line.startswith("| `crud_views.W362` |"))
    for phrase in (
        "effective core/installed-app defaults",
        "With workflow installed",
        "one nonempty colour segment without whitespace or colon",
        "custom colours need not occur in the default table",
        "Workflow keys warn when workflow is absent",
    ):
        assert phrase in row


@pytest.mark.parametrize("installed", [False, True])
def test_workflow_optional_registration_recipe(installed):
    published = recipe(THEME, "### Optional workflow classes", "python")
    # A fresh setup executes the actual published ready method during app discovery, before requests.
    source = """
import sys
from types import ModuleType
import django
from django.apps import AppConfig
from django.conf import settings
from django.test import override_settings

theme = ModuleType("workflow_docs_probe")
theme.__file__ = "workflow_docs_probe.py"
sys.modules[theme.__name__] = theme
providers = ["workflow_docs_probe.ThemeConfig"]
if INSTALLED:
    providers.append("crud_views_workflow")
settings.configure(
    SECRET_KEY="docs-probe",
    INSTALLED_APPS=["django.contrib.auth", "django.contrib.contenttypes", "crud_views", *providers],
)
namespace = {}
exec(compile(PUBLISHED, "docs/reference/theme.md", "exec"), namespace)
class ThemeConfig(AppConfig):
    name = "workflow_docs_probe"
    path = "."
    ready = namespace["ready"]
theme.ThemeConfig = ThemeConfig
django.setup()
from crud_views.lib import button_classes as bc
assert bc.get_button_class("form", "actions") == "d-flex flex-wrap gap-2"
assert not bc.button_class_check_messages()
registered = {key for key in bc._THEME_BUTTON_CLASSES if key.startswith("workflow:")}
assert bool(registered) == INSTALLED
assert "workflow:badge-purple" not in bc._get_default_button_classes()
if INSTALLED:
    assert bc.get_button_class("workflow", "badge-purple") == "badge custom-purple"

# Independently check the documented warning rule for settings and direct theme registrations.
for layer in ("settings", "theme"):
    for key, valid in (
        ("workflow:badge-purple", True),
        ("workflow:badge-", False),
        ("workflow:badge-pur ple", False),
        ("workflow:badge-purple:icon", False),
    ):
        snapshot = dict(bc._THEME_BUTTON_CLASSES)
        try:
            with override_settings(CRUD_VIEWS_BUTTON_CLASSES={key: "classes"} if layer == "settings" else {}):
                if layer == "theme":
                    bc.register_button_classes({key: "classes"})
                messages = [m.id for m in bc.button_class_check_messages() if repr(key) in m.msg]
                assert messages == ([] if INSTALLED and valid else ["crud_views.W362"]), (key, messages)
        finally:
            bc._THEME_BUTTON_CLASSES.clear()
            bc._THEME_BUTTON_CLASSES.update(snapshot)
            bc.reset_button_classes_cache()
"""
    result = subprocess.run(
        [sys.executable, "-c", f"INSTALLED = {installed!r}\nPUBLISHED = {published!r}\n" + source],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("kind", ["ordinary", "filter"])
def test_custom_actions_recipe(kind):
    mixin = _python("### Custom action-group opt-in")["SpacedActions"]
    if kind == "ordinary":
        form_class = type("StyledForm", (mixin, OrdinaryForm), {})
        with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"form:actions": "project-group"}):
            output = render_group(form_class(None).get_form_actions())
    else:
        from crud_views.lib.views.list import ListViewFilterFormHelper

        helper_class = type("StyledFilter", (mixin, ListViewFilterFormHelper), {})
        with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"form:filter-actions": "project-group"}):
            output = render_filter(filter_helper(helper_class))
    tree = html.fragment_fromstring(output, create_parent="div")
    assert tree.cssselect(".project-group.theme-actions")
    assert tree.cssselect("button[name=submit]")[0].get("type") == "submit"


def test_breaking_migration_pair():
    unreleased = (ROOT / "CHANGELOG.md").read_text().split("## Unreleased", 1)[1].split("\n## ", 1)[0]
    migration = MIGRATION.read_text()
    for title, anchor in (
        ("Page-owned forms and helpers", "page-owned-forms-and-helpers"),
        ("Copied form and workflow templates", "copied-form-and-workflow-templates"),
        ("Standalone library form wrappers", "standalone-library-form-wrappers"),
    ):
        assert f"**{title}.**" in unreleased
        assert f"docs/migrating-1.0.md#{anchor}" in unreleased
        assert migration.count(f"### {title}\n") == 1
    assert "nested forms and duplicate CSRF tokens" in unreleased.split("### Fixed", 1)[1]


@pytest.mark.parametrize("strict", [False, True])
def test_immediate_helper_migration(strict):
    form = _python("### Page-owned forms and helpers", MIGRATION)["ContactForm"](initial={"name": "<b>literal</b>"})
    with override_settings(CRUD_VIEWS_STRICT=strict):
        output = Template(recipe(MIGRATION, "### Page-owned forms and helpers")).render(_context(form))
    owner = assert_owned_form_markup(output)
    assert owner["attrs"]["method"] == "post"
    assert owner["attrs"]["action"] == "/save/?from=docs"
    assert owner["attrs"]["enctype"] == "multipart/form-data"
    assert not html.fromstring(output).cssselect("b, [onmouseover]")


@pytest.mark.parametrize("choices", [False, True])
def test_immediate_copied_template_migration(choices):
    context = _context(_library_form())
    context["has_workflow_choices"] = choices
    with _theme_templates({"crud_views/tags/form.html": recipe(MIGRATION, "### Selected inner helper")}):
        output = Template(recipe(MIGRATION, "### Workflow action body")).render(context)
    if choices:
        assert_owned_form_markup(output)
    else:
        assert "<form" not in output and "csrfmiddlewaretoken" not in output


def test_immediate_standalone_migration():
    output = Template(recipe(MIGRATION, "### Standalone library form wrappers")).render(_context(_library_form()))
    assert_owned_form_markup(output)
