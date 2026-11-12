"""Numbered columns resolve theme classes without taking ownership of custom templates."""

from copy import deepcopy

import pytest
from crispy_forms.layout import Column
from django import forms
from django.template import Context
from django.test import override_settings
from lxml import html

from crud_views.lib import button_classes as bc
from crud_views.lib.crispy import Column6
from crud_views.lib.crispy import table as columns


@pytest.fixture(autouse=True)
def isolate_classes():
    snapshot = dict(bc._THEME_BUTTON_CLASSES)
    bc.reset_button_classes_cache()
    yield
    bc._THEME_BUTTON_CLASSES.clear()
    bc._THEME_BUTTON_CLASSES.update(snapshot)
    bc.reset_button_classes_cache()


class ExampleForm(forms.Form):
    crispy_field_template = None
    name = forms.CharField()
    other = forms.CharField(required=False)


def render_column(column, context=None, form=None, template_pack="bootstrap5"):
    return column.render(
        form if form is not None else ExampleForm({"name": "Ada"}),
        context if context is not None else Context(),
        template_pack=template_pack,
    )


def test_column6_theme_tracer():
    column = Column6("name", css_class="extra")
    original = deepcopy(vars(column))
    context = Context({"div": "outer", "fields": "outer-fields", "sentinel": object()})
    surrounding = context.flatten()
    bc.register_button_classes({"form:column-6": "span-6"})
    for _ in range(2):
        wrapper = html.fromstring(render_column(column, context=context))
        assert set(wrapper.classes) == {"span-6", "extra"}
        assert wrapper.cssselect("input[name=name]")[0].get("value") == "Ada"
        assert vars(column) == original
        assert all(context[key] == value for key, value in surrounding.items())


@pytest.mark.parametrize("width", range(1, 13))
def test_default_column_bytes(width):
    helper = getattr(columns, f"Column{width}")
    assert helper.css_class == f"col-md-{width}"
    kwargs = {"css_id": "wrapper", "data_test": "column", "css_class": "extra"}
    assert render_column(helper("name", **kwargs)) == render_column(
        Column("name", css_class=f"col-md-{width} extra", css_id="wrapper", data_test="column")
    )


@pytest.mark.parametrize("width", range(1, 13))
@pytest.mark.parametrize("value", ["span-6", "col-12 col-lg-6", "", None])
@pytest.mark.parametrize("extra", [None, "extra"])
def test_column_theme_and_project_layers(width, value, extra):
    column = getattr(columns, f"Column{width}")("name", css_class=extra)
    original = deepcopy(vars(column))
    key = f"form:column-{width}"
    bc.register_button_classes({key: value})
    expected = set((value or "").split()) | ({extra} if extra else set())
    assert set(html.fromstring(render_column(column)).classes) == expected
    other_width = width % 12 + 1
    other = getattr(columns, f"Column{other_width}")("name")
    assert set(html.fromstring(render_column(other)).classes) == {f"col-md-{other_width}"}
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={key: "project"}):
        assert set(html.fromstring(render_column(column)).classes) == {"project"} | ({extra} if extra else set())
    assert set(html.fromstring(render_column(column)).classes) == expected
    bc.register_button_classes({key: "new-theme"})
    assert set(html.fromstring(render_column(column)).classes) == {"new-theme"} | ({extra} if extra else set())
    for suppressed in ("", None):
        with override_settings(CRUD_VIEWS_BUTTON_CLASSES={key: suppressed}):
            assert set(html.fromstring(render_column(column)).classes) == ({extra} if extra else set())
    assert vars(column) == original
