"""XFormSet.save() with an orderable formset writes ORDER onto the saved instance."""

import pytest
from django.forms.models import inlineformset_factory
from django.test.client import RequestFactory

from tests.test1.app.models import Book, Publisher
from tests.test1.app.views_formset import (
    BookFormSetForm,
    BookInlineFormSet,
    PublisherFormSetForm,
    publisher_formsets,
)

_OrderedBookFormSet = inlineformset_factory(
    Publisher,
    Book,
    formset=BookInlineFormSet,
    form=BookFormSetForm,
    fields=["title"],
    extra=1,
    can_delete=True,
    can_order=True,
)


def _post(publisher, rows):
    prefix = f"books-{publisher.pk}-0"
    data = {
        f"{prefix}-TOTAL_FORMS": str(len(rows)),
        f"{prefix}-INITIAL_FORMS": "0",
        f"{prefix}-MIN_NUM_FORMS": "0",
        f"{prefix}-MAX_NUM_FORMS": "1000",
    }
    for i, (title, order) in enumerate(rows):
        data[f"{prefix}-{i}-title"] = title
        data[f"{prefix}-{i}-ORDER"] = order
        nested = f"books-notes-{publisher.pk}-0-{i}-None-0"
        data.update(
            {
                f"{nested}-TOTAL_FORMS": "0",
                f"{nested}-INITIAL_FORMS": "0",
                f"{nested}-MIN_NUM_FORMS": "0",
                f"{nested}-MAX_NUM_FORMS": "1000",
            }
        )
    return RequestFactory().post("/x", data)


def _ordered_x_formset(publisher, rows):
    formsets = publisher_formsets.model_copy(deep=True)
    books = formsets["books"]
    books.klass = _OrderedBookFormSet
    main_form = PublisherFormSetForm(cv_view=None, instance=publisher)
    x_formset = next(books.init(request=_post(publisher, rows), forms=[main_form]))
    assert x_formset.instance.is_valid(), x_formset.instance.errors
    return x_formset


@pytest.mark.django_db
def test_ordered_save_sets_order_from_order_field():
    publisher = Publisher.objects.create(name="P")
    x_formset = _ordered_x_formset(publisher, [("First", "2"), ("Second", "1")])

    x_formset.save()

    by_title = {f.instance.title: f.instance for f in x_formset.instance.forms}
    assert by_title["First"].order == 2
    assert by_title["Second"].order == 1
    assert set(Book.objects.filter(publisher=publisher).values_list("title", flat=True)) == {"First", "Second"}


@pytest.mark.django_db
def test_ordered_save_leaves_order_unset_when_order_is_empty():
    publisher = Publisher.objects.create(name="P")
    x_formset = _ordered_x_formset(publisher, [("NoOrder", "")])

    x_formset.save()

    (form,) = x_formset.instance.forms
    assert not hasattr(form.instance, "order")
    assert Book.objects.filter(publisher=publisher, title="NoOrder").exists()
