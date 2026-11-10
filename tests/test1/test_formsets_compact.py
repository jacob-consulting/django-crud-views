"""Compact presentation uses the existing authorized formset lifecycle."""

import pytest
from lxml import html

from tests.lib.helper.forms import form_payload
from tests.test1.app.models import Book, Publisher
from tests.test1.app.views_formset import BookInlineFormSet, publisher_formsets


@pytest.fixture
def compact_books(monkeypatch):
    from crud_views.lib.formsets.compact import CompactColumn, CompactLayout

    layout = CompactLayout([CompactColumn("title", span=8)], controls_span=4)
    monkeypatch.setattr(publisher_formsets["books"], "compact_layout", layout)

    def forbidden(*args, **kwargs):
        pytest.fail("Compact rendering must not call the classic layout")

    monkeypatch.setattr(BookInlineFormSet, "get_helper_layout_fields", forbidden)
    return layout


@pytest.mark.django_db
def test_compact_tracer_get_post(compact_books, client_user_publisher_formset):
    publisher = Publisher.objects.create(name="Compact publisher")
    book = Book.objects.create(publisher=publisher, title="Original")
    url = f"/publisher-formset/{publisher.pk}/update/"
    response = client_user_publisher_formset.get(url)
    assert response.status_code == 200
    document = html.fromstring(response.content)
    fieldset = document.cssselect("fieldset.cv-formset-compact")[0]
    headings = fieldset.cssselect(".cv-formset-compact-headings")
    assert len(headings) == 1
    assert "Title" in headings[0].text_content()
    assert not headings[0].xpath("ancestor::div[contains(@class, 'cv-formset-row')]")
    for row in fieldset.cssselect(".cv-formset-row-compact"):
        own_form = row.find("div")
        title = own_form.cssselect("input[name$='-title']")[0]
        labels = own_form.xpath(".//label[@for=$id]", id=title.get("id"))
        assert len(labels) == 1
        assert "cv-formset-compact-label" in labels[0].get("class")
        assert row.cssselect(".cv-form-ctrl-add, .cv-form-ctrl-delete")
        for suffix in ("-id", "-publisher", "-DELETE"):
            inputs = own_form.cssselect(f"input[name$='{suffix}']")
            assert len(inputs) == 1
            assert inputs[0].get("type") == "hidden"
    assert len(document.cssselect("form.cv-form")) == 1
    assert len(document.cssselect("input[name='csrfmiddlewaretoken']")) == 1
    payload = form_payload(response)
    assert any(name.endswith("-TOTAL_FORMS") for name in payload)
    title_name = next(name for name, value in payload.items() if name.endswith("-title") and value == "Original")
    payload[title_name] = "Saved compact book"
    result = client_user_publisher_formset.post(url, payload)
    assert result.status_code == 302
    book.refresh_from_db()
    assert book.title == "Saved compact book"
