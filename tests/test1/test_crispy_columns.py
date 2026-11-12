"""Numbered columns resolve theme classes without taking ownership of custom templates."""

from copy import deepcopy

import pytest
from django import forms
from django.template import Context
from lxml import html

from crud_views.lib import button_classes as bc
from crud_views.lib.crispy import Column6


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
