"""Queryset conditions stay row-owned in the compact rendering path."""

import json

import pytest
from crispy_forms.utils import render_crispy_form
from django import forms
from django.core.exceptions import ImproperlyConfigured
from django.db import connection
from django.forms.models import inlineformset_factory
from django.template.loader import render_to_string
from django.test import RequestFactory
from django.test.utils import CaptureQueriesContext
from lxml import html

from crud_views.lib.formsets import CompactColumn, CompactLayout, FormSet, FormSets, InlineFormSet
from crud_views.lib.formsets.compact import _compact_helper, _compact_projection, _compact_schema
from tests.test1.app.models import ConditionalPersistenceRecord as Record
from tests.test1.app.models import Profile, Publisher
from tests.test1.test_conditional_queryset import guard_form, record_form, source_for

pytestmark = pytest.mark.django_db


def compact_tree(*, source=None, guard_only=False, extra=2, data=None, parent=None):
    klass = (guard_form if guard_only else record_form)(source or source_for())
    factory = inlineformset_factory(Profile, Record, form=klass, formset=InlineFormSet, extra=extra)
    declaration = FormSet(
        title="Records",
        klass=factory,
        compact_layout=CompactLayout([CompactColumn(name, span=3) for name in klass.Meta.fields], controls_span=3),
    )
    trees = FormSets(formsets={"records": declaration})
    request = RequestFactory().get("/") if data is None else RequestFactory().post("/", data)
    trees.init(request, forms.modelform_factory(Profile, fields=[])(instance=parent or Profile(name="parent")))
    return trees, trees.x_formsets[0]


def render(node):
    return html.fromstring(render_to_string("crud_views/formsets/formset.html", {"x_formset": node}))


def test_compact_queryset_cells_keep_geometry_and_row_ownership(django_assert_num_queries):
    active = Publisher.objects.create(name="active")
    other = Publisher.objects.create(name="other")
    _, node = compact_tree()
    first, second = [row.form for row in node.forms]
    first.initial["reference"] = active.pk
    second.initial["reference"] = other.pk
    first.fields["reference"].queryset = first.fields["reference"].queryset.filter(pk=active.pk)
    first.fields["blank_text"].help_text = "<script>plain help</script>"
    with django_assert_num_queries(0):
        _compact_schema(first, node.formset)
        _compact_projection(node)
        _compact_helper(node.forms[0])
    doc = render(node)
    rows = doc.cssselect(".cv-formset-row-compact")
    for index, row in enumerate(rows):
        cells = row.cssselect(".cv-formset-compact-fields > div")
        assert len(cells) == 4
        assert all("col-md-3" in cell.get("class") for cell in cells)
        controlled = row.cssselect("[cv-data-toggle-group]")
        assert len(controlled) == 2
        form = [first, second][index]
        for cell in controlled:
            assert cell.get("cv-data-toggle-field") == form.add_prefix("reference")
            assert cell.get("cv-data-toggle-kind") == "queryset"
            assert "cv-data-toggle-disable-only" in cell.attrib
            assert cell.getparent().get("class").endswith("cv-formset-compact-fields")
            assert len(cell.cssselect("label")) == 1
            assert not cell.cssselect('input[type="hidden"]')
        assert json.loads(controlled[0].get("cv-data-toggle-values")) == [str(active.pk)]
        assert json.loads(controlled[1].get("cv-data-toggle-values")) == ([] if index == 0 else [str(other.pk)])
        assert row.cssselect("select option[selected]")[0].get("value") == str([active, other][index].pk)
        for hidden in row.cssselect('input[type="hidden"]'):
            assert not hidden.xpath("ancestor::*[@cv-data-toggle-group]")
    assert not rows[0].cssselect("script")
    assert "<script>plain help</script>" in rows[0].text_content()


@pytest.mark.parametrize("guard_only", [False, True])
def test_compact_no_fields_render_coverage(guard_only, django_assert_num_queries):
    Publisher.objects.create(name="general")
    _, node = compact_tree(guard_only=guard_only)
    with django_assert_num_queries(0):
        for row in node.forms:
            _compact_schema(row.form, node.formset)
            _compact_helper(row)
        _compact_projection(node)
    doc = render(node)
    assert len(doc.cssselect("select")) == 2
    assert not doc.cssselect(".cv-queryset-condition-error")
    if guard_only:
        assert not doc.cssselect("[cv-data-toggle-group]")
    else:
        assert all(
            json.loads(cell.get("cv-data-toggle-values")) == [] for cell in doc.cssselect("[cv-data-toggle-group]")
        )
    Publisher.objects.create(name="unknown<script>")
    with pytest.raises(ImproperlyConfigured, match=r"reference.*unknown"):
        render(node)
    _, permissive = compact_tree(guard_only=guard_only, source=source_for(allow_unmatched=True))
    assert not render(permissive).cssselect(".cv-queryset-condition-error")
    # A rejected sibling keeps the whole redisplay bound, even for an empty row.
    _, node = compact_tree(guard_only=guard_only)
    for row in node.forms:
        row.form.is_bound = True
        row.form.data = {}
    node.forms[0].form.add_error(None, "Unrelated row failure")
    doc = render(node)
    diagnostics = doc.cssselect(".cv-queryset-condition-error")
    assert diagnostics
    assert all(not error.xpath("ancestor::*[@cv-data-toggle-group]") for error in diagnostics)
    assert any(not error.xpath('ancestor::*[contains(@class, "cv-formset-compact-fields")]') for error in diagnostics)
    assert "Unrelated row failure" in doc.text_content()
    assert "unknown<script>" in doc.text_content()
    assert not doc.cssselect("script")


def test_empty_compact_queryset_schema_does_not_evaluate_options(django_assert_num_queries):
    Publisher.objects.create(name="unknown")
    _, node = compact_tree(guard_only=True, extra=0)
    with django_assert_num_queries(0):
        assert len(_compact_projection(node)) == 1
        assert node.forms == []
        assert "cv-queryset-condition-error" not in render_to_string(
            "crud_views/formsets/formset.html", {"x_formset": node}
        )


@pytest.mark.parametrize("rows,options", [(1, 2), (20, 2), (1, 20), (20, 20)])
@pytest.mark.parametrize("guard_only", [False, True])
def test_compact_projection_query_budget(rows, options, guard_only):
    Publisher.objects.bulk_create([Publisher(name="active") for _ in range(options)])
    _, node = compact_tree(guard_only=guard_only, extra=rows)
    native = []
    conditional = []
    for row in node.forms:
        # Compare identical native controller rendering, without condition registration.
        form = row.form
        helper = _compact_helper(row)
        groups = form.cv_conditional_groups
        form.cv_conditional_groups = []
        baseline_helper = _compact_helper(row)
        form.cv_conditional_groups = groups
        with CaptureQueriesContext(connection) as queries:
            render_crispy_form(form, helper=baseline_helper)
        native.extend(queries.captured_queries)
        with CaptureQueriesContext(connection) as queries:
            render_crispy_form(form, helper=helper)
        conditional.extend(queries.captured_queries)
    assert len(native) == rows
    assert len(conditional) == rows * 2


def test_compact_bound_cell_preserves_field_errors_and_labels():
    active = Publisher.objects.create(name="active")
    _, node = compact_tree(extra=1)
    form = node.forms[0].form
    form.is_bound = True
    form.data = {form.add_prefix("reference"): str(active.pk), form.add_prefix("blank_text"): ""}
    form.add_error(None, "Row error")
    doc = render(node)
    cell = doc.cssselect("[cv-data-toggle-group]")[0]
    assert "This field is required" in cell.text_content()
    assert "Row error" in doc.text_content()
    assert cell.cssselect("label")[0].get("for") == form["blank_text"].id_for_label
