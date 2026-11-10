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
