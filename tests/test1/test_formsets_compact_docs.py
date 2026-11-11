"""Execute the exact public compact recipe through authorized rendering and saving."""

import re
from pathlib import Path

import pytest
from django import forms
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.test import RequestFactory
from lxml import html

from crud_views.lib.formsets import CompactColumn, CompactLayout, FormSets, InlineFormSet
from tests.lib.helper.forms import form_payload
from tests.test1.app.models import Book, BookNote, ConditionalPersistenceRecord, Profile, Publisher
from tests.test1.app.views_formset import PublisherFormSetUpdateView

ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "docs/reference/formsets.md"


@pytest.mark.django_db
def test_published_compact_checkbox_recipe():
    text = REFERENCE.read_text()
    heading = "### Stock checkbox recipe\n"
    assert text.count(heading) == 1
    section = re.split(r"\n#{2,3} ", text.split(heading, 1)[1], maxsplit=1)[0]
    fences = re.findall(r"^```python\n(.*?)^```", section, re.M | re.S)
    assert len(fences) == 1
    namespace = {"__name__": "tests.test1.app.checkbox_recipe", "__package__": "tests.test1.app"}
    exec(compile(fences[0], str(REFERENCE), "exec"), namespace)
    assert "CompactWidgetCompatible" not in namespace
    assert namespace["CheckboxRecordForm"].__bases__ == (forms.ModelForm,)
    declaration = namespace["cv_formsets"]["records"]
    assert declaration.klass.__bases__ == (InlineFormSet,)
    parent = Profile.objects.create(name="Checkbox recipe")
    record = ConditionalPersistenceRecord.objects.create(parent=parent)

    def initialize(data=None):
        trees = FormSets(formsets=namespace["cv_formsets"])
        request = RequestFactory().get("/") if data is None else RequestFactory().post("/", data)
        trees.init(request, forms.modelform_factory(Profile, fields=[])(instance=parent))
        return trees, trees.x_formsets[0]

    for checked in (True, False):
        _, initial = initialize()
        retained, extra = [row.form for row in initial.forms]
        assert retained.cv_view is declaration.cv_view
        assert extra.cv_view is declaration.cv_view
        for form in (retained, extra):
            for name in ("active", "flag"):
                assert type(form.fields[name].widget) is forms.CheckboxInput
        markup = render_to_string("crud_views/formsets/formset.html", {"x_formset": initial})
        document = html.fromstring(markup)
        headings = document.cssselect(".cv-formset-compact-headings")
        assert len(headings) == 1
        assert "Active" in headings[0].text_content() and "Flag" in headings[0].text_content()
        controls = document.cssselect('.cv-formset-compact-fields input[type="checkbox"]')
        assert len(controls) == 4
        for control in controls:
            labels = document.xpath(".//label[@for=$id]", id=control.get("id"))
            assert len(labels) == 1
            assert labels[0].text_content().strip() in ("Active", "Flag")
        payload = form_payload(HttpResponse(f"<form>{markup}</form>"))
        for control in document.cssselect("input[disabled], select[disabled], textarea[disabled]"):
            payload.pop(control.get("name"), None)
        assert payload[extra.add_prefix("flag")] == "on"
        name = retained.add_prefix("active")
        payload.pop(name, None)
        if checked:
            payload[name] = "on"
        trees, bound = initialize(payload)
        assert all(row.form.cv_view is declaration.cv_view for row in bound.forms)
        assert not bound.forms[1].form.has_changed()
        assert trees.all_valid()
        trees.save()
        record.refresh_from_db()
        assert record.active is checked and record.flag is True
        assert ConditionalPersistenceRecord.objects.filter(parent=parent).count() == 1

    prefix = initial.instance.prefix
    trees, empty = initialize({f"{prefix}-TOTAL_FORMS": "0", f"{prefix}-INITIAL_FORMS": "0"})
    assert empty.forms == []
    assert [column.label for column in empty.compact_columns] == ["Active", "Flag"]
    assert empty.instance.empty_form.cv_view is declaration.cv_view
    assert "Active" in render_to_string("crud_views/formsets/formset.html", {"x_formset": empty})
    assert trees.all_valid()


@pytest.mark.django_db
def test_published_compact_recipe_renders_and_saves_nested_rows(monkeypatch, client_user_publisher_formset):
    text = REFERENCE.read_text()
    heading = "### Standalone compact recipe\n"
    assert text.count(heading) == 1
    section = re.split(r"\n#{2,3} ", text.split(heading, 1)[1], maxsplit=1)[0]
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


@pytest.mark.django_db
def test_published_compact_widget_recipe_preserves_option_attributes(monkeypatch, client_user_publisher_formset):
    from crud_views.lib.formsets import CompactWidgetCompatible
    from tests.test1.app.views_formset import BookFormSetForm, publisher_formsets

    text = REFERENCE.read_text()
    heading = "### Custom widget compatibility recipe\n"
    assert text.count(heading) == 1, "The dedicated custom-widget recipe must exist exactly once"
    section = re.split(r"\n#{2,3} ", text.split(heading, 1)[1], maxsplit=1)[0]
    fences = re.findall(r"^```python\n(.*?)^```", section, re.M | re.S)
    assert len(fences) == 1
    namespace = {"__name__": "tests.test1.app.compact_widget_recipe"}
    exec(compile(fences[0], str(REFERENCE), "exec"), namespace)
    assert namespace["CompactWidgetCompatible"] is CompactWidgetCompatible
    widget = namespace["ProductSelect"]
    assert issubclass(widget, CompactWidgetCompatible)

    class ChoiceBook(BookFormSetForm):
        title = forms.ChoiceField(
            choices=[("", "---------"), ("beans", "Beans <roasted> & fresh")],
            widget=widget(attrs={"data-owner": "recipe"}),
            help_text="Choose <carefully> & enjoy",
        )

    monkeypatch.setattr(publisher_formsets["books"].klass, "form", ChoiceBook)
    monkeypatch.setattr(
        publisher_formsets["books"],
        "compact_layout",
        CompactLayout(columns=[CompactColumn("title", span=8)], controls_span=4),
    )
    publisher = Publisher.objects.create(name="Widget recipe publisher")
    Book.objects.create(publisher=publisher, title="beans")
    response = client_user_publisher_formset.get(f"/publisher-formset/{publisher.pk}/update/")
    assert response.status_code == 200
    document = html.fromstring(response.content)
    selects = document.cssselect(".cv-formset-compact-fields select[name$='-title']")
    assert selects
    for select in selects:
        assert select.get("id") == f"id_{select.get('name')}"
        assert select.get("name").startswith("books-")
        assert select.get("data-owner") == "recipe"
        option = select.xpath("./option[@value='beans']")
        assert len(option) == 1 and option[0].get("data-beans") == "1"
        assert option[0].text == "Beans <roasted> & fresh"
        assert not option[0].getchildren()
        labels = document.xpath(".//label[@for=$id]", id=select.get("id"))
        assert len(labels) == 1 and "cv-formset-compact-label" in labels[0].get("class")
    assert b"Beans &lt;roasted&gt; &amp; fresh" in response.content
    assert b"Choose &lt;carefully&gt; &amp; enjoy" in response.content
    assert len(document.cssselect(".cv-formset-compact-headings")) == 1
    assert "Title" in document.cssselect(".cv-formset-compact-headings")[0].text_content()
    assert len(document.cssselect("form.cv-form")) == 1
    assert len(document.cssselect("input[name='csrfmiddlewaretoken']")) == 1
