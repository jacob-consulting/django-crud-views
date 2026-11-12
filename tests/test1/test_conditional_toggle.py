import pytest
from django import forms
from django.core.exceptions import ImproperlyConfigured
from django.db import models

from crud_views.lib.conditional.group import ConditionalGroup, ConditionalGroupFormMixin
from crud_views.lib.conditional.toggle import ModelFieldToggle, UIFieldToggle, ValueToggle


class _ToggleForm(forms.Form):
    flag = forms.BooleanField(required=False)


def test_is_on_reads_cleaned_data_true():
    form = _ToggleForm(data={"flag": "on"})
    assert form.is_valid()
    assert ModelFieldToggle("flag").is_on(form) is True


def test_is_on_reads_cleaned_data_false_when_absent():
    form = _ToggleForm(data={})
    assert form.is_valid()
    assert ModelFieldToggle("flag").is_on(form) is False


def test_is_on_falls_back_to_raw_data_before_clean():
    form = _ToggleForm(data={"flag": "on"})  # not yet validated
    assert UIFieldToggle("flag").is_on(form) is True


def test_is_on_raw_data_falsey_strings():
    form = _ToggleForm(data={"flag": "false"})
    assert ModelFieldToggle("flag").is_on(form) is False


def test_ui_field_toggle_is_injectable():
    assert UIFieldToggle("flag").inject is True
    assert ModelFieldToggle("flag").inject is False


@pytest.mark.parametrize("values", [[], "one", None, 1, [None], [""], [True], [1.5], [object()], [0, "0"], ["a", "a"]])
def test_value_toggle_contract_rejects_invalid_matches(values):
    with pytest.raises(ImproperlyConfigured, match="ValueToggle"):
        ValueToggle("kind", values=values)


@pytest.mark.parametrize("value", ["a", " a ", 'a"<>[]', 0, 1, -1])
@pytest.mark.parametrize("widget", [forms.Select, forms.RadioSelect])
def test_value_toggle_contract(value, widget):
    values = [value]
    toggle = ValueToggle("kind", values=values)
    values.append("later")
    assert toggle.values == (str(value),)
    assert not toggle.inject
    assert toggle.field_name() == "kind"

    class ChoiceForm(forms.Form):
        kind = forms.ChoiceField(choices=[("Group", [(value, "Match"), ("other", "Other")])], widget=widget)

    initial = ChoiceForm(initial={"kind": value}, prefix="rows-0")
    assert toggle.is_on(initial)
    assert initial._errors is None and not hasattr(initial, "cleaned_data")
    bound = ChoiceForm(data={"rows-0-kind": str(value)}, prefix="rows-0")
    assert toggle.is_on(bound)
    assert bound._errors is None
    assert bound.is_valid()
    assert toggle.is_on(bound)


@pytest.mark.parametrize("widget", [forms.Select, forms.RadioSelect])
@pytest.mark.parametrize("value", [0, 1])
def test_value_toggle_native_integer_blank_option(widget, value):
    native = models.IntegerField(choices=[(0, "Zero"), (1, "One")], null=True, blank=True)

    class ChoiceForm(forms.Form):
        kind = native.formfield(widget=widget)

    toggle = ValueToggle("kind", values=[value])
    assert list(ChoiceForm.base_fields["kind"].choices)[0][0] == ""
    toggle.validate_field(ChoiceForm.base_fields["kind"], native)
    empty = ChoiceForm(data={"kind": ""})
    assert not toggle.is_on(empty)
    assert empty.is_valid() and empty.cleaned_data["kind"] is None
    assert not toggle.is_on(empty)
    filled = ChoiceForm(data={"kind": str(value)})
    assert filled.is_valid() and filled.cleaned_data["kind"] == value
    assert toggle.is_on(filled)
    for invalid in ("", None):
        with pytest.raises(ImproperlyConfigured):
            ValueToggle("kind", values=[invalid])


@pytest.mark.parametrize("native", [models.CharField, models.TextField, models.IntegerField])
def test_value_toggle_native_model_coercion(native):
    value = 1 if native is models.IntegerField else "a"
    field = native(choices=[(value, "Match")], blank=True).formfield()
    ValueToggle("kind", values=[value]).validate_field(field)


@pytest.mark.parametrize("coerce", [str, int])
def test_value_toggle_builtin_coercion(coerce):
    field = forms.TypedChoiceField(choices=[(0, "Zero"), (1, "One")], coerce=coerce)
    ValueToggle("kind", values=[0, 1]).validate_field(field)


@pytest.mark.parametrize(
    "field",
    [
        forms.ChoiceField(choices=[("a", "A")]),
        forms.TypedChoiceField(choices=[("01", "One")], coerce=int),
        forms.TypedChoiceField(choices=[("a", "A")], coerce=lambda value: value),
        forms.MultipleChoiceField(choices=[("1", "One")]),
        forms.ChoiceField(choices=[("1", "One")], widget=forms.SelectMultiple),
        forms.ChoiceField(choices=[("1", "One")], widget=type("CustomSelect", (forms.Select,), {})),
        type("CustomChoice", (forms.ChoiceField,), {})(choices=[("1", "One")]),
        forms.ChoiceField(choices=[(True, "True")]),
        forms.ChoiceField(choices=[(1.5, "Float")]),
        forms.ChoiceField(choices=[(1, "One"), ("1", "Duplicate")]),
    ],
)
def test_value_toggle_rejects_unsupported_field(field):
    with pytest.raises(ImproperlyConfigured, match="ValueToggle"):
        ValueToggle("kind", values=[1]).validate_field(field)


@pytest.mark.django_db
def test_value_toggle_rejects_relation_without_query(django_assert_num_queries):
    from tests.test1.app.models import Profile

    field = forms.ModelChoiceField(queryset=Profile.objects.none())
    with django_assert_num_queries(0), pytest.raises(ImproperlyConfigured, match="standard ChoiceField"):
        ValueToggle("kind", values=[1]).validate_field(field)


@pytest.mark.parametrize("data", [{}, {"kind": ""}, {"kind": "invalid"}])
def test_value_toggle_cleaned_authority(data):
    class ChoiceForm(ConditionalGroupFormMixin, forms.Form):
        kind = forms.ChoiceField(choices=[("a", "A"), ("b", "B")])
        detail = forms.CharField()
        cv_conditional_groups = [ConditionalGroup(ValueToggle("kind", values=["a"]), ["detail"])]

    form = ChoiceForm(data={**data, "detail": "forged"})
    assert not form.is_valid()
    assert form.errors.as_data()["kind"][0].code == ("invalid_choice" if data.get("kind") else "required")
    assert form.cleaned_data["detail"] == ""
    assert not form.cv_conditional_groups[0].is_on(form)
    # Cleaning removed the key; even a subsequently forged matching raw value is irrelevant.
    form.data = {"kind": "a"}
    assert not form.cv_conditional_groups[0].is_on(form)


def test_value_toggle_parent_clean_removes_controller():
    class Parent(forms.Form):
        kind = forms.ChoiceField(choices=[("a", "A")])
        detail = forms.CharField()

        def clean(self):
            cleaned = super().clean()
            cleaned.pop("kind")
            return cleaned

    class Child(ConditionalGroupFormMixin, Parent):
        cv_conditional_groups = [ConditionalGroup(ValueToggle("kind", values=["a"]), ["detail"])]

    form = Child(data={"kind": "a", "detail": "forged"})
    assert form.is_valid()
    assert form.cleaned_data == {"detail": ""}


@pytest.mark.parametrize("initial,expected", [("a", True), ("b", False)])
def test_value_toggle_disabled_controller(initial, expected):
    class ChoiceForm(forms.Form):
        kind = forms.ChoiceField(choices=[("a", "A"), ("b", "B")], disabled=True)

    form = ChoiceForm(data={"kind": "b" if initial == "a" else "a"}, initial={"kind": initial})
    toggle = ValueToggle("kind", values=["a"])
    assert toggle.is_on(form) is expected
    assert form.is_valid() and form.cleaned_data["kind"] == initial
    assert toggle.is_on(form) is expected


def test_value_toggle_missing_field_is_configuration_error():
    with pytest.raises(ImproperlyConfigured, match="missing"):
        ValueToggle("absent", values=["a"]).is_on(forms.Form())


def test_value_toggle_rejects_noncanonical_native_integer_key():
    field = models.IntegerField(choices=[("invalid", "Invalid")]).formfield()
    with pytest.raises(ImproperlyConfigured, match="canonical"):
        ValueToggle("kind", values=["invalid"]).validate_field(field)


def test_value_toggle_rejects_empty_value_colliding_with_match():
    field = forms.TypedChoiceField(choices=[(0, "Zero"), (1, "One")], coerce=int, empty_value=0, required=False)
    with pytest.raises(ImproperlyConfigured, match="empty"):
        ValueToggle("kind", values=[0]).validate_field(field)
