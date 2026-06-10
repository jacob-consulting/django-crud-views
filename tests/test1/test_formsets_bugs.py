"""
Regression tests for formsets subsystem bugs found in the 2026-06-10 audit:

- H1: XFormSet.save() must raise when a form has no matching XForm
      (was: `assert Exception(...)` which never raises)
- M1: FormSet.init() inner loop must not corrupt the `index` parameter
- M2: PolymorphicFormSetMixin.cv_get_formsets() returns None for models
      without formsets (was: contradictory ValueError)
- M3: the formset AJAX template endpoint rejects garbage input with 400
"""

from collections import OrderedDict

import pytest
from django.test.client import Client, RequestFactory

from crud_views.lib.exceptions import CrudViewError
from crud_views.lib.formsets import FormSet, FormSets
from tests.test1.app.models import Book, Publisher
from tests.test1.app.views_formset import (
    BookFormSet,
    BookNoteFormSet,
    PublisherFormSetForm,
    publisher_formsets,
)


@pytest.mark.django_db
def test_xformset_save_raises_on_missing_xform():
    """H1: a form without a matching XForm must raise, not silently pass."""
    publisher = Publisher.objects.create(name="P")
    prefix = f"books-{publisher.pk}-0"
    nested_prefix = f"books-notes-{publisher.pk}-0-0-None-0"

    data = {
        f"{prefix}-TOTAL_FORMS": "1",
        f"{prefix}-INITIAL_FORMS": "0",
        f"{prefix}-MIN_NUM_FORMS": "0",
        f"{prefix}-MAX_NUM_FORMS": "1000",
        f"{prefix}-0-title": "T",
        f"{nested_prefix}-TOTAL_FORMS": "0",
        f"{nested_prefix}-INITIAL_FORMS": "0",
        f"{nested_prefix}-MIN_NUM_FORMS": "0",
        f"{nested_prefix}-MAX_NUM_FORMS": "1000",
    }
    request = RequestFactory().post("/x", data)

    formsets = publisher_formsets.model_copy(deep=True)
    books = formsets["books"]
    main_form = PublisherFormSetForm(cv_view=None, instance=publisher)

    x_formset = next(books.init(request=request, forms=[main_form]))
    assert x_formset.instance.is_valid()

    # force a form/x-form mismatch
    x_formset.forms.clear()

    with pytest.raises(CrudViewError):
        x_formset.save()


@pytest.mark.django_db
def test_init_index_parameter_not_corrupted_by_child_loop():
    """M1: with 2+ children, the inner enumerate must not overwrite the index param."""
    formsets = FormSets(
        formsets=OrderedDict(
            books=FormSet(
                title="Books",
                klass=BookFormSet,
                fields=["title"],
                pk_field="id",
                children=OrderedDict(
                    notes=FormSet(title="Notes", klass=BookNoteFormSet, fields=["note"], pk_field="id"),
                    memos=FormSet(title="Memos", klass=BookNoteFormSet, fields=["note"], pk_field="id"),
                ),
            ),
        )
    )
    books = formsets["books"]

    p1 = Publisher.objects.create(name="P1")
    p2 = Publisher.objects.create(name="P2")
    request = RequestFactory().get("/x")

    x_formsets = list(
        books.init(
            request=request,
            forms=[PublisherFormSetForm(cv_view=None, instance=p1), PublisherFormSetForm(cv_view=None, instance=p2)],
        )
    )

    assert [x.prefix_key for x in x_formsets] == [f"{p1.pk}-0", f"{p2.pk}-0"]


def test_polymorphic_formsets_missing_model_returns_none():
    """M2: a polymorphic model without formsets is okay and yields None."""
    from crud_views.lib.formsets.mixins import PolymorphicFormSetMixin

    class FakeView(PolymorphicFormSetMixin):
        cv_polymorphic_formsets = {}
        polymorphic_model = Book

    assert FakeView().cv_get_formsets() is None


@pytest.mark.django_db
def test_ajax_template_endpoint_rejects_unknown_key(user_publisher_formset):
    """M3: unknown formset key must produce 400, not 500."""
    client = Client(raise_request_exception=False)
    client.force_login(user_publisher_formset)

    response = client.get(
        "/publisher-formset/create/",
        {"template": "doesnotexist", "num": "0", "pk": "None"},
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_ajax_template_endpoint_rejects_unknown_nested_key(user_publisher_formset):
    client = Client(raise_request_exception=False)
    client.force_login(user_publisher_formset)

    response = client.get(
        "/publisher-formset/create/",
        {"template": "books|doesnotexist", "num": "0", "pk": "None"},
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_ajax_template_endpoint_rejects_non_integer_num(user_publisher_formset):
    client = Client(raise_request_exception=False)
    client.force_login(user_publisher_formset)

    response = client.get(
        "/publisher-formset/create/",
        {"template": "books", "num": "evil", "pk": "None"},
    )
    assert response.status_code == 400
