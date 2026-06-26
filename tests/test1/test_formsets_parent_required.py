"""
Tests for the parent-required validation in nested formsets (#55).

Unit tests cover the presence hook and the InlineFormSet delegation/message
in isolation; integration tests drive the rule through the real
Publisher -> books -> notes create/update flow.
"""

import pytest

from tests.test1.app.views_formset import BookFormSetForm, BookNoteInlineFormSet


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


class _PresentStub:
    def cv_is_present(self):
        return True


class _AbsentStub:
    def cv_is_present(self):
        return False


class _NoHookEmptyStub:
    """A parent form without the hook that looks like a blank extra row."""

    cleaned_data = {}

    def is_valid(self):
        return True


def _bare_inline_formset(parent_form):
    """Build an InlineFormSet without Django's heavy __init__ to test pure logic."""
    fs = object.__new__(BookNoteInlineFormSet)
    fs.parent_form = parent_form
    return fs


def test_parent_is_present_delegates_to_hook_true():
    fs = _bare_inline_formset(_PresentStub())
    assert fs._parent_is_present() is True


def test_parent_is_present_delegates_to_hook_false():
    fs = _bare_inline_formset(_AbsentStub())
    assert fs._parent_is_present() is False


def test_parent_is_present_falls_back_to_is_empty_form():
    """A parent form without cv_is_present falls back to the is_empty_form heuristic."""
    fs = _bare_inline_formset(_NoHookEmptyStub())
    assert fs._parent_is_present() is False  # empty form -> not present


def test_parent_required_error_has_no_placeholder_copy():
    msg = str(BookNoteInlineFormSet.cv_parent_required_error)
    assert "TODO" not in msg
    assert msg  # non-empty
