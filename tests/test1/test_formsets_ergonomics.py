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


def test_explicit_fields_and_pk_field_override_derivation():
    """Explicit values are kept verbatim and never overwritten by derivation."""
    fs = FormSet(title="Books", klass=BookFormSet, fields=[], pk_field="custom")
    assert fs.fields == []
    assert fs.pk_field == "custom"
