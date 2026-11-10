"""Compact presentation uses the existing authorized formset lifecycle."""

import pytest
from lxml import html

from tests.lib.helper.forms import form_payload
from tests.test1.app.models import Book, Publisher
from tests.test1.app.views_formset import BookInlineFormSet, publisher_formsets


def test_public_compact_declarations():
    import crud_views.lib.formsets as api
    from crud_views.lib.formsets.compact import CompactColumn, CompactLayout

    assert getattr(api, "CompactColumn", None) is CompactColumn
    assert getattr(api, "CompactLayout", None) is CompactLayout


def test_compact_declarations_are_immutable_and_deepcopy_safe():
    from dataclasses import FrozenInstanceError

    from crud_views.lib.formsets import FormSet
    from crud_views.lib.formsets.compact import CompactColumn, CompactLayout
    from tests.test1.app.views_formset import BookFormSet

    columns = [CompactColumn("title", span=8)]
    layout = CompactLayout(columns, controls_span=4)
    columns.clear()
    assert layout.columns == (CompactColumn("title", span=8),)
    declaration = FormSet(klass=BookFormSet, compact_layout=layout)
    clone = declaration.model_copy(deep=True)
    assert clone.compact_layout == layout
    with pytest.raises(FrozenInstanceError):
        layout.controls_span = 2
    with pytest.raises(FrozenInstanceError):
        clone.compact_layout.columns[0].span = 2


@pytest.mark.parametrize("span", [True, False, "1", 1.0, None, 0, -1, 13])
def test_compact_spans_are_strict(span):
    from crud_views.lib.formsets.compact import CompactColumn, CompactLayout

    with pytest.raises(ValueError, match="integer from 1 to 12"):
        CompactColumn("title", span=span)
    with pytest.raises(ValueError, match="integer from 1 to 12"):
        CompactLayout([CompactColumn("title", span=1)], controls_span=span)


@pytest.mark.parametrize("name", ["", " title", "title ", "two words", None, 1])
def test_compact_names_are_exact(name):
    from crud_views.lib.formsets.compact import CompactColumn

    with pytest.raises(ValueError, match="field name"):
        CompactColumn(name, span=1)


def test_compact_layout_rejects_implicit_or_ambiguous_configuration():
    from crud_views.lib.formsets import FormSet
    from crud_views.lib.formsets.compact import CompactColumn, CompactLayout
    from tests.test1.app.views_formset import BookFormSet

    column = CompactColumn("title", span=8)
    for columns in ([], (), {"field": "title"}, [{"field": "title", "span": 8}], iter([column])):
        with pytest.raises(ValueError, match="columns"):
            CompactLayout(columns, controls_span=4)
    with pytest.raises(ValueError, match="duplicate"):
        CompactLayout([column, column], controls_span=1)
    with pytest.raises(ValueError, match="at most 12"):
        CompactLayout([column], controls_span=5)
    for layout in ({"columns": [{"field": "title", "span": 8}], "controls_span": 4}, [], "compact"):
        with pytest.raises(ValueError, match="compact_layout"):
            FormSet(klass=BookFormSet, compact_layout=layout)
    with pytest.raises(TypeError):
        CompactColumn("title", 8)
    with pytest.raises(TypeError):
        CompactLayout([column], 4)


def _runtime(*, compact=True, form_class=None, **declaration_kwargs):
    from django.test import RequestFactory

    from crud_views.lib.formsets import FormSet
    from crud_views.lib.formsets.compact import CompactColumn, CompactLayout
    from tests.test1.app.views_formset import BookFormSet, PublisherFormSetForm

    klass = BookFormSet if form_class is None else type("ConfiguredBooks", (BookFormSet,), {"form": form_class})
    if compact:
        declaration_kwargs["compact_layout"] = CompactLayout([CompactColumn("title", span=8)], controls_span=4)
    declaration = FormSet(key="books", klass=klass, **declaration_kwargs)
    return next(declaration.init(RequestFactory().get("/"), [PublisherFormSetForm(cv_view=None, instance=Publisher())]))


@pytest.mark.django_db
@pytest.mark.parametrize("explicit_none", [False, True])
@pytest.mark.parametrize("show_labels", [False, True])
def test_classic_keeps_custom_helper_and_query_observations(monkeypatch, explicit_none, show_labels):
    from crispy_forms.layout import Div
    from crispy_forms.utils import render_crispy_form
    from django.db import connection
    from django.test.utils import CaptureQueriesContext

    calls = []

    def classic_layout(self):
        calls.append(self.prefix)
        return [Div("title", css_class="custom-classic-layout"), self.form_control]

    def forbidden(*args):
        pytest.fail("Classic mode must not compute compact metadata")

    monkeypatch.setattr(BookInlineFormSet, "get_helper_layout_fields", classic_layout)
    monkeypatch.setattr("crud_views.lib.formsets.render_tree._compact_projection", forbidden)
    kwargs = {"compact_layout": None} if explicit_none else {}
    node = _runtime(compact=False, form_show_labels=show_labels, **kwargs)
    row = node.forms[0]
    with CaptureQueriesContext(connection) as baseline_queries:
        baseline = render_crispy_form(row.form, helper=node.instance.helper)
    baseline_calls = len(calls)
    with CaptureQueriesContext(connection) as actual_queries:
        actual = render_crispy_form(row.form, helper=row.helper)
    assert actual == baseline
    assert len(calls) == baseline_calls * 2
    assert [q["sql"] for q in actual_queries] == [q["sql"] for q in baseline_queries]
    assert "custom-classic-layout" in actual
    assert bool(html.fromstring(actual).cssselect("label")) is show_labels
    assert node.compact_columns == ()


@pytest.mark.django_db
def test_compact_constructor_labels_are_request_local_and_escaped():
    from django.template.loader import render_to_string

    from tests.test1.app.views_formset import BookFormSetForm

    class LabelledBook(BookFormSetForm):
        label = "<script>alert('label')</script>"

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields["title"].label = self.label

    first = _runtime(form_class=LabelledBook, form_show_labels=False)
    first_html = render_to_string("crud_views/formsets/formset.html", {"x_formset": first})
    assert "<script>alert" not in first_html
    assert "&lt;script&gt;" in first_html
    first_document = html.fromstring(first_html)
    assert first_document.cssselect("label.cv-formset-compact-label")[0].text_content().strip().startswith("<script>")
    LabelledBook.label = "Second request title"
    second = _runtime(form_class=LabelledBook)
    assert second.compact_columns[0].label == "Second request title"
    assert first.compact_columns[0].label == "<script>alert('label')</script>"
    assert render_to_string("crud_views/formsets/formset.html", {"x_formset": first}) == first_html


@pytest.mark.django_db
def test_compact_labels_resolve_under_each_active_translation():
    from django.utils.translation import gettext, gettext_lazy, override

    from tests.test1.app.views_formset import BookFormSetForm

    class TranslatedBook(BookFormSetForm):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields["title"].label = gettext_lazy("Yes")

    nodes = []
    labels = []
    for language in ("en", "de"):
        with override(language):
            node = _runtime(form_class=TranslatedBook)
            nodes.append(node)
            labels.append(node.compact_columns[0].label)
            assert labels[-1] == gettext("Yes")
    assert labels[0] != labels[1]
    assert [node.compact_columns[0].label for node in nodes] == labels


@pytest.mark.django_db
@pytest.mark.parametrize("label", ["", " "])
def test_compact_rejects_empty_effective_label(label):
    from django.core.exceptions import ImproperlyConfigured

    node = _runtime()
    node.forms[0].form.fields["title"].label = label
    with pytest.raises(ImproperlyConfigured, match=r"books.*title.*label"):
        _ = node.compact_columns


@pytest.mark.django_db
def test_classic_polymorphic_dispatch_keeps_form_owned_helper(monkeypatch):
    from polymorphic.formsets import BasePolymorphicInlineFormSet

    node = _runtime(compact=False)
    sentinel = object()
    monkeypatch.setattr(node.formset, "klass", BasePolymorphicInlineFormSet)
    monkeypatch.setattr(type(node.forms[0].form), "helper", property(lambda self: sentinel))
    assert node.forms[0].helper is sentinel


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
