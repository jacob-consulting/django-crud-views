"""Bounded native model-choice admission and authoritative conditional cleaning."""

import json
from decimal import Decimal
from types import SimpleNamespace
from uuid import UUID

import pytest
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from crispy_forms.utils import render_crispy_form
from django import forms
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.forms.models import ModelChoiceIterator
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
