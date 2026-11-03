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

from crud_views.lib.formsets import FormSets
from tests.lib.helper.forms import field_key, form_payload
from tests.test1.app.models import BookNote, Publisher
from tests.test1.app.views_formset import BookNoteInlineFormSet
from tests.test1.test_formsets_policy import editor, observe_saves
from tests.test1.test_formsets_policy import policy_routes as policy_routes
from tests.test1.test_formsets_policy import policy_world as policy_world


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


@pytest.mark.django_db
def test_child_clean_main_form_error_rejects_before_save(monkeypatch, client_user_publisher_formset):
    """The top-level main form participates in the second validity pass too."""
    main = {}
    original_init = FormSets.init

    def init(self, request, form):
        main["form"] = form
        return original_init(self, request, form)

    def clean(self):
        BaseInlineFormSet.clean(self)
        main["form"].add_error(None, "main error from child clean")

    monkeypatch.setattr(FormSets, "init", init)
    monkeypatch.setattr(BookNoteInlineFormSet, "clean", clean)
    saves = []
    original_save = Publisher.save

    def save(self, *args, **kwargs):
        saves.append(self.pk)
        return original_save(self, *args, **kwargs)

    monkeypatch.setattr(Publisher, "save", save)
    client_user_publisher_formset.raise_request_exception = False
    page = client_user_publisher_formset.get("/publisher-formset/create/")
    payload = form_payload(page)
    payload["name"] = "must not save main"
    response = client_user_publisher_formset.post("/publisher-formset/create/", payload)
    assert response.status_code == 200
    assert b"main error from child clean" in response.content
    assert saves == []
    assert not Publisher.objects.filter(name="must not save main").exists()


@pytest.mark.django_db
@pytest.mark.parametrize("cleaner", ["siblings", "notes"])
@pytest.mark.parametrize("violation", ["addition", "identity"])
def test_late_clean_reclean_restores_row_policy_before_http_save(
    policy_routes, policy_world, monkeypatch, cleaner, violation
):
    """Later custom clean erases an earlier error; phase two must restore it."""
    trees = []
    recleans = []
    original_init = FormSets.init
    original_clean = policy_routes.family.clean

    def init(self, request, form):
        result = original_init(self, request, form)
        if request.method == "POST":
            trees.append(self)
        return result

    def clean(self):
        original_clean(self)
        if self.formset.original_key == cleaner:
            earlier = trees[-1].x_formsets[0].instance
            recleans.append([e.code for e in earlier.non_form_errors().as_data()])
            earlier.full_clean()

    monkeypatch.setattr(FormSets, "init", init)
    monkeypatch.setattr(policy_routes.family, "clean", clean)
    url, payload = editor(policy_routes, policy_world)
    payload["name"] = "Positive late clean control"
    assert policy_routes.client.post(url, payload).status_code == 302
    recleans.clear()
    _, payload = editor(policy_routes, policy_world)
    payload["name"] = "Must not save"
    prefix = f"books-{policy_world.parent.pk}-0"
    payload[f"{prefix}-0-title"] = "must not edit"
    payload[f"siblings-{policy_world.parent.pk}-0-0-title"] = "sibling must not edit"
    payload[f"books-notes-{policy_world.parent.pk}-0-0-{policy_world.book.pk}-0-0-note"] = "must not edit"
    if violation == "addition":
        payload[f"{prefix}-1-title"] = "forged"
        code, message = "cv_additions_not_allowed", "Additions are not allowed."
    else:
        payload[f"{prefix}-0-id"] = "bad-pk"
        payload[f"{prefix}-0-DELETE"] = "on"
        code, message = "cv_invalid_row", "Invalid row."
    saves = observe_saves(monkeypatch)
    response = policy_routes.client.post(url, payload)
    assert response.status_code == 200
    assert any(code in codes for codes in recleans)
    tree = response.context["formsets"]
    assert tree.all_valid() is False
    errors = tree.x_formsets[0].instance.non_form_errors().as_data()
    assert [(e.code, e.messages) for e in errors] == [(code, [message])]
    assert message.encode() in response.content
    assert saves == []
    policy_world.parent.refresh_from_db()
    policy_world.book.refresh_from_db()
    policy_world.sibling.refresh_from_db()
    policy_world.note.refresh_from_db()
    assert policy_world.parent.name == "Positive late clean control"
    assert policy_world.book.title == "book"
    assert policy_world.sibling.title == "sibling original"
    assert policy_world.note.note == "original note"
