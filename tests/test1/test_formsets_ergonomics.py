"""
Tests for formsets ergonomics (issue #29):
- FormSet.fields / pk_field are derived from the formset klass when omitted.
- FormSet.form_show_labels is configurable (Task 2).
"""

import pytest

from crud_views.lib.formsets import FormSet
from tests.test1.app.models import Publisher
from tests.test1.app.views_formset import BookFormSet


def test_fields_and_pk_field_derived_from_klass():
    """Omitting fields/pk_field derives them from the inline formset klass."""
    fs = FormSet(title="Books", klass=BookFormSet)
    assert fs.fields == ["title"]
    assert fs.pk_field == "id"
    # derived fields exclude the parent FK and the auto pk / management fields
    assert "publisher" not in fs.fields
    assert "id" not in fs.fields
    assert "ORDER" not in fs.fields
    assert "DELETE" not in fs.fields


def test_explicit_fields_and_pk_field_override_derivation():
    """Explicit values are kept verbatim and never overwritten by derivation."""
    fs = FormSet(title="Books", klass=BookFormSet, fields=[], pk_field="custom")
    assert fs.fields == []
    assert fs.pk_field == "custom"


@pytest.mark.django_db
def test_form_show_labels_defaults_false():
    """Default form_show_labels is False, preserving current inline-row behavior."""
    publisher = Publisher.objects.create(name="P")
    fs = FormSet(title="Books", klass=BookFormSet)
    instance = BookFormSet(formset=fs, instance=publisher)
    assert instance.get_helper().form_show_labels is False


@pytest.mark.django_db
def test_form_show_labels_configurable():
    """form_show_labels=True on the FormSet flows through to the crispy helper."""
    publisher = Publisher.objects.create(name="P")
    fs = FormSet(title="Books", klass=BookFormSet, form_show_labels=True)
    instance = BookFormSet(formset=fs, instance=publisher)
    assert instance.get_helper().form_show_labels is True
