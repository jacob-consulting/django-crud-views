"""
Characterization tests for the nested formsets subsystem
(Publisher → books → notes, see tests/test1/app/views_formset.py).
"""

import pytest
from django.test.client import Client

from tests.lib.helper.forms import field_key, field_keys, form_payload
from tests.test1.app.models import Book, BookNote, Publisher


@pytest.mark.django_db
def test_create_with_nested_formsets(client_user_publisher_formset: Client, cv_publisher_formset):
    response = client_user_publisher_formset.get("/publisher-formset/create/")
    assert response.status_code == 200

    payload = form_payload(response)
    payload["name"] = "Ace Books"
    payload[field_key(payload, "-title")] = "Dune"
    payload[field_key(payload, "-note")] = "classic"

    response = client_user_publisher_formset.post("/publisher-formset/create/", payload)
    assert response.status_code == 302, getattr(response, "context", None) and str(response.context.get("form").errors)

    publisher = Publisher.objects.get(name="Ace Books")
    book = Book.objects.get(publisher=publisher, title="Dune")
    assert BookNote.objects.filter(book=book, note="classic").exists()


@pytest.mark.django_db
def test_create_without_formset_rows(client_user_publisher_formset: Client, cv_publisher_formset):
    response = client_user_publisher_formset.get("/publisher-formset/create/")
    payload = form_payload(response)
    payload["name"] = "Empty House"

    response = client_user_publisher_formset.post("/publisher-formset/create/", payload)
    assert response.status_code == 302

    publisher = Publisher.objects.get(name="Empty House")
    assert publisher.books.count() == 0


@pytest.mark.django_db
def test_update_changes_nested_rows(client_user_publisher_formset: Client, cv_publisher_formset):
    publisher = Publisher.objects.create(name="Tor")
    book = Book.objects.create(publisher=publisher, title="Mistborn")
    note = BookNote.objects.create(book=book, note="fantasy")

    response = client_user_publisher_formset.get(f"/publisher-formset/{publisher.pk}/update/")
    assert response.status_code == 200

    payload = form_payload(response)

    # change the existing book title and note text (existing rows carry the current values)
    title_key = next(k for k in field_keys(payload, "-title") if payload[k] == "Mistborn")
    note_key = next(k for k in field_keys(payload, "-note") if payload[k] == "fantasy")
    payload[title_key] = "Elantris"
    payload[note_key] = "standalone"

    response = client_user_publisher_formset.post(f"/publisher-formset/{publisher.pk}/update/", payload)
    assert response.status_code == 302

    book.refresh_from_db()
    note.refresh_from_db()
    assert book.title == "Elantris"
    assert note.note == "standalone"


@pytest.mark.django_db
def test_update_adds_book_via_extra_row(client_user_publisher_formset: Client, cv_publisher_formset):
    publisher = Publisher.objects.create(name="Orbit")
    Book.objects.create(publisher=publisher, title="Leviathan")

    response = client_user_publisher_formset.get(f"/publisher-formset/{publisher.pk}/update/")
    payload = form_payload(response)

    # fill the blank extra row
    blank_title_key = next(k for k in field_keys(payload, "-title") if payload[k] == "")
    payload[blank_title_key] = "Ancillary"

    response = client_user_publisher_formset.post(f"/publisher-formset/{publisher.pk}/update/", payload)
    assert response.status_code == 302

    assert set(publisher.books.values_list("title", flat=True)) == {"Leviathan", "Ancillary"}


@pytest.mark.django_db
def test_update_deletes_book_row_and_nested_notes(client_user_publisher_formset: Client, cv_publisher_formset):
    publisher = Publisher.objects.create(name="Baen")
    book = Book.objects.create(publisher=publisher, title="Honor")
    BookNote.objects.create(book=book, note="space opera")

    response = client_user_publisher_formset.get(f"/publisher-formset/{publisher.pk}/update/")
    payload = form_payload(response)

    # check the DELETE box of the existing book row
    title_key = next(k for k in field_keys(payload, "-title") if payload[k] == "Honor")
    delete_key = title_key[: -len("title")] + "DELETE"
    payload[delete_key] = "on"

    response = client_user_publisher_formset.post(f"/publisher-formset/{publisher.pk}/update/", payload)
    assert response.status_code == 302

    assert not Book.objects.filter(pk=book.pk).exists()
    assert not BookNote.objects.filter(book_id=book.pk).exists()


@pytest.mark.django_db
def test_update_invalid_nested_row_rerenders_with_errors(client_user_publisher_formset: Client, cv_publisher_formset):
    publisher = Publisher.objects.create(name="Gollancz")
    book = Book.objects.create(publisher=publisher, title="Hyperion")

    response = client_user_publisher_formset.get(f"/publisher-formset/{publisher.pk}/update/")
    payload = form_payload(response)

    # blank out the required title of the existing row
    title_key = next(k for k in field_keys(payload, "-title") if payload[k] == "Hyperion")
    payload[title_key] = ""

    response = client_user_publisher_formset.post(f"/publisher-formset/{publisher.pk}/update/", payload)
    assert response.status_code == 200  # re-rendered, not redirected

    book.refresh_from_db()
    assert book.title == "Hyperion"  # unchanged


@pytest.mark.django_db
def test_ajax_formset_template_endpoint(client_user_publisher_formset: Client, cv_publisher_formset):
    response = client_user_publisher_formset.get(
        "/publisher-formset/create/",
        {"template": "books", "num": "0", "pk": "None"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "rows" in data
    assert "html" in data
    assert data["rows"]
