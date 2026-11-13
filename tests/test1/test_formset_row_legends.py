import pytest
from django.template.loader import render_to_string
from django.test import RequestFactory
from django.utils.translation import gettext_lazy, override
from lxml import html
from pydantic import ValidationError

from crud_views.lib.formsets import FormSet
from tests.test1.app.views_formset import BookFormSet, PublisherFormSetForm, publisher_formsets


@pytest.mark.django_db
@pytest.mark.parametrize("label", [None, False, "", "answer", gettext_lazy("answer"), "<b>Answer</b>"])
@pytest.mark.parametrize("fragment", [False, True])
@pytest.mark.parametrize("parent_label", [None, False])
def test_nested_row_legends_are_independent(label, fragment, parent_label):
    declarations = publisher_formsets.model_copy(deep=True)
    books = declarations["books"]
    books.row_legend = parent_label
    books.children["notes"].row_legend = label
    node = next(
        books.template(pk=None, index=0, force_form_index=3)
        if fragment
        else books.init(RequestFactory().get("/"), [PublisherFormSetForm(cv_view=None)])
    )
    doc = html.fromstring(render_to_string("crud_views/formsets/formset.html", {"x_formset": node}))
    parent_row = doc.cssselect(".cv-formset-row")[0]
    parent_cards = parent_row.cssselect(":scope > .cv-formset-row-card")
    assert bool(parent_cards) is (parent_label is None)
    if parent_cards:
        assert parent_cards[0].cssselect(":scope > legend")[0].text_content() == "Book"
    child_row = doc.cssselect(".cv-formset-row .cv-formset-row")[0]
    if label is False or label == "":
        assert child_row.cssselect(":scope > .cv-formset-form")
        assert not child_row.cssselect(".cv-formset-row-legend, .cv-formset-row-card")
    else:
        child_legend = child_row.cssselect(":scope > .cv-formset-row-card > .cv-formset-row-legend")
        expected = "Book note" if label is None else str(label)
        assert child_legend[0].text_content() == expected
        assert not child_legend[0].cssselect("b")


@pytest.mark.parametrize("label", [True, 0, 0.0, 1, b"answer", [], {}])
def test_row_legend_rejects_unsupported_values(label):
    with pytest.raises(ValidationError, match="row_legend"):
        FormSet(klass=BookFormSet, row_legend=label)


@pytest.mark.parametrize("label", [None, False, "", "answer", gettext_lazy("answer")])
def test_row_legend_keeps_declared_value(label):
    assert FormSet(klass=BookFormSet, row_legend=label).row_legend is label


@pytest.mark.django_db
def test_lazy_legend_is_translated_at_each_render():
    label = gettext_lazy("Yes")
    declaration = FormSet(klass=BookFormSet, row_legend=label, key="books", title="Section title")
    node = next(declaration.init(RequestFactory().get("/"), [PublisherFormSetForm(cv_view=None)]))
    assert node.forms[0].row_title is label
    for language, expected in [("en", "Yes"), ("de", "Ja"), ("fr", "Oui")]:
        with override(language):
            doc = html.fromstring(render_to_string("crud_views/formsets/formset.html", {"x_formset": node}))
            assert doc.cssselect(".cv-formset-row-legend")[0].text_content() == expected
            assert "Section title" in doc.text_content()


@pytest.mark.django_db
def test_row_title_uses_each_polymorphic_instance_and_plain_form_fallback():
    from django.forms import Form, modelform_factory

    from tests.test1.app.models import Car, Truck

    books = publisher_formsets.model_copy(deep=True)["books"]
    node = next(books.init(RequestFactory().get("/"), [PublisherFormSetForm(cv_view=None)]))
    row = node.forms[0]
    for model in (Car, Truck):
        row.form = modelform_factory(model, fields=[])(instance=model())
        assert row.row_title == model._meta.verbose_name.capitalize()
    row.form = Form()
    assert row.row_title == "Books"


@pytest.mark.django_db
@pytest.mark.parametrize("label", [None, False, "", "Unused custom legend", gettext_lazy("Yes")])
@pytest.mark.parametrize("fragment", [False, True])
def test_compact_rows_ignore_row_legends_in_initial_and_fragment_rendering(label, fragment):
    from crud_views.lib.formsets import CompactColumn, CompactLayout

    declaration = FormSet(
        klass=BookFormSet,
        key="books",
        title="Book section",
        row_legend=label,
        compact_layout=CompactLayout([CompactColumn("title", span=8)], controls_span=4),
    )
    node = next(
        declaration.template(pk=None, index=0, force_form_index=3)
        if fragment
        else declaration.init(RequestFactory().get("/"), [PublisherFormSetForm(cv_view=None)])
    )
    rendered = render_to_string("crud_views/formsets/formset.html", {"x_formset": node})
    doc = html.fragment_fromstring(rendered, create_parent="div")
    rows = doc.cssselect(".cv-formset-row-compact")
    assert len(rows) == len(node.forms) > 0
    assert all(row.cssselect("input[name$='-title']") for row in rows)
    assert not doc.cssselect(".cv-formset-row-card, .cv-formset-row-legend")

    node.formset.row_legend = None
    assert rendered == render_to_string("crud_views/formsets/formset.html", {"x_formset": node})
