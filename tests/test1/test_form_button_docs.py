"""The published form-button recipes (06-08): the documented helpers and templates, executed and rendered for real.

Each recipe is taken from its page, not restated here: the filter-helper subclasses of list_view.md, and the
custom form-button template of theme.md. They render through real crispy (``{% crispy form helper %}``), the
custom template through an isolated locmem loader in front of the project's loaders.
"""

import ast
import copy
import logging
import re
from types import SimpleNamespace

import pytest
from crispy_forms.bootstrap import FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from django import forms
from django.template import Context, Template
from django.test import RequestFactory, override_settings
from lxml import html as lxml_html

from tests.test1.test_alerts import TEMPLATE_FENCE
from tests.test1.test_label_mode_docs import DOCS, FENCE, _flat, _section

LIST_VIEW_MD = DOCS / "reference" / "list_view.md"
THEME_MD = DOCS / "reference" / "theme.md"
TUTORIAL_MD = DOCS / "getting_started" / "tutorial-5-filters-permissions.md"

# a literal that breaks attributes, injects markup and looks like template code
HOSTILE = '"><script>alert(1)</script>{{ request.user }}&amp;'
GET = {"sort": "-last_name", "order": "name", "dir": "desc"}
HIDDEN = {"sort": "-last_name", "order": "name", "dir": "desc"}


def _exec_classes(code: str, names: set[str] | None = None) -> dict[str, type]:
    """Execute a documented fence: its imports and its class definitions (only ``names`` when given)."""
    tree = ast.parse(code)
    body = [
        node
        for node in tree.body
        if isinstance(node, (ast.Import, ast.ImportFrom))
        or (isinstance(node, ast.ClassDef) and (names is None or node.name in names))
    ]
    namespace: dict = {"__name__": "docs_recipe"}
    exec(compile(ast.Module(body=body, type_ignores=[]), "<docs>", "exec"), namespace)
    return {node.name: namespace[node.name] for node in body if isinstance(node, ast.ClassDef)}


def _filter_helpers() -> dict[str, type]:
    text = LIST_VIEW_MD.read_text()
    # the documented field-only subclass, from the filtering example (its view and filter set are not executed)
    (example, *_) = FENCE.findall(_section(text, "## Filtering with django-filter"))
    helpers = _exec_classes(example, {"AuthorFilterFormHelper"})
    for block in FENCE.findall(_section(text, "### Custom filter helpers")):
        helpers.update(_exec_classes(block))
    assert set(helpers) == {"AuthorFilterFormHelper", "SearchFilterFormHelper", "NoButtonsFilterFormHelper"}
    return helpers


class _AuthorFilterForm(forms.Form):
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)


def _helper(helper_class):
    request = RequestFactory().get("/authors/", GET)
    return helper_class(SimpleNamespace(), request)


def _render(form, helper, **extra) -> str:
    context = Context({"form": form, "helper": helper, **extra})
    return Template("{% load crispy_forms_tags %}{% crispy form helper %}").render(context)


def _parse(markup: str):
    return lxml_html.fragment_fromstring(markup, create_parent="div")


def _hidden(doc) -> dict[str, str]:
    return {el.get("name"): el.get("value") for el in doc.cssselect('input[type="hidden"]')}


def _fields(doc) -> list[str]:
    return [el.get("name") for el in doc.cssselect('input[type="text"]')]


def _buttons(doc) -> list[tuple[str, str, str, str]]:
    return [(b.get("id"), b.get("type"), b.get("name"), b.get("value")) for b in doc.cssselect("button")]


STOCK = [
    ("filter-button", "submit", "submit", "Apply Filter"),
    ("filter-button-reset", "reset", "reset", "Reset Filter"),
]


def test_documented_field_only_helper_appends_the_stock_actions_once():
    helpers = _filter_helpers()
    helper_class = helpers["AuthorFilterFormHelper"]
    declared = len(helper_class.layout.fields)

    helper = _helper(helper_class)
    first = _render(_AuthorFilterForm(), helper)
    doc = _parse(first)
    assert _fields(doc) == ["first_name", "last_name"]
    assert _buttons(doc) == STOCK
    assert _hidden(doc) == HIDDEN
    # the visible actions come before the pack's hidden-input wrapper
    markup = first
    assert markup.index('id="filter-button-reset"') < markup.index('name="sort"')

    # repeated renders and other instances neither accumulate actions nor touch the class layout
    assert _render(_AuthorFilterForm(), helper) == first
    assert _render(_AuthorFilterForm(), _helper(helper_class)) == first
    assert len(helper_class.layout.fields) == declared


def test_documented_replacement_hook_keeps_fields_and_hidden_inputs():
    helper = _helper(_filter_helpers()["SearchFilterFormHelper"])
    for _ in range(2):
        doc = _parse(_render(_AuthorFilterForm(), helper))
        assert _fields(doc) == ["first_name", "last_name"]
        assert _buttons(doc) == [("filter-button", "submit", "submit", "Search")]
        assert _hidden(doc) == HIDDEN


def test_documented_omission_hook_removes_only_the_actions(caplog, recwarn):
    helper = _helper(_filter_helpers()["NoButtonsFilterFormHelper"])
    with caplog.at_level(logging.WARNING):
        renders = [_render(_AuthorFilterForm(), helper) for _ in range(2)]
    assert renders[0] == renders[1]
    doc = _parse(renders[0])
    assert _fields(doc) == ["first_name", "last_name"]
    assert _buttons(doc) == []
    assert _hidden(doc) == HIDDEN
    assert not caplog.records and not recwarn.list


def test_clearing_inputs_no_longer_suppresses_the_actions(caplog, recwarn):
    """The pre-1.0 technique, as a changed-behavior regression: why the documented None hook is required."""
    helper = _helper(_filter_helpers()["AuthorFilterFormHelper"])
    helper.inputs = []
    with caplog.at_level(logging.WARNING):
        doc = _parse(_render(_AuthorFilterForm(), helper))
    # the stock layout actions stay, only the hidden GET controls went, and nothing warns about it
    assert _buttons(doc) == STOCK
    assert _fields(doc) == ["first_name", "last_name"]
    assert _hidden(doc) == {}
    assert not caplog.records and not recwarn.list


def test_suppression_recipe_is_linked_from_the_tutorial():
    tutorial = TUTORIAL_MD.read_text()
    assert "no submit button of its own" not in tutorial
    assert "(../reference/list_view.md#custom-filter-helpers)" in tutorial
    assert "get_form_actions()" in tutorial
    removing = _flat(_section(LIST_VIEW_MD.read_text(), "#### Removing the filter buttons"))
    for marker in ("self.inputs = []", "helper.inputs = []", "Nothing warns", "get_form_actions() to return None"):
        assert marker in removing, marker


# --- the custom form-button template recipe (theme.md) ---


def _theme_recipe() -> tuple[type, str, str]:
    section = _section(THEME_MD.read_text(), "## Custom form-button templates")
    (code,) = FENCE.findall(section)
    (template,) = TEMPLATE_FENCE.findall(section)
    (pill,) = _exec_classes(code).values()
    (saved,) = re.findall(r"`[\w/]+/templates/([\w/.-]+\.html)`", section)
    return pill, template, saved


PROBE = "probe[{{ input }}|{{ input.value }}|{{ form }}|{{ outer }}|{{ cv_value }}]"


@pytest.fixture
def recipe_templates(settings):
    """The documented template under its documented pack path, in an isolated locmem loader."""
    pill, template, saved = _theme_recipe()
    templates = copy.deepcopy(settings.TEMPLATES)
    engine = templates[0]
    engine["APP_DIRS"] = False
    engine["OPTIONS"]["loaders"] = [
        ("django.template.loaders.locmem.Loader", {saved: template, "probe/explicit.html": PROBE}),
        "django.template.loaders.filesystem.Loader",
        "django.template.loaders.app_directories.Loader",
    ]
    settings.TEMPLATES = templates
    return pill, saved


def _layout_helper(*buttons) -> FormHelper:
    helper = FormHelper()
    helper.form_tag = False
    helper.layout = Layout(FormActions(*buttons))
    return helper


def test_documented_pill_template_renders_literal_text(recipe_templates):
    pill, saved = recipe_templates
    # the class name keeps the pack placeholder; the documented file sits under the active pack
    assert pill.template == "%s/buttons/pill.html" and saved == "bootstrap5/buttons/pill.html"
    request = SimpleNamespace(user="ALICE")
    markup = _render(forms.Form(), _layout_helper(pill("submit", HOSTILE, data_note=HOSTILE)), request=request)
    assert "ALICE" not in markup and "<script" not in markup

    (button,) = _parse(markup).cssselect("button")
    assert "rounded-pill" in button.get("class").split()
    assert button.get("value") == HOSTILE and button.text_content().strip() == HOSTILE
    assert button.get("data-note") == HOSTILE
    assert set(button.attrib) == {"type", "name", "value", "id", "class", "data-note"}
    assert not button.cssselect("script, i") and button.get("title") is None


def test_documented_pill_template_keeps_icon_mode(recipe_templates):
    pill, _ = recipe_templates
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"form": "icon"}):
        (button,) = _parse(_render(forms.Form(), _layout_helper(pill("submit", HOSTILE)))).cssselect("button")
    assert "rounded-pill" in button.get("class").split()
    (hidden,) = button.cssselect("span.visually-hidden")
    assert hidden.text == HOSTILE
    assert (button.get("title"), button.get("data-cv-tooltip")) == (HOSTILE, "form")
    assert len(button.cssselect("i")) == 1


def test_custom_template_selection_and_scoped_context(recipe_templates):
    pill, _ = recipe_templates
    # an explicit template= wins over the subclass attribute; the template sees only the leaf contract
    markup = _render(
        forms.Form(), _layout_helper(pill("submit", "Go", template="probe/explicit.html")), input="IN", outer="OUT"
    )
    assert re.search(r"probe\[(.*?)\]", markup).group(1) == "||||Go"
