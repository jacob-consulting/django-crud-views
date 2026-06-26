"""
Tests for the parent-required validation in nested formsets (#55).

Unit tests cover the presence hook and the InlineFormSet delegation/message
in isolation; integration tests drive the rule through the real
Publisher -> books -> notes create/update flow.
"""

import pytest

from tests.test1.app.views_formset import BookFormSetForm


@pytest.mark.django_db
def test_cv_is_present_default_false_for_blank_form():
    """An unbound/blank form is not a present parent."""
    form = BookFormSetForm(cv_view=None)
    assert form.cv_is_present() is False


@pytest.mark.django_db
def test_cv_is_present_default_true_for_filled_form():
    """A bound form carrying data is a present parent."""
    form = BookFormSetForm(cv_view=None, data={"title": "Dune"})
    assert form.cv_is_present() is True
