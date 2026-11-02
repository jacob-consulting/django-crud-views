"""Execute the published theme and ownership migrations through real renderers."""

from pathlib import Path

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.template import Context, Template
from django.test import RequestFactory, override_settings
from lxml import html

from crud_views.lib import button_classes as bc
from crud_views.lib.view.label_mode import default_label_mode, register_label_mode_defaults
from tests.test1.test_form_frame import _theme_templates
from tests.test1.test_heading_docs import recipe
from tests.test1.test_theme_action_groups import OrdinaryForm, filter_helper, render_filter, render_group
from tests.test1.test_theme_form_ownership import _library_form, assert_owned_form_markup

ROOT = Path(__file__).resolve().parents[2]
THEME = ROOT / "docs/reference/theme.md"
MIGRATION = ROOT / "docs/migrating-1.0.md"


@pytest.fixture(autouse=True)
def isolate_class_registry(monkeypatch):
    monkeypatch.setattr(bc, "_THEME_BUTTON_CLASSES", dict(bc._THEME_BUTTON_CLASSES))
    bc.reset_button_classes_cache()
    yield
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
def test_copied_workflow_recipe(choices):
    context = _context(_library_form())
    context["has_workflow_choices"] = choices
    output = Template(recipe(THEME, "### Copied workflow action template")).render(context)
    if choices:
        assert_owned_form_markup(output)
    else:
        assert "<form" not in output and "csrfmiddlewaretoken" not in output
        assert "There are no workflow steps available" in output


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
