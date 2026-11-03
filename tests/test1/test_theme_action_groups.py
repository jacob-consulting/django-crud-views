"""Library action groups add classes without replacing the active pack's contract."""

import importlib.metadata
import json
import re
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest
from crispy_forms.bootstrap import FormActions
from crispy_forms.layout import HTML, Layout
from django import forms
from django.conf import settings
from django.template import Context, Template
from django.template.loader import get_template
from django.test import RequestFactory, override_settings
from django.utils.safestring import mark_safe
from lxml import html

from crud_views.lib import button_classes as bc
from crud_views.lib.crispy import CrispyDeleteForm, CrispyForm
from crud_views.lib.views.list import ListViewFilterFormHelper

FLOOR_SOURCE = """<div{% if formactions.attrs %} {{ formactions.flat_attrs }}{% endif %} class="mb-3">
    {% if label_class %}
        <div class="aab {{ label_class }}"></div>
    {% endif %}

    <div class="{{ field_class }}">
        {{ fields_output|safe }}
    </div>
</div>
"""


@pytest.fixture(autouse=True)
def isolate_classes():
    snapshot = dict(bc._THEME_BUTTON_CLASSES)
    bc.reset_button_classes_cache()
    yield
    bc._THEME_BUTTON_CLASSES.clear()
    bc._THEME_BUTTON_CLASSES.update(snapshot)
    bc.reset_button_classes_cache()


class OrdinaryForm(CrispyForm):
    def get_layout_fields(self):
        return []

    def get_cancel_button_kwargs(self):
        return {"name": "reset", "value": "Cancel", "data_cv_cancel_url": "/back/"}


class DeleteForm(CrispyDeleteForm):
    get_cancel_button_kwargs = OrdinaryForm.get_cancel_button_kwargs


def ordinary_group():
    return OrdinaryForm(None).get_form_actions()


def render_group(group, **context):
    return group.render(
        forms.Form(), Context({"field_class": "fields", "label_class": "labels", **context}), template_pack="bootstrap5"
    )


def test_pack_structure_probe():
    template = get_template("bootstrap5/layout/formactions.html")
    empty = render_group(FormActions(HTML("<b>Control</b>")))
    nonempty = render_group(FormActions(HTML("<b>Control</b>"), css_class="phase066-probe"))
    print(
        json.dumps(
            {
                "versions": {
                    name: importlib.metadata.version(name)
                    for name in ("Django", "django-crispy-forms", "crispy-bootstrap5")
                },
                "origin": template.origin.name,
                "source": template.template.source,
                "empty": empty,
                "nonempty": nonempty,
                "consumes_class": "phase066-probe" in nonempty,
            }
        )
    )
    assert "Control" in empty and "Control" in nonempty


def test_ordinary_group_classes():
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"form:actions": "phase066-sentinel"}):
        markup = render_group(ordinary_group())
    wrapper = html.fromstring(markup)
    assert "phase066-sentinel" in wrapper.classes
    assert "mb-3" in wrapper.classes
    assert [(b.get("name"), b.get("type")) for b in wrapper.cssselect("button")] == [
        ("submit", "submit"),
        ("reset", "button"),
    ]


@pytest.mark.parametrize("label_class", ["", "labels"])
def test_pack_structure_empty_matches_original_bytes(label_class):
    group = ordinary_group()
    original = FormActions(*group.fields)
    assert render_group(group, label_class=label_class) == render_group(original, label_class=label_class)


def test_ordinary_delete_group_classes():
    group = DeleteForm(None).helper.layout.fields[-1]
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"form:actions": "delete-sentinel"}):
        wrapper = html.fromstring(render_group(group))
    assert "delete-sentinel" in wrapper.classes
    assert wrapper.cssselect("button[name=delete]")[0].get("type") == "submit"


def test_pack_structure_installed_discriminator():
    from crud_views.lib.crispy.actions import _BOOTSTRAP5_FLOOR_SOURCE, _use_bootstrap5_floor_bridge

    template = get_template("bootstrap5/layout/formactions.html")
    assert _BOOTSTRAP5_FLOOR_SOURCE == FLOOR_SOURCE
    assert _use_bootstrap5_floor_bridge("bootstrap5", template) is (template.template.source == FLOOR_SOURCE)
    assert not _use_bootstrap5_floor_bridge("custom", template)


@pytest.mark.parametrize("change", ["origin", "attrs", "label", "field", "output", "whitespace"])
def test_pack_structure_discriminator_requires_full_match(change, tmp_path):
    from crud_views.lib.crispy.actions import _use_bootstrap5_floor_bridge

    installed = importlib.metadata.distribution("crispy-bootstrap5").locate_file(
        "crispy_bootstrap5/templates/bootstrap5/layout/formactions.html"
    )
    candidate = SimpleNamespace(
        origin=SimpleNamespace(name=str(installed)), template=SimpleNamespace(source=FLOOR_SOURCE)
    )
    assert _use_bootstrap5_floor_bridge("bootstrap5", candidate)
    if change == "origin":
        candidate.origin.name = str(tmp_path / "custom.html")
    else:
        needle = {
            "attrs": "flat_attrs",
            "label": "label_class",
            "field": "field_class",
            "output": "fields_output",
            "whitespace": "\n",
        }[change]
        candidate.template.source = FLOOR_SOURCE.replace(needle, "changed", 1)
    assert not _use_bootstrap5_floor_bridge("bootstrap5", candidate)


def custom_templates(source, tmp_path=None, name="bootstrap5/layout/formactions.html"):
    templates = [
        {
            **settings.TEMPLATES[0],
            "APP_DIRS": False,
            "OPTIONS": {
                **settings.TEMPLATES[0].get("OPTIONS", {}),
                "loaders": [
                    ("django.template.loaders.locmem.Loader", {name: source}),
                    "django.template.loaders.app_directories.Loader",
                ],
            },
        }
    ]
    if tmp_path is not None:
        path = tmp_path / name
        path.parent.mkdir(parents=True)
        path.write_text(source)
        templates[0]["DIRS"] = [str(tmp_path)]
        templates[0]["OPTIONS"]["loaders"][0] = "django.template.loaders.filesystem.Loader"
    return override_settings(TEMPLATES=templates)


@pytest.mark.parametrize("filesystem", [False, True])
def test_pack_structure_custom_origin_never_bridged(filesystem, tmp_path):
    from crud_views.lib.crispy.actions import _use_bootstrap5_floor_bridge

    group = ordinary_group()
    with custom_templates(FLOOR_SOURCE, tmp_path if filesystem else None):
        template = get_template("bootstrap5/layout/formactions.html")
        assert not _use_bootstrap5_floor_bridge("bootstrap5", template)
        with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"form:actions": "ignored-by-custom"}):
            assert "ignored-by-custom" not in render_group(group)
    # Same object, different loader selection: no global bridge capability cache.
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"form:actions": "back-to-installed"}):
        assert "back-to-installed" in render_group(group)


class FilterForm(forms.Form):
    q = forms.CharField(required=False)


def filter_helper(klass=ListViewFilterFormHelper):
    return klass(SimpleNamespace(), RequestFactory().get("/?sort=name&order=name&dir=desc"))


def render_filter(helper):
    return Template("{% load crispy_forms_tags %}{% crispy form helper %}").render(
        Context({"form": FilterForm(), "helper": helper})
    )


def filter_group(markup):
    tree = html.fragment_fromstring(markup, create_parent="div")
    return tree.cssselect("button[name=submit]")[0].getparent().getparent()


def test_filter_group_independence():
    classes = {"form:actions": "ordinary-only", "form:filter-actions": "filter-only"}
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES=classes):
        wrapper = filter_group(render_filter(filter_helper()))
        assert "filter-only" in wrapper.classes
        assert "ordinary-only" not in wrapper.classes
        ordinary = html.fromstring(render_group(ordinary_group()))
        assert "ordinary-only" in ordinary.classes and "filter-only" not in ordinary.classes


@pytest.mark.parametrize("key", ["form:actions", "form:filter-actions"])
def test_action_keys_are_empty_base_only_utilities(key):
    assert bc.DEFAULT_BUTTON_CLASSES[key] == ""
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={key: "gap-2"}):
        assert not [m for m in bc.button_class_check_messages() if m.id == "crud_views.W362"]
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={key + ":icon": "gap-2"}):
        assert len([m for m in bc.button_class_check_messages() if m.id == "crud_views.W362"]) == 1
    assert key.split(":")[1] not in bc.FORM_KINDS


def test_same_prepared_filter_reads_live_classes_and_deepcopy():
    helper = filter_helper()
    baseline = render_filter(helper)
    group = helper._cv_actions
    group.css_class = "authored"
    bc.register_button_classes({"form:filter-actions": "first"})
    assert filter_group(render_filter(helper)).classes == {"mb-3", "authored", "first"}
    bc.register_button_classes({"form:filter-actions": "second"})
    assert filter_group(render_filter(helper)).classes == {"mb-3", "authored", "second"}
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"form:filter-actions": "project"}):
        assert filter_group(render_filter(helper)).classes == {"mb-3", "authored", "project"}
        with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"form:filter-actions": None}):
            assert filter_group(render_filter(helper)).classes == {"mb-3", "authored"}
        assert filter_group(render_filter(helper)).classes == {"mb-3", "authored", "project"}
    for copied in (helper, deepcopy(helper)):
        assert filter_group(render_filter(copied)).classes == {"mb-3", "authored", "second"}
        assert render_filter(copied) == render_filter(copied)  # NOSONAR S5863: renders twice to prove determinism
        assert copied._cv_actions.css_class == "authored"
    assert helper._cv_actions is group
    group.css_class = None
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"form:filter-actions": ""}):
        assert render_filter(helper) == baseline


def test_filter_hidden_inputs_keep_the_pack_trailing_wrapper():
    helper = filter_helper()
    before = html.fragment_fromstring(render_filter(helper), create_parent="div")
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"form:filter-actions": "group-only"}):
        markup = render_filter(helper)
    tree = html.fragment_fromstring(markup, create_parent="div")
    hidden = tree.cssselect("input[type=hidden]")
    assert [(i.get("name"), i.get("value")) for i in hidden] == [("sort", "name"), ("order", "name"), ("dir", "desc")]
    wrapper = hidden[0].getparent().getparent()
    assert html.tostring(wrapper) == html.tostring(before.cssselect("input[type=hidden]")[0].getparent().getparent())
    assert "group-only" not in wrapper.classes
    assert not wrapper.cssselect("button")
    group = tree.cssselect("button[name=submit]")[0].getparent().getparent()
    assert group.getparent() is wrapper.getparent()
    assert list(group.getparent()).index(group) < list(wrapper.getparent()).index(wrapper)


@pytest.mark.parametrize("kind", ["none", "empty", "custom"])
def test_custom_filter_provider_keeps_ownership(kind):
    class CustomHelper(ListViewFilterFormHelper):
        layout = Layout("q")

        def get_form_actions(self):
            return {"none": None, "empty": FormActions(), "custom": HTML("<aside>Custom actions</aside>")}[kind]

    helper = filter_helper(CustomHelper)
    baseline = render_filter(helper)
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"form:filter-actions": "should-not-appear"}):
        assert render_filter(helper) == baseline
    assert not html.fragment_fromstring(baseline, create_parent="div").cssselect("button")


@pytest.mark.parametrize("base", [OrdinaryForm, ListViewFilterFormHelper])
def test_custom_group_opt_in(base):
    class Custom(base):
        def get_form_actions(self):
            group = super().get_form_actions()
            group.css_class = "authored"
            return group

    classes = {"form:actions": "theme", "form:filter-actions": "theme"}
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES=classes):
        if base is OrdinaryForm:
            wrapper = html.fromstring(render_group(Custom(None).get_form_actions()))
        else:
            wrapper = filter_group(render_filter(filter_helper(Custom)))
    assert {"mb-3", "authored", "theme"} <= wrapper.classes
    assert wrapper.get("class").split().count("theme") == 1


@pytest.mark.parametrize("pack", ["bootstrap5", "custom"])
@pytest.mark.parametrize("consumes", [True, False])
def test_custom_pack_keeps_its_own_structure_even_when_classes_are_ignored(pack, consumes):
    source = '<section class="native{% if formactions.css_class %} {{ formactions.css_class }}{% endif %}">'
    if not consumes:
        source = '<section class="native">'
    source += "<nav>{{ fields_output|safe }}</nav></section>"
    group = ordinary_group()
    classes = override_settings(CRUD_VIEWS_BUTTON_CLASSES={"form:actions": "sentinel"})
    with custom_templates(source, name=f"{pack}/layout/formactions.html"), classes:
        markup = group.render(forms.Form(), Context(), template_pack=pack)
    wrapper = html.fromstring(markup)
    assert wrapper.tag == "section"
    assert "native" in wrapper.classes
    assert ("sentinel" in wrapper.classes) is consumes
    assert len(wrapper.xpath("./nav/button")) == 2
    assert not wrapper.cssselect("div")


@pytest.mark.parametrize("safe", [False, True])
@pytest.mark.parametrize("factory,key", [(ordinary_group, "form:actions"), (filter_helper, "form:filter-actions")])
def test_hostile_group_classes_are_escaped(safe, factory, key):
    value = 'x" autofocus onfocus="alert(1)<img src=x onerror=alert(2)>'
    if safe:
        value = mark_safe(value)
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={key: value}):
        group = factory()
        markup = render_group(group) if factory is ordinary_group else render_filter(group)
    assert "&quot;" in markup and "&lt;img" in markup
    tree = html.fragment_fromstring(markup, create_parent="div")
    assert not tree.xpath(".//*[@autofocus or @onfocus or @onerror]")
    assert not tree.cssselect("img")


@pytest.mark.parametrize("label_class", ["", "grid-labels"])
def test_empty_pack_structure_preserves_authored_attrs_and_fields(label_class):
    group = ordinary_group()
    group.flat_attrs = 'data-owner="group"'
    group.attrs = {"data-owner": "group"}
    group.id = "authored-group"
    original = FormActions(*group.fields, css_id=group.id)
    original.flat_attrs = group.flat_attrs
    original.attrs = group.attrs
    assert render_group(group, label_class=label_class) == render_group(original, label_class=label_class)


@pytest.mark.parametrize("base", [OrdinaryForm, ListViewFilterFormHelper])
def test_documented_custom_opt_in_keeps_native_controls(base):
    document = (Path(__file__).resolve().parents[2] / "docs/reference/buttons.md").read_text()
    snippet = next(
        code for code in re.findall(r"```python\n(.*?)```", document, re.S) if "class ActionClassesMixin:" in code
    )
    namespace = {}
    exec(compile(snippet, "docs/reference/buttons.md", "exec"), namespace)
    custom = type("Documented", (namespace["ActionClassesMixin"], base), {})
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"form:actions": "theme", "form:filter-actions": "theme"}):
        if base is OrdinaryForm:
            group = html.fromstring(render_group(custom(None).get_form_actions()))
            expected = [("submit", "submit"), ("reset", "button")]
        else:
            group = filter_group(render_filter(filter_helper(custom)))
            expected = [("submit", "submit"), ("reset", "reset")]
    assert {"mb-3", "my-actions", "theme"} <= group.classes
    assert [(b.get("name"), b.get("type")) for b in group.cssselect("button")] == expected
