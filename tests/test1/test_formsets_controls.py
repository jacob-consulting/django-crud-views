"""Capability and accessibility contracts of the shipped row control template."""

from html.parser import HTMLParser

import pytest
from django.template.loader import render_to_string
from pydantic import ValidationError

from crud_views.lib.formsets import FormSet, FormSets
from tests.test1.app.models import Publisher
from tests.test1.app.views_formset import BookFormSet


class Buttons(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.buttons = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        if tag == "button":
            self.buttons.append(dict(attrs))


@pytest.mark.parametrize("edit_only", [False, True])
@pytest.mark.parametrize("can_delete", [False, True])
@pytest.mark.parametrize("can_order", [False, True])
@pytest.mark.parametrize("can_delete_extra", [False, True])
def test_stock_controls_render_real_formset_capabilities(
    monkeypatch, edit_only, can_delete, can_order, can_delete_extra
):
    # Exercise the supported optional-ordered-model configuration. The template's
    # capability projection is independent of the startup model-ordering check.
    monkeypatch.setattr("crud_views.lib.ordered.get_ordered_model", lambda: None)
    klass = type(
        "ControlFormSet",
        (BookFormSet,),
        {
            "edit_only": edit_only,
            "can_delete": can_delete,
            "can_order": can_order,
            "can_delete_extra": can_delete_extra,
        },
    )
    declaration = FormSet(title="Books", klass=klass)
    runtime = klass(formset=declaration, instance=Publisher(), prefix="line-items-None-0")
    form = runtime.empty_form
    buttons = Buttons(
        render_to_string(
            "crud_views/formsets/control.html",
            {
                "formset": declaration,
                "form": form,
            },
        )
    ).buttons
    controls = {next(c for c in button["class"].split() if c.startswith("cv-form-ctrl-")): button for button in buttons}
    assert ("cv-form-ctrl-add" in controls) is (not edit_only)
    assert ("cv-form-ctrl-delete" in controls) is (can_delete and can_delete_extra)
    assert ("cv-form-ctrl-up" in controls) is can_order
    assert ("cv-form-ctrl-down" in controls) is can_order
    for button in buttons:
        assert button["type"] == "button"
        assert button["cv-data-formset-form-prefix"] == form.prefix
        assert button["aria-label"] == button["title"]
        assert button["aria-label"]
    if not edit_only:
        assert controls["cv-form-ctrl-add"]["aria-label"] == "Add row"
    if can_delete and can_delete_extra:
        assert controls["cv-form-ctrl-delete"]["data-cv-class"]
        assert controls["cv-form-ctrl-delete"]["data-cv-class-danger"]


def test_formset_declaration_keys_keep_existing_grammar():
    declaration = FormSet(title="Books", klass=BookFormSet)
    assert FormSets(formsets={"line-items": declaration}).formsets["line-items"].key == "line-items"
    with pytest.raises(ValidationError, match="Formset key must contain"):
        FormSets(formsets={"line.items:detail": declaration})
