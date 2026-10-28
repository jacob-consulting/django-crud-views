"""The published form-button recipes (06-08): the documented helpers and templates, executed and rendered for real.

Each recipe is taken from its page, not restated here: the filter-helper subclasses of list_view.md, the
custom form-button templates of theme.md and the cancel-link opt-ins of buttons.md (06.1). They render through
real crispy (``{% crispy form helper %}``), the custom templates through an isolated locmem loader in front of the
project's loaders.
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

from crud_views.lib.crispy import Button
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


# --- cancel links (06.1): the published opt-in recipes of buttons.md and theme.md, executed for real ---

BUTTONS_MD = DOCS / "reference" / "buttons.md"
CANCEL_HEADING = "### Cancel links"
THEME_CANCEL_HEADING = "## Cancel links in custom form-button templates"
CANCEL_ID = "button-id-reset"


def _cancel_fences() -> dict[str, str]:
    """The python fences of the canonical cancel-link section, keyed by their first comment line."""
    fences: dict[str, str] = {}
    for code in FENCE.findall(_section(BUTTONS_MD.read_text(), CANCEL_HEADING)):
        first = code.splitlines()[0]
        assert first.startswith("# "), first
        assert first[2:] not in fences, first
        fences[first[2:]] = code
    return fences


def _exec_fence(code: str) -> dict:
    """Execute a whole documented fence and return its namespace."""
    namespace: dict = {"__name__": "docs_recipe"}
    exec(compile(code, "<docs>", "exec"), namespace)
    return namespace


@pytest.fixture
def isolated_theme_registry():
    """A8: a registration recipe touches the module-level theme layer; restore it even when the test fails."""
    import crud_views.lib.button_classes as bc

    snapshot = dict(bc._THEME_BUTTON_CLASSES)
    bc.reset_button_classes_cache()
    try:
        yield
    finally:
        bc._THEME_BUTTON_CLASSES.clear()
        bc._THEME_BUTTON_CLASSES.update(snapshot)
        bc.reset_button_classes_cache()


def _create_page(client, viewset) -> str:
    from tests.test1.test_crispy_buttons import url

    return client.get(url(viewset, "create")).content.decode()


def _page_cancel(markup: str):
    """The single element carrying the cancel id on a page."""
    (element,) = _parse(markup).xpath("//*[@id=$id]", id=CANCEL_ID)
    return element


def test_cancel_link_section_publishes_each_opt_in_path():
    assert set(_cancel_fences()) == {"myapp_theme/apps.py", "settings.py", "forms.py", "a layout of your own"}


@pytest.mark.django_db
def test_documented_theme_registration_renders_a_native_link(
    isolated_theme_registry, client_user_author_add, cv_author
):
    default = _page_cancel(_create_page(client_user_author_add, cv_author))
    assert default.tag == "button"
    destination = default.get("data-cv-cancel-url")
    assert destination

    tree = ast.parse(_cancel_fences()["myapp_theme/apps.py"])
    (ready,) = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "ready"]
    namespace = _exec_fence(ast.unparse(ast.Module(body=[ready], type_ignores=[])))
    namespace["ready"](None)

    link = _page_cancel(_create_page(client_user_author_add, cv_author))
    assert link.tag == "a" and link.get("href") == destination
    for omitted in ("type", "name", "value", "data-cv-cancel-url"):
        assert link.get(omitted) is None, omitted
    assert link.get("class") == default.get("class")


@pytest.mark.django_db
def test_documented_project_setting_renders_a_native_link(client_user_author_add, cv_author):
    classes = _exec_fence(_cancel_fences()["settings.py"])["CRUD_VIEWS_BUTTON_CLASSES"]
    assert classes == {"form:cancel-tag": "a"}
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES=classes):
        link = _page_cancel(_create_page(client_user_author_add, cv_author))
    assert link.tag == "a" and link.get("href")
    # the scoped setting is gone again: the default button returns
    assert _page_cancel(_create_page(client_user_author_add, cv_author)).tag == "button"


@pytest.mark.django_db
def test_documented_form_hooks_select_the_tag_per_form(client_user_author_add, cv_author, monkeypatch):
    from tests.test1.app.views import AuthorCreateView, AuthorForm

    recipes = _exec_classes(_cancel_fences()["forms.py"])
    assert set(recipes) == {"CancelLinkForm", "CancelButtonForm"}
    link_setting = _exec_fence(_cancel_fences()["settings.py"])["CRUD_VIEWS_BUTTON_CLASSES"]

    # the documented base classes, mixed into the test app's model form as a project would subclass them
    monkeypatch.setattr(AuthorCreateView, "form_class", type("F", (recipes["CancelLinkForm"], AuthorForm), {}))
    link = _page_cancel(_create_page(client_user_author_add, cv_author))
    assert link.tag == "a" and link.get("href") and link.get("data-cv-cancel-url") is None

    # the explicit button wins over a configured link
    monkeypatch.setattr(AuthorCreateView, "form_class", type("F", (recipes["CancelButtonForm"], AuthorForm), {}))
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES=link_setting):
        button = _page_cancel(_create_page(client_user_author_add, cv_author))
    assert button.tag == "button"
    assert (button.get("type"), button.get("name")) == ("button", "reset") and button.get("data-cv-cancel-url")


def test_documented_layout_renders_one_link_and_keeps_target_and_rel():
    namespace = _exec_fence(_cancel_fences()["a layout of your own"])
    doc = _parse(_render(forms.Form(), _layout_helper(namespace["actions"])))
    (link,) = doc.cssselect("a")
    assert (link.get("href"), link.get("id")) == ("/authors/", CANCEL_ID)
    assert _buttons(doc) == [("submit-id-submit", "submit", "submit", "Save")]

    (new_tab,) = _parse(_render(forms.Form(), _layout_helper(namespace["new_tab"]))).cssselect("a")
    # the caller's target and rel survive as given; nothing is added to or rewritten in rel
    assert (new_tab.get("href"), new_tab.get("target"), new_tab.get("rel")) == ("/authors/", "_blank", "noopener")
    assert set(new_tab.attrib) == {"href", "id", "class", "target", "rel"}


def test_documented_validation_and_legacy_input_boundaries():
    """The section's boundary claims, checked against the runtime."""
    from crud_views.lib.crispy import Button, Reset, Submit

    for bad in ("", "A", " a", "link", ["a"]):
        with pytest.raises(ValueError):
            Button("reset", "Back", tag=bad)
    for control in (Submit, Reset):
        with pytest.raises(ValueError):
            control("x", "X", tag="a")
    with pytest.raises(ValueError):
        Button("reset", "Back", tag="a", slot="form:submit")
    # an explicit "button" is accepted on any control
    Submit("submit", "Go", tag="button")

    # a valid link option on a helper input is checked, yet the input stays the pack's input
    helper = FormHelper()
    helper.form_tag = False
    helper.add_input(Button("reset", "Back", tag="a", data_cv_cancel_url="/b/"))
    doc = _parse(_render(forms.Form(), helper))
    assert doc.cssselect("a") == []
    (control,) = doc.cssselect("input")
    assert (control.get("type"), control.get("data-cv-cancel-url"), control.get("tag")) == ("button", "/b/", None)

    section = _flat(_section(BUTTONS_MD.read_text(), CANCEL_HEADING))
    for marker in (
        "crud_views.E365",
        "crud_views.E361",
        "helper.add_input()",
        'rel="noopener"',
        "not URL validation",
        "without JavaScript",
        "viewset.js",
        "cv_type, cv_name, cv_value and cv_cancel_url keep their values",
    ):
        assert marker in section, marker


# --- the cancel-capable custom template recipe (theme.md) ---


def _theme_cancel_recipe() -> tuple[type, str, str]:
    section = _section(THEME_MD.read_text(), THEME_CANCEL_HEADING)
    (code,) = FENCE.findall(section)
    (template,) = TEMPLATE_FENCE.findall(section)
    (cancel,) = _exec_classes(code).values()
    (saved,) = re.findall(r"`[\w/]+/templates/([\w/.-]+\.html)`", section)
    return cancel, template, saved


@pytest.fixture
def cancel_recipe_templates(settings):
    """Both documented templates, the button-only pill and the tag-aware cancel, in an isolated locmem loader."""
    _, pill_template, pill_saved = _theme_recipe()
    cancel, template, saved = _theme_cancel_recipe()
    templates = copy.deepcopy(settings.TEMPLATES)
    engine = templates[0]
    engine["APP_DIRS"] = False
    engine["OPTIONS"]["loaders"] = [
        ("django.template.loaders.locmem.Loader", {saved: template, pill_saved: pill_template}),
        "django.template.loaders.filesystem.Loader",
        "django.template.loaders.app_directories.Loader",
    ]
    settings.TEMPLATES = templates
    return cancel, saved, pill_saved


def _link_setting() -> dict:
    return _exec_fence(_cancel_fences()["settings.py"])["CRUD_VIEWS_BUTTON_CLASSES"]


def test_documented_cancel_template_renders_a_link_with_its_fields(cancel_recipe_templates):
    cancel, saved, _ = cancel_recipe_templates
    assert cancel.template == "%s/buttons/pill_cancel.html" and saved == "bootstrap5/buttons/pill_cancel.html"
    control = cancel("reset", HOSTILE, data_cv_cancel_url=HOSTILE, target="_blank", rel="noopener", data_note=HOSTILE)
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES=_link_setting()):
        markup = _render(forms.Form(), _layout_helper(control), request=SimpleNamespace(user="ALICE"))
    assert "ALICE" not in markup and "<script" not in markup
    doc = _parse(markup)
    assert doc.cssselect("button") == []
    (link,) = doc.cssselect("a")
    assert "rounded-pill" in link.get("class").split()
    assert link.get("href") == HOSTILE and link.text_content().strip() == HOSTILE
    assert (link.get("target"), link.get("rel"), link.get("data-note")) == ("_blank", "noopener", HOSTILE)
    assert set(link.attrib) == {"href", "id", "class", "target", "rel", "data-note"}
    (start,) = re.findall(r"<a\b(?:[^>\"']|\"[^\"]*\"|'[^']*')*>", markup)
    assert len(re.findall(r"(?<![\w-])href=", start, re.IGNORECASE)) == 1


def test_documented_cancel_template_keeps_the_button_branch(cancel_recipe_templates):
    cancel, _, _ = cancel_recipe_templates
    # unconfigured, and configured but overridden per button: the native button with its navigation marker
    renders = [_render(forms.Form(), _layout_helper(cancel("reset", "Back", data_cv_cancel_url="/b/")))]
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES=_link_setting()):
        renders.append(
            _render(forms.Form(), _layout_helper(cancel("reset", "Back", tag="button", data_cv_cancel_url="/b/")))
        )
        # a disabled cancel stays the native button, disabled
        disabled = _render(
            forms.Form(), _layout_helper(cancel("reset", "Back", data_cv_cancel_url="/b/", disabled=True))
        )
    for markup in renders:
        doc = _parse(markup)
        assert doc.cssselect("a") == []
        (button,) = doc.cssselect("button")
        assert "rounded-pill" in button.get("class").split()
        assert (button.get("type"), button.get("name"), button.get("value")) == ("button", "reset", "Back")
        assert button.get("data-cv-cancel-url") == "/b/"
    (button,) = _parse(disabled).cssselect("button")
    assert button.get("disabled") is not None and _parse(disabled).cssselect("a") == []


def test_documented_cancel_template_keeps_icon_mode(cancel_recipe_templates):
    cancel, _, _ = cancel_recipe_templates
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES=_link_setting(), CRUD_VIEWS_LABEL_MODE_DEFAULTS={"form": "icon"}):
        markup = _render(forms.Form(), _layout_helper(cancel("reset", HOSTILE, data_cv_cancel_url="/b/")))
    (link,) = _parse(markup).cssselect("a")
    (hidden,) = link.cssselect("span.visually-hidden")
    assert hidden.text == HOSTILE
    assert (link.get("title"), link.get("data-cv-tooltip")) == (HOSTILE, "form")
    assert len(link.cssselect("i")) == 1


def test_button_only_template_stays_usable_under_a_configured_link(cancel_recipe_templates):
    """D-16: the earlier pill template knows nothing of cv_tag; on a cancel it still renders its button, which still
    carries the navigation marker viewset.js reads."""
    _, _, pill_saved = cancel_recipe_templates
    control = Button("reset", "Back", template=pill_saved, data_cv_cancel_url="/b/")
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES=_link_setting()):
        doc = _parse(_render(forms.Form(), _layout_helper(control)))
    assert doc.cssselect("a") == []
    (button,) = doc.cssselect("button")
    assert (button.get("type"), button.get("data-cv-cancel-url")) == ("button", "/b/")
    assert "rounded-pill" in button.get("class").split()
