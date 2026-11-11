"""Compact presentation uses the existing authorized formset lifecycle."""

import pytest
from lxml import html

from tests.lib.helper.forms import form_payload
from tests.test1.app.models import Book, Publisher
from tests.test1.app.views_formset import BookInlineFormSet, publisher_formsets
from tests.test1.test_fragment_authorization import deep_leaf_formset as deep_leaf_formset


def test_public_compact_declarations():
    import crud_views.lib.formsets as api
    from crud_views.lib.formsets.compact import CompactColumn, CompactLayout, CompactWidgetCompatible

    assert getattr(api, "CompactColumn", None) is CompactColumn
    assert getattr(api, "CompactLayout", None) is CompactLayout
    assert getattr(api, "CompactWidgetCompatible", None) is CompactWidgetCompatible
    assert not any(callable(value) for value in vars(CompactWidgetCompatible).values())


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


@pytest.mark.django_db
@pytest.mark.parametrize("dense", [False, True])
def test_compact_presentation_columns_labels_and_owned_feedback(dense):
    from django import forms
    from django.forms.utils import ErrorList
    from django.template.loader import render_to_string

    from crud_views.lib.formsets import CompactColumn, CompactLayout

    node = _runtime(factory_attrs={"extra": 2})
    names = ["title", *[f"score_{i}" for i in range(7)]] if dense else ["title"]
    spans = [3, *([1] * 7)] if dense else [4]
    for row in node.forms:
        row.form.fields["title"].label = "<script>Long translated heading</script>"
        row.form.fields["title"].help_text = "Detailed help for this field"
        for name in names[1:]:
            row.form.fields[name] = forms.DecimalField(label=name, required=False)
    node.formset.compact_layout = CompactLayout(
        [CompactColumn(name, span=span) for name, span in zip(names, spans, strict=True)], controls_span=2
    )
    first = node.forms[0].form
    first.is_bound = True
    first.data = {first.add_prefix("title"): "Kept title"}
    first.add_error("title", "Owned field error")
    first.add_error(None, "Owned row error")
    node.instance._non_form_errors = ErrorList(["Owned formset error"])
    doc = html.fromstring(render_to_string("crud_views/formsets/formset.html", {"x_formset": node}))
    headings = doc.cssselect(".cv-formset-compact-headings")
    assert len(headings) == 1
    heading = headings[0]
    assert not heading.xpath("ancestor::div[@cv-data-formset-form-prefix]")
    assert [cell.get("class") for cell in heading] == [f"col-md-{span}" for span in [*spans, 2]]
    assert not heading.cssselect("script")
    assert "<script>Long translated heading</script>" in heading.text_content()
    assert len(heading.cssselect(".asteriskField")) == 1
    rows = doc.cssselect(".cv-formset-row-compact")
    for row in rows:
        cells = row.cssselect(".cv-formset-compact-fields > div")
        assert [cell.get("class").strip() for cell in cells] == [f"col-md-{span}" for span in [*spans, 2]]
        for name in names:
            field = row.cssselect(f'input[name$="-{name}"]')
            assert len(field) == 1
            labels = row.xpath(".//label[@for=$id]", id=field[0].get("id"))
            assert len(labels) == 1
            assert "cv-formset-compact-label" in labels[0].get("class")
            assert "aria-hidden" not in labels[0].attrib
        assert len(row.cssselect("label .asteriskField")) == 1
        assert not row.cssselect(".cv-formset-compact-headings")
    assert "Owned field error" in rows[0].text_content()
    assert "Owned row error" in rows[0].text_content()
    assert "Owned field error" not in rows[1].text_content()
    assert "Owned row error" not in rows[1].text_content()
    assert "Owned formset error" in doc.text_content()
    assert all("Owned formset error" not in row.text_content() for row in rows)
    assert not doc.cssselect('[role="grid"], [role="gridcell"]')


@pytest.mark.django_db
def test_compact_presentation_heading_include_is_overridable():
    from copy import deepcopy

    from django.conf import settings
    from django.template.loader import render_to_string
    from django.test import override_settings

    templates = deepcopy(settings.TEMPLATES)
    templates[0]["APP_DIRS"] = False
    templates[0]["OPTIONS"]["loaders"] = [
        ("django.template.loaders.locmem.Loader", {"crud_views/formsets/compact_headings.html": "THEME HEADINGS"}),
        "django.template.loaders.filesystem.Loader",
        "django.template.loaders.app_directories.Loader",
    ]
    node = _runtime()
    with override_settings(TEMPLATES=templates):
        page = render_to_string("crud_views/formsets/formset.html", {"x_formset": node})
        assert page.count("THEME HEADINGS") == 1
        node.render_rows_only = True
        fragment = render_to_string("crud_views/formsets/formset.html", {"x_formset": node})
        assert "THEME HEADINGS" not in fragment
        assert "cv-formset-row-compact" in fragment


@pytest.mark.django_db
@pytest.mark.parametrize("parent_compact,child_compact", [(True, True), (True, False), (False, True), (False, False)])
@pytest.mark.parametrize("show_labels", [False, True])
def test_compact_nested_geometry_is_node_local(parent_compact, child_compact, show_labels):
    from django.template.loader import render_to_string

    from crud_views.lib.formsets import CompactColumn, CompactLayout, FormSet
    from tests.test1.app.views_formset import BookNoteFormSet

    child_layout = CompactLayout([CompactColumn("note", span=6)], controls_span=2) if child_compact else None
    node = _runtime(
        compact=parent_compact,
        form_show_labels=show_labels,
        children={
            "notes": FormSet(
                key="notes", klass=BookNoteFormSet, compact_layout=child_layout, form_show_labels=show_labels
            )
        },
    )
    child = node.forms[0].formsets[0]
    assert (child.has_pre_col, child.col, child.col_pre) == ((False, 12, 0) if child_compact else (True, 11, 1))
    assert (node.has_pre_col, node.col, node.col_pre) == (False, 12, 0)
    doc = html.fromstring(render_to_string("crud_views/formsets/formset.html", {"x_formset": node}))
    child_fieldset = doc.get_element_by_id(f"cv-formset-fieldset-{child.prefix}")
    assert ("cv-formset-compact-child" in child_fieldset.get("class")) is child_compact
    owner = child_fieldset.xpath("ancestor::div[@cv-data-formset-form-prefix][1]")[0]
    assert owner.get("cv-data-formset-form-prefix") == node.forms[0].prefix
    assert child_fieldset.getparent().get("class") == ("col-12" if child_compact else "col-11")
    for current in (node, child):
        fieldset = doc.get_element_by_id(f"cv-formset-fieldset-{current.prefix}")
        own_content = fieldset.cssselect(".cv-formset-content")[0]
        own_headings = own_content.xpath('./div[contains(@class, "cv-formset-compact-headings")]')
        assert len(own_headings) == int(current.formset.compact_layout is not None)
        field_name = "note" if current is child else "title"
        field = fieldset.cssselect(f'input[name="{current.forms[0].prefix}-{field_name}"]')[0]
        labels = fieldset.xpath(".//label[@for=$id]", id=field.get("id"))
        assert bool(labels) is (current.formset.compact_layout is not None or show_labels)
        if labels:
            assert ("cv-formset-compact-label" in labels[0].get("class", "")) is (
                current.formset.compact_layout is not None
            )


def _nested_declarations(parent_compact=True, leaf_class=None):
    from crud_views.lib.formsets import CompactColumn, CompactLayout, FormSet, FormSets
    from tests.test1.app.views_formset import BookFormSet, BookNoteFormSet

    def layout(name, span, controls):
        return CompactLayout([CompactColumn(name, span=span)], controls_span=controls)

    leaves = {"leaf": FormSet(klass=leaf_class, compact_layout=layout("text", 8, 4))} if leaf_class else {}
    return FormSets(
        formsets={
            "books": FormSet(
                klass=BookFormSet,
                compact_layout=layout("title", 8, 4) if parent_compact else None,
                children={
                    "notes": FormSet(klass=BookNoteFormSet, form_show_labels=True),
                    "memos": FormSet(klass=BookNoteFormSet, compact_layout=layout("note", 4, 2), children=leaves),
                },
            )
        }
    )


@pytest.mark.django_db
@pytest.mark.parametrize("parent_compact", [False, True])
def test_compact_nested_siblings_keep_headings_helpers_and_error_owners(parent_compact, monkeypatch):
    from django.forms.utils import ErrorList
    from django.template.loader import render_to_string
    from django.test import RequestFactory

    from tests.test1.app.views_formset import BookNoteInlineFormSet, PublisherFormSetForm

    calls = []
    original = BookNoteInlineFormSet.get_helper_layout_fields

    def classic_fields(self):
        calls.append(self.prefix)
        return original(self)

    monkeypatch.setattr(BookNoteInlineFormSet, "get_helper_layout_fields", classic_fields)
    declarations = _nested_declarations(parent_compact)
    node = next(declarations["books"].init(RequestFactory().get("/"), [PublisherFormSetForm(cv_view=None)]))
    notes, memos = node.forms[0].formsets
    for child in (notes, memos):
        form = child.forms[0].form
        form.is_bound = True
        form.data = {form.add_prefix("note"): "Preserved note"}
        form.add_error("note", f"Field error for {child.key}")
        form.add_error(None, f"Row error for {child.key}")
        child.instance._non_form_errors = ErrorList([f"Formset error for {child.key}"])
    doc = html.fromstring(render_to_string("crud_views/formsets/formset.html", {"x_formset": node}))
    assert calls == [notes.prefix]
    for child, compact in ((notes, False), (memos, True)):
        fieldset = doc.get_element_by_id(f"cv-formset-fieldset-{child.prefix}")
        assert ("cv-formset-compact-child" in fieldset.get("class")) is compact
        assert len(fieldset.cssselect(".cv-formset-compact-headings")) == int(compact)
        assert (
            fieldset.xpath("ancestor::div[@cv-data-formset-form-prefix][1]")[0].get("cv-data-formset-form-prefix")
            == node.forms[0].prefix
        )
        for error in ("Field", "Row", "Formset"):
            assert f"{error} error for {child.key}" in fieldset.text_content()
        other = memos if child is notes else notes
        assert f"error for {other.key}" not in fieldset.text_content()
        own_row = fieldset.cssselect(".cv-formset-row")[0]
        assert f"Formset error for {child.key}" not in own_row.text_content()
        if compact:
            cells = fieldset.cssselect(".cv-formset-compact-headings > div")
            assert [c.get("class") for c in cells] == ["col-md-4", "col-md-2"]


@pytest.mark.django_db(transaction=True)
def test_compact_nested_grandchild_and_authorized_fragments(
    deep_leaf_formset, client_user_publisher_formset, monkeypatch
):
    from tests.test1.app.models import BookNote
    from tests.test1.app.views_formset import PublisherFormSetUpdateView
    from tests.test1.test_fragment_authorization import _assert_raw_wrappers, browser_add_row

    Leaf, leaf_class = deep_leaf_formset
    declarations = _nested_declarations(leaf_class=leaf_class)
    monkeypatch.setattr(PublisherFormSetUpdateView, "cv_formsets", declarations)
    publisher = Publisher.objects.create(name="Nested")
    book = Book.objects.create(publisher=publisher, title="Owner")
    note = BookNote.objects.create(book=book, note="Grandchild owner")
    Leaf.objects.create(note=note, text="Leaf value")
    url = f"/publisher-formset/{publisher.pk}/update/"
    response = client_user_publisher_formset.get(url)
    assert response.status_code == 200
    _assert_raw_wrappers(response.content.decode())
    doc = html.fromstring(response.content)

    def assert_tree(tree):
        ids = tree.xpath(".//*[@id]/@id")
        assert len(ids) == len(set(ids))
        for fieldset in tree.cssselect("fieldset.cv-formset-fieldset"):
            compact = "cv-formset-compact" in fieldset.get("class").split()
            content = fieldset.cssselect(".cv-formset-content")[0]
            headings = content.xpath('./div[contains(@class, "cv-formset-compact-headings")]')
            assert len(headings) == int(compact)
            key = fieldset.get("cv-data-formset-key")
            if key == "books":
                continue
            owner = fieldset.xpath("ancestor::div[@cv-data-formset-form-prefix][1]")[0]
            if key == "books-memos-leaf":
                assert owner.get("cv-data-formset-form-prefix").startswith("books-memos-")
                assert fieldset.getparent().get("class") == "col-12"
            else:
                assert owner.get("cv-data-formset-form-prefix").startswith("books-")
        for field in tree.cssselect(".cv-formset-compact-fields input:not([type=hidden])"):
            labels = tree.xpath(".//label[@for=$id]", id=field.get("id"))
            assert len(labels) == 1

    assert_tree(doc)
    for key in ("books", "books-memos", "books-memos-leaf"):
        fieldset = doc.cssselect(f'fieldset[cv-data-formset-key="{key}"]')[0]
        prefix = fieldset.get("cv-data-formset-prefix")
        params = browser_add_row(response.content, prefix)
        fragment_response = client_user_publisher_formset.get(url, params)
        assert fragment_response.status_code == 200
        fragment = fragment_response.json()
        _assert_raw_wrappers(fragment["html"])
        tree = html.fragment_fromstring(fragment["html"], create_parent="div")
        assert_tree(tree)
        # Only advertised rows are roots; their complete children stay inside them.
        roots = [element for element in tree if isinstance(element.tag, str)]
        assert [row.get("cv-data-formset-form-prefix") for row in roots] == fragment["rows"]
        assert all("cv-formset-row-compact" in row.get("class") for row in roots)
        for heading in tree.cssselect(".cv-formset-compact-headings"):
            assert heading.xpath("ancestor::fieldset[contains(@class, 'cv-formset-compact')]")
        if key == "books":
            assert tree.cssselect('fieldset[cv-data-formset-key="books-notes"]')
            assert tree.cssselect('fieldset[cv-data-formset-key="books-memos-leaf"]')
        if key == "books-memos":
            assert params["template"] == "books|memos"
            assert params["formset_parent_prefix_key"] == f"{publisher.pk}-0-0"
            assert tree.cssselect('fieldset[cv-data-formset-key="books-memos-leaf"]')
        if key == "books-memos-leaf":
            assert params["template"] == "books|memos|leaf"
            assert not tree.cssselect(".cv-formset-compact-headings")


def _runtime(*, compact=True, form_class=None, parent=None, factory_attrs=None, **declaration_kwargs):
    from django.test import RequestFactory

    from crud_views.lib.formsets import FormSet
    from crud_views.lib.formsets.compact import CompactColumn, CompactLayout
    from tests.test1.app.views_formset import BookFormSet, PublisherFormSetForm

    attrs = dict(factory_attrs or {})
    if form_class is not None:
        attrs["form"] = form_class
    klass = type("ConfiguredBooks", (BookFormSet,), attrs) if attrs else BookFormSet
    if compact:
        declaration_kwargs["compact_layout"] = CompactLayout([CompactColumn("title", span=8)], controls_span=4)
    declaration = FormSet(key="books", klass=klass, **declaration_kwargs)
    parent = Publisher() if parent is None else parent
    return next(declaration.init(RequestFactory().get("/"), [PublisherFormSetForm(cv_view=None, instance=parent)]))


@pytest.mark.django_db
@pytest.mark.parametrize("explicit_none", [False, True])
@pytest.mark.parametrize("show_labels", [False, True])
def test_compact_classic_keeps_custom_helper_and_query_observations(monkeypatch, explicit_none, show_labels):
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
def test_compact_hidden_errors_and_plain_help_are_escaped(monkeypatch, compact_books, client_user_publisher_formset):
    from django import forms
    from django.core.exceptions import ValidationError

    from tests.test1.app.views_formset import BookFormSetForm

    class ErrorBook(BookFormSetForm):
        secret = forms.CharField(widget=forms.HiddenInput, initial="initial-secret")

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields["title"].help_text = "<script>help attack</script>"

        def clean(self):
            data = super().clean()
            if data.get("secret") == "invalid-secret":
                self.add_error("secret", "<script>hidden attack</script>")
                self.add_error("title", "<script>field attack</script>")
                self.add_error(None, "<script>row attack</script>")
            return data

    original_clean = BookInlineFormSet.clean

    def clean_formset(self):
        original_clean(self)
        if any(f.data.get(f.add_prefix("secret")) == "invalid-secret" for f in self.forms):
            raise ValidationError("<script>formset attack</script>")

    monkeypatch.setattr(publisher_formsets["books"].klass, "form", ErrorBook)
    monkeypatch.setattr(BookInlineFormSet, "clean", clean_formset)
    publisher = Publisher.objects.create(name="Errors")
    book = Book.objects.create(publisher=publisher, title="Original")
    url = f"/publisher-formset/{publisher.pk}/update/"
    initial = client_user_publisher_formset.get(url)
    payload = form_payload(initial)
    title_name = next(k for k, v in payload.items() if k.endswith("-title") and v == "Original")
    prefix = title_name.removesuffix("-title")
    payload[title_name] = "Retained value"
    payload[f"{prefix}-secret"] = "invalid-secret"
    response = client_user_publisher_formset.post(url, payload)
    assert response.status_code == 200
    document = html.fromstring(response.content)
    row = document.xpath("//div[@cv-data-formset-form-prefix=$prefix]", prefix=prefix)[0]
    own = row.cssselect(".cv-formset-form")[0]
    for message in ("hidden attack", "field attack", "row attack"):
        assert own.text_content().count(message) == 1
    assert not own.cssselect("script")
    assert "help attack" in own.text_content()
    assert own.cssselect("input[name$='-title']")[0].get("value") == "Retained value"
    assert "cv-formset-row-compact" in row.get("class")
    assert not row.xpath(".//input[@required]")
    assert own.cssselect(".asteriskField")
    fieldset = row.xpath("ancestor::fieldset[contains(@class, 'cv-formset-compact')]")[0]
    formset_message = fieldset.xpath(".//li[contains(., 'formset attack')]")
    assert len(formset_message) == 1
    assert not formset_message[0].xpath("ancestor::div[contains(@class, 'cv-formset-row')]")
    for suffix in ("title", "secret", "id", "publisher", "DELETE"):
        assert len(own.xpath(".//input[@name=$name]", name=f"{prefix}-{suffix}")) == 1
    book.refresh_from_db()
    assert book.title == "Original"
    payload[f"{prefix}-secret"] = "valid-secret"
    result = client_user_publisher_formset.post(url, payload)
    assert result.status_code == 302
    book.refresh_from_db()
    assert book.title == "Retained value"


@pytest.mark.django_db
def test_compact_hidden_policy_errors_and_values_render_once(monkeypatch):
    from django import forms
    from django.template.loader import render_to_string

    monkeypatch.setattr("crud_views.lib.ordered.get_ordered_model", lambda: None)
    node = _runtime(factory_attrs={"can_order": True})
    form = node.forms[0].form
    form.fields["secret"] = forms.CharField(widget=forms.HiddenInput)
    form.data = {form.add_prefix("title"): "A title", form.add_prefix("secret"): "kept"}
    form.is_bound = True
    for name in ("secret", "id", "publisher", "ORDER", "DELETE"):
        form.add_error(name, f"Error on {name}")
    for _ in range(2):
        rendered = render_to_string("crud_views/formsets/formset.html", {"x_formset": node})
        doc = html.fromstring(rendered)
        for name in ("secret", "id", "publisher", "ORDER", "DELETE"):
            assert len(doc.xpath(".//input[@name=$name]", name=form.add_prefix(name))) == 1
            assert doc.text_content().count(f"Error on {name}") == 1
        assert doc.cssselect('input[name$="-secret"]')[0].get("value") == "kept"


@pytest.mark.django_db
def test_compact_hidden_identity_roles_do_not_depend_on_original_widget():
    from django import forms
    from django.template.loader import render_to_string

    node = _runtime()
    for name in ("id", "publisher"):
        node.forms[0].form.fields[name].widget = forms.TextInput()
    for _ in range(2):
        doc = html.fromstring(render_to_string("crud_views/formsets/formset.html", {"x_formset": node}))
        for name in ("id", "publisher"):
            fields = doc.xpath(".//input[@name=$name]", name=node.forms[0].form.add_prefix(name))
            assert len(fields) == 1 and fields[0].get("type") == "hidden"


@pytest.mark.django_db
@pytest.mark.parametrize("state", ["zero", "blank", "existing", "no_controls", "no_extra_delete"])
def test_compact_empty_and_control_policy_edges(state):
    from django.template.loader import render_to_string

    parent = Publisher.objects.create(name="States")
    attrs = {}
    if state in ("existing", "no_controls"):
        Book.objects.create(publisher=parent, title="Existing")
    if state in ("zero", "existing", "no_controls"):
        attrs["extra"] = 0
    if state == "no_controls":
        attrs.update(edit_only=True, can_order=False, can_delete=False)
    if state == "no_extra_delete":
        attrs["can_delete_extra"] = False
    node = _runtime(parent=parent, factory_attrs=attrs)
    rendered = render_to_string("crud_views/formsets/formset.html", {"x_formset": node})
    doc = html.fromstring(rendered)
    assert len(doc.cssselect(".cv-formset-compact-headings")) == 1
    assert len(doc.cssselect('input[name$="-TOTAL_FORMS"]')) == 1
    assert len(doc.cssselect(".cv-formset-row-compact")) == (0 if state == "zero" else 1)
    if state in ("zero", "no_controls"):
        assert not doc.cssselect("button")
    if state == "no_controls":
        cells = doc.cssselect(".cv-formset-compact-fields > div")
        assert "col-md-4" in cells[-1].get("class")
        assert "d-none" in cells[-1].get("class") and "d-md-block" in cells[-1].get("class")
    if state == "no_extra_delete":
        assert not doc.cssselect('input[name$="-DELETE"], .cv-form-ctrl-delete')
        assert doc.cssselect(".cv-form-ctrl-add")
    if state in ("zero", "existing"):
        with pytest.raises(IndexError):
            list(node.formset.template(pk=None, index=0, force_form_index=1))


@pytest.mark.django_db
def test_compact_optional_disabled_fields_and_safe_text():
    from django import forms
    from django.template.loader import render_to_string
    from django.utils.safestring import mark_safe

    from crud_views.lib.formsets import CompactColumn, CompactLayout

    node = _runtime()
    form = node.forms[0].form
    form.fields["title"].label = mark_safe("<em>Safe label</em>")
    form.fields["title"].help_text = mark_safe("<em>Safe help</em>")
    form.fields["optional"] = forms.CharField(required=False, disabled=True, initial="Fixed")
    node.formset.compact_layout = CompactLayout(
        [CompactColumn("title", span=4), CompactColumn("optional", span=4)], controls_span=4
    )
    doc = html.fromstring(render_to_string("crud_views/formsets/formset.html", {"x_formset": node}))
    field = doc.cssselect('input[name$="-optional"]')
    assert len(field) == 1 and "disabled" in field[0].attrib and field[0].get("value") == "Fixed"
    assert len(doc.cssselect(".cv-formset-compact-headings .asteriskField")) == 1
    assert len(doc.cssselect("em")) == 3


@pytest.mark.django_db
def test_compact_management_error_stays_on_zero_total_owner(compact_books, client_user_publisher_formset):
    publisher = Publisher.objects.create(name="Management")
    url = f"/publisher-formset/{publisher.pk}/update/"
    payload = form_payload(client_user_publisher_formset.get(url))
    key = next(k for k in payload if k.startswith("books-") and k.endswith("-TOTAL_FORMS"))
    del payload[key]
    response = client_user_publisher_formset.post(url, payload)
    assert response.status_code == 200
    doc = html.fromstring(response.content)
    fieldset = doc.cssselect("fieldset.cv-formset-compact")[0]
    assert "ManagementForm data is missing" in fieldset.text_content()
    assert not fieldset.cssselect(".cv-formset-row-compact")
    assert len(fieldset.cssselect(".cv-formset-compact-headings")) == 1
    assert not fieldset.cssselect(".cv-form-ctrl-add")


@pytest.mark.django_db
@pytest.mark.parametrize("label", ["", " "])
def test_compact_rejects_empty_effective_label(label):
    from django.core.exceptions import ImproperlyConfigured

    node = _runtime()
    node.forms[0].form.fields["title"].label = label
    with pytest.raises(ImproperlyConfigured, match=r"books.*title.*label"):
        _ = node.compact_columns


@pytest.mark.django_db
def test_compact_classic_polymorphic_dispatch_keeps_form_owned_helper(monkeypatch):
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


@pytest.mark.django_db
def test_compact_marked_select_requests(monkeypatch, compact_books, client_user_publisher_formset):
    from django import forms

    import crud_views.lib.formsets as api
    from crud_views.lib.formsets import compact
    from tests.test1.app.views_formset import BookFormSetForm
    from tests.test1.test_fragment_authorization import browser_add_row

    marker = getattr(api, "CompactWidgetCompatible", None)
    assert marker is not None, "CompactWidgetCompatible must be publicly importable"
    assert marker is compact.CompactWidgetCompatible

    class ProductSelect(marker, forms.Select):
        def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
            option = super().create_option(name, value, label, selected, index, subindex=subindex, attrs=attrs)
            if value == "Original":
                option["attrs"]["data-beans"] = "1"
            return option

    class ChoiceBook(BookFormSetForm):
        title = forms.ChoiceField(
            choices=[("", "---------"), ("Original", "Original beans"), ("Retained", "Retained"), ("Saved", "Saved")],
            widget=ProductSelect,
            help_text="Choose the book title",
        )

    monkeypatch.setattr(publisher_formsets["books"].klass, "form", ChoiceBook)
    publisher = Publisher.objects.create(name="Marked publisher")
    book = Book.objects.create(publisher=publisher, title="Original")
    retained = Book.objects.create(publisher=publisher, title="Retained")
    url = f"/publisher-formset/{publisher.pk}/update/"

    def assert_rows(tree, *, headings):
        owned_headings = tree.cssselect(".cv-formset-compact-headings")
        assert len(owned_headings) == headings
        for heading in owned_headings:
            assert "Title" in heading.text_content()
            assert not heading.xpath("ancestor::div[@cv-data-formset-form-prefix]")
        selects = tree.cssselect(".cv-formset-row-compact select[name$='-title']")
        assert selects
        for select in selects:
            name = select.get("name")
            assert select.get("id") == f"id_{name}"
            row = select.xpath("ancestor::div[@cv-data-formset-form-prefix][1]")[0]
            own = row.cssselect(".cv-formset-form")[0]
            assert name == f"{row.get('cv-data-formset-form-prefix')}-title"
            labels = own.xpath(".//label[@for=$id]", id=select.get("id"))
            assert len(labels) == 1 and "cv-formset-compact-label" in labels[0].get("class")
            assert "Choose the book title" in own.text_content()
            option = select.cssselect("option[value='Original']")
            assert len(option) == 1 and option[0].get("data-beans") == "1"
            assert option[0].text == "Original beans"
            for suffix in ("id", "publisher", "DELETE"):
                controls = own.xpath(".//input[@name=$name]", name=f"{name.removesuffix('-title')}-{suffix}")
                assert len(controls) == 1 and controls[0].get("type") == "hidden"
            assert not own.cssselect(".cv-formset-compact-headings")
        return selects

    initial = client_user_publisher_formset.get(url)
    assert initial.status_code == 200
    document = html.fromstring(initial.content)
    assert len(document.cssselect("form.cv-form")) == 1
    assert len(document.cssselect("input[name='csrfmiddlewaretoken']")) == 1
    fieldset = document.cssselect('fieldset[cv-data-formset-key="books"]')[0]
    assert_rows(fieldset, headings=1)
    payload = form_payload(initial)
    original_name = next(k for k, v in payload.items() if k.endswith("-title") and v == "Original")
    retained_name = next(k for k, v in payload.items() if k.endswith("-title") and v == "Retained")
    extra_names = [k for k in payload if k.endswith("-title") and k not in (original_name, retained_name)]
    assert len(extra_names) == 1 and payload[extra_names[0]] == ""

    # The independently invalid retained row forces redisplay even when the first is deleted.
    for invalid in ("", "not-a-choice"):
        payload[retained_name] = invalid
        for delete_value in ("", "on", ""):
            payload[original_name.removesuffix("-title") + "-DELETE"] = delete_value
            response = client_user_publisher_formset.post(url, payload)
            assert response.status_code == 200
            tree = html.fromstring(response.content)
            current = tree.cssselect('fieldset[cv-data-formset-key="books"]')[0]
            assert_rows(current, headings=1)
            invalid_row = tree.xpath(
                "//select[@name=$name]/ancestor::div[@cv-data-formset-form-prefix][1]", name=retained_name
            )[0]
            other_row = tree.xpath(
                "//select[@name=$name]/ancestor::div[@cv-data-formset-form-prefix][1]", name=original_name
            )[0]
            message = "This field is required." if invalid == "" else "Select a valid choice."
            assert message in invalid_row.text_content() and message not in other_row.text_content()
            if invalid == "":
                assert invalid_row.cssselect("option[value=''][selected]")
            delete_input = other_row.xpath(
                ".//input[@name=$name]", name=original_name.removesuffix("-title") + "-DELETE"
            )[0]
            assert bool(delete_input.get("value")) == bool(delete_value)

    params = browser_add_row(initial.content, fieldset.get("cv-data-formset-prefix"))
    added = client_user_publisher_formset.get(url, params)
    assert added.status_code == 200
    fragment = added.json()
    added_tree = html.fragment_fromstring(fragment["html"], create_parent="div")
    added_selects = assert_rows(added_tree, headings=0)
    assert [s.get("name").removesuffix("-title") for s in added_selects] == fragment["rows"]
    assert not added_tree.cssselect("form, input[name='csrfmiddlewaretoken']")

    payload[original_name] = "Saved"
    payload[retained_name] = "Retained"
    payload[original_name.removesuffix("-title") + "-DELETE"] = ""
    assert payload[extra_names[0]] == ""
    result = client_user_publisher_formset.post(url, payload)
    assert result.status_code == 302
    book.refresh_from_db()
    retained.refresh_from_db()
    assert book.title == "Saved" and retained.title == "Retained"
    assert Book.objects.filter(publisher=publisher).count() == 2


@pytest.mark.django_db
@pytest.mark.parametrize("kind", ["field_type", "widget_type", "required", "label", "missing", "extra"])
def test_compact_schema_rejects_heterogeneous_rows(kind):
    from django import forms
    from django.core.exceptions import ImproperlyConfigured

    node = _runtime(factory_attrs={"extra": 2})
    second = node.forms[1].form
    if kind == "field_type":
        second.fields["title"] = forms.RegexField(".*", label="Title")
    elif kind == "widget_type":
        second.fields["title"].widget = forms.NumberInput()
    elif kind == "required":
        second.fields["title"].required = False
    elif kind == "label":
        second.fields["title"].label = "Different"
    elif kind == "missing":
        del second.fields["title"]
    else:
        second.fields["other"] = forms.CharField(required=False, disabled=True)
    field = "other" if kind == "extra" else "title"
    with pytest.raises(ImproperlyConfigured, match=rf"books.*{field}"):
        _ = node.forms[0].helper


@pytest.mark.django_db
@pytest.mark.parametrize(
    "kind",
    [
        "checkbox",
        "radio",
        "multiple",
        "multiwidget",
        "file",
        "password",
        "textarea",
        "subclass",
        "template",
        "option",
        "input_type",
        "select_multiple",
    ],
)
def test_compact_schema_rejects_unsupported_widget_shape(kind):
    from django import forms
    from django.core.exceptions import ImproperlyConfigured

    node = _runtime()
    choices = {
        "checkbox": forms.CheckboxInput,
        "radio": forms.RadioSelect,
        "multiple": forms.SelectMultiple,
        "multiwidget": forms.SplitDateTimeWidget,
        "file": forms.FileInput,
        "password": forms.PasswordInput,
        "textarea": forms.Textarea,
        "subclass": type("CustomText", (forms.TextInput,), {}),
    }
    widget = choices.get(kind, forms.Select if kind in ("option", "select_multiple") else forms.TextInput)()
    if kind == "template":
        widget.template_name = "custom.html"
    elif kind == "option":
        widget.option_template_name = "custom_option.html"
    elif kind == "input_type":
        widget.input_type = "password"
    elif kind == "select_multiple":
        widget.allow_multiple_selected = True
    node.forms[0].form.fields["title"].widget = widget
    with pytest.raises(ImproperlyConfigured, match=r"books.*title.*widget"):
        _ = node.forms[0].helper


@pytest.mark.django_db
@pytest.mark.parametrize(
    "kind",
    [
        "checkbox",
        "radio",
        "multiple",
        "multiwidget",
        "file",
        "password",
        "textarea",
        "subclass",
        "template",
        "option",
        "input_type",
        "select_multiple",
    ],
)
def test_compact_marked_schema_admission(kind):
    from django import forms

    from crud_views.lib.formsets import CompactWidgetCompatible

    families = {
        "checkbox": forms.CheckboxInput,
        "radio": forms.RadioSelect,
        "multiple": forms.SelectMultiple,
        "multiwidget": forms.SplitDateTimeWidget,
        "file": forms.FileInput,
        "password": forms.PasswordInput,
        "textarea": forms.Textarea,
        "subclass": type("CustomText", (forms.TextInput,), {}),
    }
    base = families.get(kind, forms.Select if kind in ("option", "select_multiple") else forms.TextInput)
    marked = type("MarkedWidget", (CompactWidgetCompatible, base), {})
    widget = marked()
    if kind == "template":
        widget.template_name = "custom.html"
    elif kind == "option":
        widget.option_template_name = "custom_option.html"
    elif kind == "input_type":
        widget.input_type = "password"
    elif kind == "select_multiple":
        widget.allow_multiple_selected = True
    node = _runtime()
    node.forms[0].form.fields["title"].widget = widget
    # These deliberately mismatched pairs prove admission, never output certification.
    assert node.compact_columns[0].widget_type is marked
    assert node.forms[0].helper.label_class == "cv-formset-compact-label"


@pytest.mark.django_db
def test_compact_marked_inheritance_and_pretty_name():
    from django import forms

    from crud_views.lib.formsets import CompactWidgetCompatible

    class MarkedText(CompactWidgetCompatible, forms.TextInput):
        pass

    class Descendant(MarkedText):
        pass

    node = _runtime(factory_attrs={"extra": 2})
    for row in node.forms:
        row.form.fields["title"].widget = Descendant()
        row.form.fields["title"].label = None
    assert node.compact_columns[0].label == "Title"
    assert node.compact_columns[0].widget_type is Descendant


@pytest.mark.django_db
@pytest.mark.parametrize(
    "kind",
    [
        "field_type",
        "widget_type",
        "descendant_type",
        "required",
        "label",
        "missing",
        "extra",
        "omitted_optional",
        "omitted_disabled",
        "effective_none",
        "empty_label",
        "blank_label",
        "column_missing",
        "secret",
        "id",
        "publisher",
        "ORDER",
        "DELETE",
    ],
)
def test_compact_marked_schema_retains_checks(kind):
    from django import forms
    from django.core.exceptions import ImproperlyConfigured

    from crud_views.lib.formsets import CompactColumn, CompactLayout, CompactWidgetCompatible

    class MarkedText(CompactWidgetCompatible, forms.TextInput):
        pass

    class OtherMarkedText(CompactWidgetCompatible, forms.TextInput):
        pass

    class Descendant(MarkedText):
        pass

    node = _runtime(factory_attrs={"extra": 2})
    for row in node.forms:
        row.form.fields["title"].widget = MarkedText()
    second = node.forms[1].form
    field = "title"
    if kind == "field_type":
        second.fields["title"] = forms.RegexField(".*", label="Title", widget=MarkedText)
    elif kind in ("widget_type", "descendant_type"):
        second.fields["title"].widget = (OtherMarkedText if kind == "widget_type" else Descendant)()
    elif kind == "required":
        second.fields["title"].required = False
    elif kind == "label":
        second.fields["title"].label = "Different"
    elif kind == "missing":
        del second.fields["title"]
    elif kind in ("extra", "omitted_optional", "omitted_disabled"):
        field = "other"
        second.fields[field] = forms.CharField(
            widget=MarkedText, required=kind == "omitted_disabled", disabled=kind in ("extra", "omitted_disabled")
        )
    elif kind in ("effective_none", "empty_label", "blank_label"):
        for row in node.forms:
            if kind == "effective_none":
                row.form["title"].label = None
            else:
                row.form.fields["title"].label = "" if kind == "empty_label" else " \t "
    else:
        field = "missing" if kind == "column_missing" else kind
        for row in node.forms:
            if field == "secret":

                class MarkedHidden(CompactWidgetCompatible, forms.HiddenInput):
                    pass

                row.form.fields[field] = forms.CharField(widget=MarkedHidden)
            elif field == "ORDER":
                row.form.fields[field] = forms.IntegerField(widget=MarkedText, required=False)
            elif field != "missing":
                original_widget = row.form.fields[field].widget
                marked = type("MarkedRole", (CompactWidgetCompatible, type(original_widget)), {})
                row.form.fields[field].widget = marked()
        node.formset.compact_layout = CompactLayout(
            [CompactColumn("title", span=6), CompactColumn(field, span=2)], controls_span=4
        )
    with pytest.raises(ImproperlyConfigured, match=rf"books.*{field}"):
        _ = node.compact_columns


@pytest.mark.django_db
@pytest.mark.parametrize("custom_template", [False, True])
def test_compact_marked_widgets_render_with_existing_helper(custom_template):
    from copy import deepcopy
    from pathlib import Path

    from django import forms
    from django.conf import settings
    from django.forms.renderers import TemplatesSetting
    from django.template.loader import render_to_string
    from django.test import override_settings

    from crud_views.lib.formsets import CompactWidgetCompatible
    from tests.test1.app.views_formset import BookFormSetForm

    class MarkedTextarea(CompactWidgetCompatible, forms.Textarea):
        pass

    class CustomInput(CompactWidgetCompatible, forms.TextInput):
        template_name = "marked_input.html"

    class MarkedBook(BookFormSetForm):
        title = forms.CharField(widget=CustomInput if custom_template else MarkedTextarea)

    original_templates = settings.TEMPLATES
    templates = deepcopy(original_templates)
    templates[0]["APP_DIRS"] = False
    templates[0]["DIRS"] = [*templates[0]["DIRS"], str(Path(forms.__file__).parent / "templates")]
    templates[0]["OPTIONS"]["loaders"] = [
        (
            "django.template.loaders.locmem.Loader",
            {
                "marked_input.html": (
                    '<span data-marked-template="yes">{% include "django/forms/widgets/text.html" %}</span>'
                )
            },
        ),
        "django.template.loaders.filesystem.Loader",
        "django.template.loaders.app_directories.Loader",
    ]
    with override_settings(TEMPLATES=templates):
        node = _runtime(form_class=MarkedBook, factory_attrs={"renderer": TemplatesSetting()})
        page = html.fromstring(render_to_string("crud_views/formsets/formset.html", {"x_formset": node}))
        bound = node.forms[0].form["title"]
        element = page.xpath("//*[@id=$id]", id=bound.auto_id)
        assert len(element) == 1 and element[0].get("name") == bound.html_name
        assert element[0].tag == ("input" if custom_template else "textarea")
        labels = page.xpath("//label[@for=$id]", id=bound.auto_id)
        assert len(labels) == 1 and "cv-formset-compact-label" in labels[0].get("class")
        assert bool(page.cssselect("[data-marked-template='yes']")) is custom_template
        assert page.cssselect(".cv-formset-compact-headings")
    assert settings.TEMPLATES is original_templates


@pytest.mark.django_db
@pytest.mark.parametrize("empty", [False, True])
@pytest.mark.parametrize("saved", [False, True])
def test_compact_marked_metadata_has_no_side_effects(monkeypatch, empty, saved):
    from django import forms
    from django.db import connection
    from django.forms.models import ModelChoiceIterator
    from django.test.utils import CaptureQueriesContext

    from crud_views.lib.formsets import CompactWidgetCompatible
    from tests.test1.app.views_formset import BookFormSetForm

    constructed = []
    widgets = []

    def forbidden(*args, **kwargs):
        pytest.fail("Metadata must not augment, validate, render or consult helpers")

    class MarkedSelect(CompactWidgetCompatible, forms.Select):
        render = forbidden
        create_option = forbidden

    class ChoiceBook(BookFormSetForm):
        title = forms.ModelChoiceField(queryset=Publisher.objects.all(), label="Publisher choice", widget=MarkedSelect)

        def __init__(self, *args, **kwargs):
            constructed.append(kwargs.copy())
            super().__init__(*args, **kwargs)
            field = self.fields["title"]
            assert isinstance(field.widget.choices, ModelChoiceIterator)
            assert field.widget.choices.field is field
            widgets.append(field.widget)

    parent = Publisher.objects.create(name="Choice") if saved else Publisher()
    identity = parent.pk
    original_iterator = ModelChoiceIterator.__iter__

    class ChoiceIteration(Exception):
        pass

    def forbidden_choices(self):
        raise ChoiceIteration("Actual field-bound choices were iterated")

    with monkeypatch.context() as patch:
        patch.setattr(ModelChoiceIterator, "__iter__", forbidden_choices)
        node = _runtime(form_class=ChoiceBook, parent=parent, factory_attrs={"extra": 0 if empty else 2})
        before = len(constructed)
        assert before == (0 if empty else 2)
        kwargs_calls = []
        original_kwargs = node.instance.get_form_kwargs

        def get_kwargs(index):
            kwargs_calls.append(index)
            return original_kwargs(index)

        patch.setattr(node.instance, "get_form_kwargs", get_kwargs)
        for method in ("add_fields", "_construct_form"):
            patch.setattr(node.instance, method, forbidden)
        patch.setattr(type(node.instance), "empty_form", property(forbidden))
        patch.setattr(type(node.instance), "helper", property(forbidden))
        for method in ("full_clean", "is_valid", "get_layout_fields"):
            patch.setattr(ChoiceBook, method, forbidden)
        patch.setattr(ChoiceBook, "helper", property(forbidden))
        with CaptureQueriesContext(connection) as queries:
            columns = node.compact_columns
            assert node.compact_columns is columns
        assert len(queries) == 0
        assert len(constructed) - before == int(empty)
        assert kwargs_calls == ([None] if empty else [])
        assert columns[0].label == "Publisher choice" and columns[0].widget_type is MarkedSelect
        assert parent.pk == identity
        assert len(widgets) == (1 if empty else 2)
        if empty:
            assert constructed[0]["cv_view"] is None
            assert constructed[0].get("instance") is not parent
            assert node.instance.total_form_count() == 0
        for widget in widgets:
            with pytest.raises(ChoiceIteration, match="Actual field-bound choices"):
                list(widget.choices)

    assert ModelChoiceIterator.__iter__ is original_iterator

    class RenderableSelect(CompactWidgetCompatible, forms.Select):
        pass

    class RenderableBook(BookFormSetForm):
        title = forms.ModelChoiceField(queryset=Publisher.objects.all(), widget=RenderableSelect)

    if not saved:
        Publisher.objects.create(name="Choice")
    normal = RenderableBook(cv_view=None)
    with CaptureQueriesContext(connection) as queries:
        rendered = str(normal["title"])
    assert "Choice" in rendered and len(queries) == 1


@pytest.mark.django_db
@pytest.mark.parametrize("name", ["missing", "secret", "id", "publisher", "ORDER", "DELETE"])
def test_compact_schema_rejects_hidden_identity_and_control_columns(name):
    from django import forms
    from django.core.exceptions import ImproperlyConfigured

    from crud_views.lib.formsets import CompactColumn, CompactLayout

    node = _runtime()
    node.forms[0].form.fields["secret"] = forms.CharField(widget=forms.HiddenInput)
    node.forms[0].form.fields["ORDER"] = forms.IntegerField(required=False)
    node.formset.compact_layout = CompactLayout(
        [CompactColumn("title", span=6), CompactColumn(name, span=2)], controls_span=4
    )
    with pytest.raises(ImproperlyConfigured, match=rf"books.*{name}"):
        _ = node.compact_columns


@pytest.mark.django_db
def test_compact_schema_rejects_polymorphic_even_with_uniform_first_row(monkeypatch):
    from django.core.exceptions import ImproperlyConfigured
    from polymorphic.formsets import BasePolymorphicInlineFormSet

    node = _runtime()
    monkeypatch.setattr(node.formset, "klass", BasePolymorphicInlineFormSet)
    with pytest.raises(ImproperlyConfigured, match=r"books.*polymorphic"):
        _ = node.compact_columns


@pytest.mark.django_db
@pytest.mark.parametrize("empty", [False, True])
def test_compact_metadata_model_choice_projection_has_no_queries(empty):
    from django import forms
    from django.db import connection
    from django.test.utils import CaptureQueriesContext

    from tests.test1.app.views_formset import BookFormSetForm

    constructed = []

    class ChoiceBook(BookFormSetForm):
        title = forms.ModelChoiceField(queryset=Publisher.objects.all(), label="Publisher choice")

        def __init__(self, *args, **kwargs):
            constructed.append(kwargs.copy())
            super().__init__(*args, **kwargs)

    Publisher.objects.create(name="Choice")
    node = _runtime(form_class=ChoiceBook, factory_attrs={"extra": 0 if empty else 2})
    before = len(constructed)
    with CaptureQueriesContext(connection) as queries:
        columns = node.compact_columns
        assert node.compact_columns is columns
    assert len(queries) == 0
    assert len(constructed) - before == int(empty)
    assert columns[0].label == "Publisher choice"
    widget_form = ChoiceBook(cv_view=None)
    with CaptureQueriesContext(connection) as widget_queries:
        rendered = str(widget_form["title"])
    assert "Choice" in rendered
    assert len(widget_queries) == 1


@pytest.mark.django_db
@pytest.mark.parametrize("saved", [False, True])
def test_compact_metadata_empty_uses_only_detached_constructor(monkeypatch, saved):
    from django.db import connection
    from django.test.utils import CaptureQueriesContext

    from tests.test1.app.views_formset import BookFormSetForm

    calls = []

    class MetadataBook(BookFormSetForm):
        def __init__(self, *args, **kwargs):
            calls.append(kwargs.copy())
            super().__init__(*args, **kwargs)
            self.fields["title"].label = "Request heading"

    parent = Publisher.objects.create(name="Saved") if saved else Publisher()
    identity = parent.pk
    node = _runtime(form_class=MetadataBook, parent=parent, factory_attrs={"extra": 0})
    assert not calls and not node.forms
    kwargs_calls = []
    original = node.instance.get_form_kwargs

    def kwargs_for(index):
        kwargs_calls.append(index)
        return original(index)

    def forbidden(*args, **kwargs):
        pytest.fail("Metadata must not augment, validate, render or consult helpers")

    monkeypatch.setattr(node.instance, "get_form_kwargs", kwargs_for)
    for method in ("add_fields", "_construct_form"):
        monkeypatch.setattr(node.instance, method, forbidden)
    monkeypatch.setattr(type(node.instance), "empty_form", property(forbidden))
    for method in ("full_clean", "is_valid", "get_layout_fields"):
        monkeypatch.setattr(MetadataBook, method, forbidden)
    with CaptureQueriesContext(connection) as queries:
        assert node.compact_columns[0].label == "Request heading"
        assert node.compact_columns[0].label == "Request heading"
    assert len(queries) == 0
    assert kwargs_calls == [None]
    assert len(calls) == 1 and calls[0]["cv_view"] is None
    assert calls[0].get("instance") is not parent
    assert parent.pk == identity
    assert node.instance.total_form_count() == 0


@pytest.mark.django_db
def test_compact_metadata_rejects_live_parent_instance():
    from django.core.exceptions import ImproperlyConfigured

    node = _runtime(factory_attrs={"extra": 0})
    node.instance.form_kwargs["instance"] = node.instance.instance
    with pytest.raises(ImproperlyConfigured, match=r"books.*parent"):
        _ = node.compact_columns


@pytest.mark.django_db
def test_compact_metadata_preserves_unsaved_uuid_parent():
    import uuid

    from django.db import connection, models
    from django.forms import inlineformset_factory
    from django.test.utils import CaptureQueriesContext, isolate_apps

    from crud_views.lib.crispy import CrispyModelForm
    from crud_views.lib.formsets import CompactColumn, CompactLayout, FormSet, InlineFormSet
    from crud_views.lib.formsets.render_tree import XFormSet

    with isolate_apps():

        class Parent(models.Model):
            id = models.UUIDField(primary_key=True, default=uuid.uuid4)

            class Meta:
                app_label = "compact_tests"

        class Child(models.Model):
            parent = models.ForeignKey(Parent, on_delete=models.CASCADE)
            title = models.CharField(max_length=100)

            class Meta:
                app_label = "compact_tests"

        class ChildForm(CrispyModelForm):
            class Meta:
                model = Child
                fields = ["title"]

        factory = inlineformset_factory(Parent, Child, form=ChildForm, formset=InlineFormSet, extra=0)
        declaration = FormSet(
            key="uuid-children",
            klass=factory,
            compact_layout=CompactLayout([CompactColumn("title", span=8)], controls_span=4),
        )
        parent = Parent()
        identity = parent.pk
        instance = factory(formset=declaration, instance=parent, queryset=Child.objects.none())
        assert not instance.forms
        node = XFormSet(
            level=0, prefix_key="None", formset=declaration, instance=instance, management_form=instance.management_form
        )
        with CaptureQueriesContext(connection) as queries:
            assert node.compact_columns[0].label == "Title"
        assert len(queries) == 0
        assert parent.pk == identity and parent._state.adding


@pytest.mark.django_db
@pytest.mark.parametrize("widget_name", ["TextInput", "NumberInput", "DateInput", "Select"])
def test_compact_schema_stock_widgets_preserve_attributes(widget_name):
    from django import forms
    from django.template.loader import render_to_string

    node = _runtime()
    widget = getattr(forms, widget_name)(attrs={"class": "small-owned-widget", "data-owned": "yes"})
    node.forms[0].form.fields["title"].widget = widget
    assert node.compact_columns[0].label == "Title"
    rendered = render_to_string("crud_views/formsets/formset.html", {"x_formset": node})
    document = html.fromstring(rendered)
    assert len(document.cssselect('[data-owned="yes"].small-owned-widget')) == 1


@pytest.mark.django_db
def test_compact_metadata_context_translation_and_fragment_uniformity():
    from django.test import RequestFactory
    from django.utils.translation import gettext, gettext_lazy, override

    from tests.test1.app.views_formset import BookFormSetForm, PublisherFormSetUpdateView

    class ContextBook(BookFormSetForm):
        def __init__(self, *args, **kwargs):
            view = kwargs["cv_view"]
            super().__init__(*args, **kwargs)
            self.fields["title"].label = f"{view.request.GET['label']} {gettext_lazy('Yes')}"

    labels = []
    for language, request_label in (("en", "First"), ("de", "Second")):
        view = PublisherFormSetUpdateView()
        view.request = RequestFactory().get("/", {"label": request_label})
        with override(language):
            initial = _runtime(form_class=ContextBook, cv_view=view)
            empty = _runtime(form_class=ContextBook, cv_view=view, factory_attrs={"extra": 0})
            fragment = next(initial.formset.template(pk=None, index=0, force_form_index=4))
            assert initial.compact_columns == empty.compact_columns == fragment.compact_columns
            labels.append(empty.compact_columns[0].label)
            assert labels[-1] == f"{request_label} {gettext('Yes')}"
    assert labels[0] != labels[1]
