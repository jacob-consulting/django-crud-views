"""Execute the exact public compact recipe through authorized rendering and saving."""

import re
from pathlib import Path

import pytest
from django import forms
from lxml import html

from crud_views.lib.formsets import CompactColumn, CompactLayout, InlineFormSet
from tests.lib.helper.forms import form_payload
from tests.test1.app.models import Book, BookNote, Publisher
from tests.test1.app.views_formset import PublisherFormSetUpdateView

ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "docs/reference/formsets.md"


@pytest.mark.django_db
def test_published_compact_recipe_renders_and_saves_nested_rows(monkeypatch, client_user_publisher_formset):
    text = REFERENCE.read_text()
    heading = "### Standalone compact recipe\n"
    assert text.count(heading) == 1
    section = text.split(heading, 1)[1].split("\n### ", 1)[0]
    fences = re.findall(r"^```python\n(.*?)^```", section, re.M | re.S)
    assert len(fences) == 1
    assert "cv-sync:" not in section
    namespace = {"__name__": "tests.test1.app.compact_recipe", "__package__": "tests.test1.app"}
    exec(compile(fences[0], str(REFERENCE), "exec"), namespace)
    assert namespace["CompactColumn"] is CompactColumn
    assert namespace["CompactLayout"] is CompactLayout
    assert namespace["InlineRowForm"].__bases__ == (forms.ModelForm,)
    declarations = namespace["cv_formsets"]
    for declaration in (declarations["books"], declarations["books"].children["notes"]):
        assert declaration.klass.__bases__ == (InlineFormSet,)
        assert declaration.compact_layout is not None
        assert declaration.form_show_labels is False  # compact still emits accessible labels

    def forbidden(*args, **kwargs):
        pytest.fail("The copied compact recipe must not consult a classic layout")

    monkeypatch.setattr(InlineFormSet, "get_helper_layout_fields", forbidden)
    monkeypatch.setattr(PublisherFormSetUpdateView, "cv_formsets", declarations)
    publisher = Publisher.objects.create(name="Recipe publisher")
    book = Book.objects.create(publisher=publisher, title="Original book")
    note = BookNote.objects.create(book=book, note="Original note")
    url = f"/publisher-formset/{publisher.pk}/update/"
    response = client_user_publisher_formset.get(url)
    assert response.status_code == 200
    document = html.fromstring(response.content)
    fieldsets = document.cssselect("fieldset.cv-formset-compact")
    assert len(fieldsets) == 3  # books, existing book's notes, extra book's notes
    assert len(document.cssselect(".cv-formset-compact-headings")) == 3
    assert "Book title" in fieldsets[0].cssselect(".cv-formset-compact-headings")[0].text_content()
    for field in document.cssselect(".cv-formset-compact-fields input"):
        labels = document.xpath(".//label[@for=$id]", id=field.get("id"))
        assert len(labels) == 1
        assert "cv-formset-compact-label" in labels[0].get("class")
    assert len(document.cssselect("form.cv-form")) == 1
    assert len(document.cssselect("input[name='csrfmiddlewaretoken']")) == 1
    payload = form_payload(response)
    for suffix, previous, replacement in (
        ("-title", "Original book", "Published recipe book"),
        ("-note", "Original note", "Published recipe note"),
    ):
        name = next(name for name, value in payload.items() if name.endswith(suffix) and value == previous)
        payload[name] = replacement
    result = client_user_publisher_formset.post(url, payload)
    assert result.status_code == 302
    book.refresh_from_db()
    note.refresh_from_db()
    assert book.title == "Published recipe book" and book.publisher_id == publisher.pk
    assert note.note == "Published recipe note" and note.book_id == book.pk
    assert Book.objects.filter(publisher=publisher).count() == 1
    assert BookNote.objects.filter(book=book).count() == 1
