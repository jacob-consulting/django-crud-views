"""
Characterization tests for the nested formsets subsystem
(Publisher → books → notes, see tests/test1/app/views_formset.py).
"""

import pytest
from django.test.client import Client

from tests.lib.helper.forms import field_key, field_keys, form_payload
from tests.test1.app.models import Book, BookNote, Publisher
from tests.test1.test_theme_form_ownership import assert_owned_form_markup


@pytest.mark.django_db
def test_formset_create_page_has_no_nested_form(client_user_publisher_formset: Client, cv_publisher_formset):
    """A formset parent form must not emit its own <form> tag.

    The CRUD create/update template already wraps the fields in
    ``<form class="cv-form">``. If the form's crispy helper leaves
    ``form_tag=True`` (the crispy default), a second <form> is nested inside
    cv-form; the browser then closes cv-form early and ``formset.js`` — which
    binds add/reorder handlers to ``form.cv-form`` — can no longer manage the
    formset (rows can't be added). Guard against that regression here.
    """
    response = client_user_publisher_formset.get("/publisher-formset/create/")
    assert response.status_code == 200
    assert_owned_form_markup(response.content.decode())


def test_parent_inherited_helper_exposes_static_w292(monkeypatch):
    from django.test import override_settings

    from tests.test1.app.views_formset import PublisherFormSetCreateView, PublisherFormSetForm
    from tests.test1.test_form_button_checks import _w292

    def forbidden(*args, **kwargs):
        pytest.fail("Static parent checks must not construct forms")

    monkeypatch.setattr(PublisherFormSetForm, "__init__", forbidden)
    monkeypatch.setattr(PublisherFormSetForm, "submit_icon", None)
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"form": "icon"}):
        assert _w292(PublisherFormSetCreateView) == [("submit", "PublisherFormSetForm")]


@pytest.mark.django_db
@pytest.mark.parametrize("operation", ["create", "update"])
def test_parent_formset_owned_csrf_and_nested_payload(operation, user_publisher_formset):
    from lxml import html

    from crud_views.lib.crispy.form import CrispyFormMixin
    from tests.test1.app.views_formset import PublisherFormSetForm

    assert PublisherFormSetForm.helper is CrispyFormMixin.helper
    client = Client(enforce_csrf_checks=True)
    client.force_login(user_publisher_formset)
    publisher = Publisher.objects.create(name="Existing")
    if operation == "update":
        book = Book.objects.create(publisher=publisher, title="Original")
        BookNote.objects.create(book=book, note="Original note")
    url = "/publisher-formset/create/" if operation == "create" else f"/publisher-formset/{publisher.pk}/update/"
    response = client.get(url)
    assert response.status_code == 200
    owner = assert_owned_form_markup(response.content.decode())
    assert response.context["form"].helper.form_tag is False
    document = html.fromstring(response.content)
    form = document.cssselect("form.cv-form")[0]
    management = form.cssselect("input[name$='-TOTAL_FORMS'], input[name$='-INITIAL_FORMS']")
    assert management
    for control in document.cssselect("input, select, textarea, button[type=submit]"):
        assert next(control.iterancestors("form"), None) is form
    payload = form_payload(response)
    payload["name"] = "Saved parent"
    title_key = next(
        k for k in field_keys(payload, "-title") if payload[k] == ("Original" if operation == "update" else "")
    )
    note_key = next(
        k for k in field_keys(payload, "-note") if payload[k] == ("Original note" if operation == "update" else "")
    )
    payload[title_key] = "Saved child"
    payload[note_key] = "Saved grandchild"
    submitter = owner["submitters"][0]
    payload[submitter["name"]] = submitter["value"]
    before = (list(Publisher.objects.values()), list(Book.objects.values()), list(BookNote.objects.values()))

    def unchanged():
        assert (
            list(Publisher.objects.values()),
            list(Book.objects.values()),
            list(BookNote.objects.values()),
        ) == before

    for token in (None, "invalid"):
        rejected = dict(payload)
        rejected.pop("csrfmiddlewaretoken")
        if token is not None:
            rejected["csrfmiddlewaretoken"] = token
        assert client.post(url, rejected).status_code == 403
        unchanged()
    invalid = client.post(url, {**payload, "name": ""})
    assert invalid.status_code == 200
    assert invalid.context["form"].errors
    assert_owned_form_markup(invalid.content.decode())
    invalid_payload = form_payload(invalid)
    for control in management:
        assert invalid_payload[control.get("name")] == payload[control.get("name")]
    unchanged()
    result = client.post(url, payload)
    assert result.status_code == 302
    saved = Publisher.objects.get(name="Saved parent")
    if operation == "update":
        assert saved.pk == publisher.pk
    child = Book.objects.get(publisher=saved, title="Saved child")
    assert BookNote.objects.filter(book=child, note="Saved grandchild").count() == 1
    assert result.wsgi_request.POST[submitter["name"]] == submitter["value"]
    destination = client.get(result["Location"])
    assert destination.status_code == 200
    assert b"Saved parent" in destination.content


def test_example_parent_inherits_library_helper():
    """The example's import graph belongs to its own Django project; inspect only the named class here."""
    import ast
    from pathlib import Path

    tree = ast.parse((Path(__file__).resolve().parents[2] / "examples/bootstrap5/formsets/views.py").read_text())
    parent = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "QuestionnaireForm")
    assert any(isinstance(base, ast.Name) and base.id == "CrispyModelForm" for base in parent.bases)
    assert not any(isinstance(node, ast.FunctionDef) and node.name == "helper" for node in parent.body)


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
