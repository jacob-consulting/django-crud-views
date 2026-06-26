"""
Tests for the order-independent formset validity gate.

A child formset's clean() may add_error() to a PARENT form. The gate must reject the
submission even when the parent form's validity was already collected earlier in the
traversal. This is verified WITHOUT a raise (the live InlineFormSet.clean() also raises,
which would otherwise mask the gate behavior).
"""

import pytest
from django.forms.models import BaseInlineFormSet
from django.test.client import Client

from tests.lib.helper.forms import field_key, form_payload
from tests.test1.app.models import BookNote, Publisher
from tests.test1.app.views_formset import BookNoteInlineFormSet


@pytest.mark.django_db
def test_cross_form_add_error_without_raise_rejects_submission(
    monkeypatch, client_user_publisher_formset: Client, cv_publisher_formset
):
    """A child clean() that add_error()s its parent WITHOUT raising must still reject."""

    def add_error_only(self):
        # Django's base formset clean populates cleaned_data; then annotate the parent
        # WITHOUT raising — exactly the cross-form pattern the hardened gate must catch.
        BaseInlineFormSet.clean(self)
        if self.parent_form and self.has_any_form_with_data and not self._parent_is_present():
            self.parent_form.add_error(None, "boom: parent missing")

    monkeypatch.setattr(BookNoteInlineFormSet, "clean", add_error_only)

    response = client_user_publisher_formset.get("/publisher-formset/create/")
    payload = form_payload(response)
    payload["name"] = "Ace Books"
    # fill the nested note, leave the parent book row blank -> orphan
    payload[field_key(payload, "-note")] = "orphan"

    response = client_user_publisher_formset.post("/publisher-formset/create/", payload)

    assert response.status_code == 200  # rejected, re-rendered (not 302, not a crash)
    assert b"boom: parent missing" in response.content
    assert not Publisher.objects.filter(name="Ace Books").exists()
    assert not BookNote.objects.exists()
