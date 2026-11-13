"""Bounded native model-choice admission and authoritative conditional cleaning."""

import json
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch
from uuid import UUID

import pytest
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from crispy_forms.utils import render_crispy_form
from django import forms
from django.core.exceptions import ImproperlyConfigured
from django.db import connection, models
from django.forms.models import ModelChoiceIterator
from django.template import Context
from django.test.utils import CaptureQueriesContext, isolate_apps
from lxml import html

from crud_views.lib.conditional import ConditionalGroup, ConditionalGroupFormMixin, QuerysetConditions, ToggleGroup
from crud_views.lib.conditional.group import validate_value_groups
from crud_views.lib.conditional.toggle import ValueToggle
from tests.test1.app.models import Author, Profile, Publisher
from tests.test1.app.models import ConditionalPersistenceRecord as Record


def source(**kwargs):
    return QuerysetConditions("choice", conditional_key="category", keys=["active", "other"], **kwargs)


@pytest.mark.parametrize("key", [" A ", "a", 0, -1, UUID("12345678-1234-1234-1234-123456789abc")])
def test_category_scalar_bounds(key):
    conditions = QuerysetConditions("choice", conditional_key="category", keys=[key])
    assert conditions.keys == (str(key),)
    assert conditions.when(key).values == (str(key),)
    assert conditions.category_for(SimpleNamespace(category=key)) == str(key)


@pytest.mark.parametrize("key", [None, "", True, False, 1.5, Decimal("1"), b"a", [], {}, set(), object()])
def test_category_rejected_scalar_bounds(key):
    with pytest.raises(ImproperlyConfigured):
        QuerysetConditions("choice", conditional_key="category", keys=[key])


@pytest.mark.parametrize("keys", [[0, "0"], ["a", "a"], [UUID(int=1), str(UUID(int=1))], None, 1, "a"])
def test_category_rejects_ambiguous_keys(keys):
    with pytest.raises(ImproperlyConfigured):
        QuerysetConditions("choice", conditional_key="category", keys=keys)


@pytest.mark.parametrize("name", ["", "a__b", "a.b", "method()", "two names", None])
def test_category_requires_direct_attribute(name):
    with pytest.raises(ImproperlyConfigured):
        QuerysetConditions("choice", conditional_key=name, keys=["active"])


def test_membership_unknown_and_callable_category():
    with pytest.raises(ImproperlyConfigured, match="undeclared"):
        source().when("missing")
    obj = SimpleNamespace(category=lambda: pytest.fail("must not invoke category"))
    assert source(allow_unmatched=True).category_for(obj) is None


class LabelChoice(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f"Label: {obj.name}"


@pytest.mark.django_db
def test_label_only_subclass_is_native(django_assert_num_queries):
    field = LabelChoice(queryset=Publisher.objects.all())
    with django_assert_num_queries(0):
        source().when("active").validate_field(field)
    option = Publisher.objects.create(name="active")
    assert field.label_from_instance(option) == "Label: active"


@pytest.mark.django_db
@pytest.mark.parametrize(
    "mutation",
    [
        "multiple",
        "choices",
        "widget_choices",
        "iterator",
        "prepare_value",
        "to_python",
        "validate",
        "clean",
        "template",
        "option_template",
        "widget",
        "custom_widget",
        "choices_property",
    ],
)
def test_rejects_non_native_selection_without_queries(mutation, django_assert_num_queries):
    field = forms.ModelChoiceField(queryset=Publisher.objects.all())
    if mutation == "multiple":
        field = forms.ModelMultipleChoiceField(queryset=Publisher.objects.all())
    elif mutation == "choices":
        field.choices = [(1, "manual")]
    elif mutation == "widget_choices":
        field.widget.choices = [(1, "manual")]
    elif mutation == "iterator":
        field.iterator = type("CustomIterator", (ModelChoiceIterator,), {})
    elif mutation in ("prepare_value", "to_python", "validate", "clean"):
        setattr(field, mutation, lambda value: value)
    elif mutation in ("template", "option_template"):
        setattr(field.widget, mutation + "_name", "custom.html")
    elif mutation == "widget":
        field.widget = forms.SelectMultiple()
    elif mutation == "custom_widget":
        field.widget = type("CustomSelect", (forms.Select,), {})()
    else:
        field = type("CustomChoices", (forms.ModelChoiceField,), {"choices": property(lambda self: [])})(
            queryset=Publisher.objects.all()
        )
    with django_assert_num_queries(0), pytest.raises(ImproperlyConfigured, match="native"):
        source().when("active").validate_field(field)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "model,key,accepted",
    [
        (Publisher, None, True),
        (Author, None, True),
        (Record, "unique_text", True),
        (Record, "blank_text", False),
        (Record, "parent", False),
        (Record, "parent__name", False),
        (Record, "missing", False),
    ],
)
def test_native_identity_metadata(model, key, accepted, django_assert_num_queries):
    field = forms.ModelChoiceField(queryset=model.objects.all(), to_field_name=key)
    with django_assert_num_queries(0):
        if accepted:
            source().when("active").validate_field(field)
        else:
            with pytest.raises(ImproperlyConfigured, match=r"unique.*scalar"):
                source().when("active").validate_field(field)


@pytest.mark.parametrize("change", ["keys", "conditional_key", "allow_unmatched"])
@pytest.mark.parametrize("reverse", [False, True])
def test_sources_for_controller_must_agree(change, reverse):
    kwargs = {"conditional_key": "category", "keys": ["active", "other"], "allow_unmatched": False}
    kwargs[change] = {"keys": ["active"], "conditional_key": "different", "allow_unmatched": True}[change]
    groups = [
        ConditionalGroup(source().when("active"), ["one"]),
        ConditionalGroup(QuerysetConditions("choice", **kwargs).when("active"), ["two"]),
    ]
    with pytest.raises(ImproperlyConfigured, match=r"conflicting.*source"):
        validate_value_groups(groups[::-1] if reverse else groups, None)


@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("conflict", ["duplicate", "static_controller", "queryset_controller", "required"])
def test_mixed_ownership_is_order_independent(reverse, conflict):
    first = ConditionalGroup(source().when("active"), ["one"])
    second = ConditionalGroup(ValueToggle("kind", values=["a"]), ["two"])
    if conflict == "duplicate":
        second.fields = ["one"]
    elif conflict == "static_controller":
        first.fields = ["kind"]
    elif conflict == "queryset_controller":
        second.fields = ["choice"]
    else:
        first.required = ["two"]
    with pytest.raises(ImproperlyConfigured, match=r"conflicts|required fields"):
        validate_value_groups([second, first] if reverse else [first, second], None)


@pytest.mark.django_db
def test_equivalent_sources_and_missing_runtime_fields(django_assert_num_queries):
    groups = [ConditionalGroup(source().when("active"), ["one"]), ConditionalGroup(source().when("other"), ["two"])]
    with django_assert_num_queries(0):
        validate_value_groups(groups, {"choice": forms.ModelChoiceField(queryset=Publisher.objects.all())})

        class Broken(ConditionalGroupFormMixin, forms.Form):
            choice = forms.ModelChoiceField(queryset=Publisher.objects.all())
            cv_conditional_groups = groups

        with pytest.raises(ImproperlyConfigured, match="missing"):
            Broken(data={}).full_clean()


@pytest.mark.django_db
def test_unique_text_native_options_metadata_and_post():
    parent = Profile.objects.create(name="parent")
    options = [Record.objects.create(parent=parent, unique_text=key) for key in ("native-alpha", "native-beta")]
    conditions = source()

    class Form(ConditionalGroupFormMixin, forms.Form):
        choice = forms.ModelChoiceField(
            queryset=Record.objects.annotate(category=models.Value("active")), to_field_name="unique_text"
        )
        detail = forms.CharField()
        cv_conditional_groups = [ConditionalGroup(conditions.when("active"), ["detail"])]

    form = Form()
    helper = FormHelper()
    helper.form_action = ""
    helper.disable_csrf = True
    helper.layout = Layout("choice", ToggleGroup(conditions.when("active"), "detail"))
    doc = html.fromstring(render_crispy_form(form, helper=helper))
    native = [node.get("value") for node in doc.cssselect("option") if node.get("value")]
    assert native == [str(form.fields["choice"].prepare_value(obj)) for obj in options]
    assert json.loads(doc.cssselect("[cv-data-toggle-group]")[0].get("cv-data-toggle-values")) == native
    for option, token in zip(options, native, strict=False):
        bound = Form(data={"choice": token, "detail": "kept"})
        assert bound.is_valid(), bound.errors
        assert bound.cleaned_data["choice"] == option


@pytest.mark.django_db
@pytest.mark.parametrize("mode", ["none", "replacement", "removed", "invalid", "disabled"])
def test_final_inherited_mapping_controls_activation(mode):
    option = Publisher.objects.create(name="active")

    class Parent(forms.Form):
        choice = forms.ModelChoiceField(queryset=Publisher.objects.annotate(category=models.F("name")))
        detail = forms.CharField()

        def clean(self):
            cleaned = super().clean()
            if mode == "none":
                return None
            if mode == "replacement":
                return {**cleaned, "detail": "replacement"}
            if mode == "removed":
                return {"detail": "must clear"}
            return cleaned

    class Form(ConditionalGroupFormMixin, Parent):
        cv_conditional_groups = [ConditionalGroup(source().when("active"), ["detail"])]

    form = Form(
        data={"choice": "999999" if mode in ("invalid", "disabled") else str(option.pk), "detail": "kept"},
        initial={"choice": option.pk},
    )
    form.fields["choice"].disabled = mode == "disabled"
    assert form.is_valid() is (mode != "invalid")
    assert form.cleaned_data["detail"] == {"replacement": "replacement", "removed": "", "invalid": ""}.get(mode, "kept")
    if mode == "invalid":
        assert form.errors.as_data()["choice"][0].code == "invalid_choice"


@pytest.mark.django_db
@pytest.mark.parametrize("scenario", ["changed", "restricted", "stale", "forged", "blank", "required"])
def test_post_uses_current_queryset_and_category(scenario):
    from tests.test1.test_conditional_queryset import record_form, source_for

    option = Publisher.objects.create(name="active")
    klass = record_form(source_for())
    render_crispy_form(klass())
    if scenario == "changed":
        Publisher.objects.filter(pk=option.pk).update(name="general")
    if scenario == "stale":
        option.delete()
    value = "" if scenario in ("blank", "required") else str(option.pk)
    form = klass(data={"reference": "999999" if scenario == "forged" else value, "blank_text": "discard"})
    if scenario == "restricted":
        form.fields["reference"].queryset = form.fields["reference"].queryset.none()
    form.fields["reference"].required = scenario == "required"
    assert form.is_valid() is (scenario in ("changed", "blank"))
    assert form.cleaned_data["blank_text"] == ""
    if scenario not in ("changed", "blank"):
        assert form.errors.as_data()["reference"][0].code == (
            "required" if scenario == "required" else "invalid_choice"
        )


@pytest.mark.django_db
@pytest.mark.parametrize("category", ["active", "other", "unknown"])
@pytest.mark.parametrize("empty", [False, None, "", [], 0])
def test_shared_membership_explicit_empty_and_independent_source(category, empty):
    option = Publisher.objects.create(name=category)
    conditions = source(allow_unmatched=True)
    strict = QuerysetConditions("second", conditional_key="category", keys=["active"])

    class Form(ConditionalGroupFormMixin, forms.Form):
        choice = forms.ModelChoiceField(queryset=Publisher.objects.annotate(category=models.F("name")))
        second = forms.ModelChoiceField(queryset=Publisher.objects.annotate(category=models.Value("active")))
        detail = forms.JSONField()
        protected = forms.CharField(disabled=True, initial="trusted")
        independent = forms.CharField()
        cv_conditional_groups = [
            ConditionalGroup(
                conditions.when("active", "other"), ["detail", "protected"], empty_values={"detail": empty}
            ),
            ConditionalGroup(strict.when("active"), ["independent"]),
        ]

    form = Form(
        data={
            "choice": str(option.pk),
            "second": str(option.pk),
            "detail": '"kept"' if category != "unknown" else "invalid json",
            "protected": "forged",
            "independent": "kept",
        }
    )
    assert form.is_valid(), form.errors
    assert form.cleaned_data["detail"] == (empty if category == "unknown" else "kept")
    assert form.cleaned_data["protected"] == "trusted"
    assert form.cleaned_data["independent"] == "kept"


@pytest.mark.django_db
@pytest.mark.parametrize("options", [2, 20])
@pytest.mark.parametrize("rows", [1, 20])
def test_render_query_budget_options_and_rows(options, rows):
    from tests.test1.test_conditional_queryset import record_form, source_for

    Publisher.objects.bulk_create([Publisher(name="active" if index % 2 else "other") for index in range(options)])
    conditions = source_for()
    from django.forms.models import inlineformset_factory

    from crud_views.lib.formsets import FormSet, InlineFormSet

    factory = inlineformset_factory(Profile, Record, form=record_form(conditions), formset=InlineFormSet, extra=rows)
    formset = factory(instance=Profile(), formset=FormSet(title="Rows", klass=factory), prefix="records")
    forms_to_render = formset.forms
    with CaptureQueriesContext(connection) as baseline:
        for form in forms_to_render:
            str(form["reference"])
    labels = []
    original = forms.ModelChoiceField.label_from_instance

    def label(field, obj):
        labels.append(obj.pk)
        return original(field, obj)

    with patch.object(forms.ModelChoiceField, "label_from_instance", label), CaptureQueriesContext(connection) as total:
        for form in forms_to_render:
            context = Context()
            str(form["reference"])
            for _ in range(2):
                ToggleGroup(conditions.when("active")).render(form, context)
                ToggleGroup(conditions.when("other")).render(form, context)
    assert len(baseline) == rows
    assert len(total) == rows * 2
    assert len(labels) == rows * options


@pytest.mark.django_db
def test_post_category_property_cost_is_application_owned(monkeypatch, django_assert_num_queries):
    calls = []

    def category(obj):
        calls.append(obj.pk)
        return obj.name

    monkeypatch.setattr(Publisher, "category", property(category), raising=False)
    option = Publisher.objects.create(name="active")
    conditions = source()

    class Form(ConditionalGroupFormMixin, forms.Form):
        choice = forms.ModelChoiceField(queryset=Publisher.objects.all())
        one = forms.CharField()
        two = forms.CharField()
        cv_conditional_groups = [
            ConditionalGroup(conditions.when("active"), ["one"]),
            ConditionalGroup(source().when("other"), ["two"]),
        ]

    with django_assert_num_queries(1):
        form = Form(data={"choice": str(option.pk), "one": "kept", "two": "discard"})
        assert form.is_valid(), form.errors
    assert calls == [option.pk]
    calls.clear()
    with django_assert_num_queries(1):
        context = Context()
        ToggleGroup(conditions.when("active")).render(form, context)
        ToggleGroup(source().when("other")).render(form, context)
    assert calls == [option.pk]


@isolate_apps()
@pytest.mark.parametrize(
    "kind,accepted",
    [
        (models.CharField, True),
        (models.TextField, True),
        (models.IntegerField, True),
        (models.UUIDField, True),
        (models.FloatField, False),
        (models.BooleanField, False),
        (models.DecimalField, False),
        (models.JSONField, False),
    ],
)
def test_native_pk_families_from_metadata(kind, accepted):
    class Option(models.Model):
        id = kind(primary_key=True)

        class Meta:
            app_label = "queryset_contract"

    field = forms.ModelChoiceField(queryset=Option.objects.all())
    if accepted:
        source().when("active").validate_field(field)
    else:
        with pytest.raises(ImproperlyConfigured, match="scalar"):
            source().when("active").validate_field(field)


@isolate_apps()
def test_composite_identity_is_rejected_when_supported():
    if not hasattr(models, "CompositePrimaryKey"):
        return  # Django 4.2 has no composite model metadata to admit.

    class Option(models.Model):
        first = models.IntegerField()
        second = models.IntegerField()
        pk = models.CompositePrimaryKey("first", "second")

        class Meta:
            app_label = "queryset_contract"

    with pytest.raises(ImproperlyConfigured, match="scalar"):
        source().when("active").validate_field(forms.ModelChoiceField(queryset=Option.objects.all()))
