"""Library action groups add classes without replacing the active pack's contract."""

import importlib.metadata
import json
from types import SimpleNamespace

import pytest
from crispy_forms.bootstrap import FormActions
from crispy_forms.layout import HTML
from django import forms
from django.conf import settings
from django.template import Context
from django.template.loader import get_template
from django.test import override_settings
from lxml import html

from crud_views.lib.crispy import CrispyDeleteForm, CrispyForm

FLOOR_SOURCE = """<div{% if formactions.attrs %} {{ formactions.flat_attrs }}{% endif %} class="mb-3">
    {% if label_class %}
        <div class="aab {{ label_class }}"></div>
    {% endif %}

    <div class="{{ field_class }}">
        {{ fields_output|safe }}
    </div>
</div>
"""


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


def custom_templates(source, tmp_path=None):
    templates = [
        {
            **settings.TEMPLATES[0],
            "APP_DIRS": False,
            "OPTIONS": {
                **settings.TEMPLATES[0].get("OPTIONS", {}),
                "loaders": [
                    ("django.template.loaders.locmem.Loader", {"bootstrap5/layout/formactions.html": source}),
                    "django.template.loaders.app_directories.Loader",
                ],
            },
        }
    ]
    if tmp_path is not None:
        path = tmp_path / "bootstrap5/layout/formactions.html"
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
