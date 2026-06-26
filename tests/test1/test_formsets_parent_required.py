"""
Tests for the parent-required validation in nested formsets (#55).

Unit tests cover the presence hook and the InlineFormSet delegation/message
in isolation; integration tests drive the rule through the real
Publisher -> books -> notes create/update flow.
"""

import pytest
from django.test.client import Client

from tests.lib.helper.forms import field_key, form_payload
from tests.test1.app.models import Book, BookNote, Publisher
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


@pytest.mark.django_db
def test_orphan_note_on_blank_book_is_rejected(client_user_publisher_formset: Client, cv_publisher_formset):
    """A note (grandchild) with data under a blank book row must be rejected."""
    response = client_user_publisher_formset.get("/publisher-formset/create/")
    payload = form_payload(response)
    payload["name"] = "Ace Books"
    # fill the nested note but leave the parent book row blank -> orphan
    payload[field_key(payload, "-note")] = "orphan note"

    response = client_user_publisher_formset.post("/publisher-formset/create/", payload)

    assert response.status_code == 200  # re-rendered, not redirected
    assert b"Cannot add entries here" in response.content
    assert not Publisher.objects.filter(name="Ace Books").exists()
    assert not BookNote.objects.exists()


@pytest.mark.django_db
def test_filled_book_with_note_saves(client_user_publisher_formset: Client, cv_publisher_formset):
    """A present parent book with a child note saves cleanly."""
    response = client_user_publisher_formset.get("/publisher-formset/create/")
    payload = form_payload(response)
    payload["name"] = "Tor"
    payload[field_key(payload, "-title")] = "Mistborn"
    payload[field_key(payload, "-note")] = "fantasy"

    response = client_user_publisher_formset.post("/publisher-formset/create/", payload)

    assert response.status_code == 302
    book = Book.objects.get(title="Mistborn")
    assert BookNote.objects.filter(book=book, note="fantasy").exists()


@pytest.mark.django_db
def test_all_blank_rows_no_false_positive(client_user_publisher_formset: Client, cv_publisher_formset):
    """Blank parent row with no grandchild data must not trigger the rule."""
    response = client_user_publisher_formset.get("/publisher-formset/create/")
    payload = form_payload(response)
    payload["name"] = "Empty House"
    # leave both the book row and the note row blank

    response = client_user_publisher_formset.post("/publisher-formset/create/", payload)

    assert response.status_code == 302
    publisher = Publisher.objects.get(name="Empty House")
    assert publisher.books.count() == 0
