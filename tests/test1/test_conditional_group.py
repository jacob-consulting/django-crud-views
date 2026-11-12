# tests/test1/test_conditional_group.py
import pytest
from django import forms
from django.core.exceptions import ImproperlyConfigured

from crud_views.lib.conditional.group import ConditionalGroup, ConditionalGroupFormMixin
from crud_views.lib.conditional.toggle import ModelFieldToggle, UIFieldToggle, ValueToggle
from tests.test1.app.models import Profile

pytestmark = pytest.mark.django_db


class ContactForm(ConditionalGroupFormMixin, forms.ModelForm):
    cv_conditional_groups = [
        ConditionalGroup(
            toggle=ModelFieldToggle("with_contact"),
            fields=["email", "phone"],
            required=["email"],
        ),
    ]

    class Meta:
        model = Profile
        fields = ["name", "with_contact", "email", "phone"]


def test_required_enforced_when_toggle_on():
    form = ContactForm(data={"name": "a", "with_contact": "on", "email": "", "phone": ""})
    assert form.is_valid() is False
    assert "email" in form.errors
    assert "phone" not in form.errors  # phone is not in required list


def test_valid_when_toggle_on_and_required_present():
    form = ContactForm(data={"name": "a", "with_contact": "on", "email": "x@y.z", "phone": ""})
    assert form.is_valid() is True


def test_skips_required_when_toggle_off():
    form = ContactForm(data={"name": "a", "email": "", "phone": ""})  # with_contact absent => off
    assert form.is_valid() is True
    assert form.cleaned_data["email"] is None


def test_clears_smuggled_values_when_toggle_off():
    # Tampering / JS-failure: toggle off but values present => server wipes them.
    form = ContactForm(data={"name": "a", "email": "x@y.z", "phone": "123"})
    assert form.is_valid() is True
    assert form.cleaned_data["email"] is None
    assert form.cleaned_data["phone"] is None


def test_clean_skips_fields_not_on_form():
    """group.clean() must not raise KeyError when a group field is absent from Meta.fields."""

    class PartialContactForm(ConditionalGroupFormMixin, forms.ModelForm):
        cv_conditional_groups = [
            ConditionalGroup(
                toggle=ModelFieldToggle("with_contact"),
                fields=["email", "phone"],  # phone is NOT in Meta.fields
                required=["email", "phone"],
            ),
        ]

        class Meta:
            model = Profile
            fields = ["name", "with_contact", "email"]  # phone excluded

    # Toggle ON — missing required field (phone) should be silently skipped
    form_on = PartialContactForm(data={"name": "a", "with_contact": "on", "email": "x@y.z"})
    assert form_on.is_valid() is True  # no KeyError; phone guard skipped

    # Toggle OFF — clearing phone should also be silently skipped
    form_off = PartialContactForm(data={"name": "a", "email": "x@y.z"})
    assert form_off.is_valid() is True  # no KeyError; email cleared, phone skipped
    assert form_off.cleaned_data["email"] is None


def test_off_group_suppresses_field_level_errors():
    """Off means off: even a field-level error (max_length) on an off-group field
    must not block the form — the value is discarded anyway."""
    form = ContactForm(data={"name": "a", "email": "x" * 150})  # toggle off, email over max_length=100
    assert form.is_valid() is True
    assert form.cleaned_data["email"] is None


def test_on_group_field_error_is_not_doubled_with_required():
    """A field failing its own validation while the toggle is on must not get an
    additional contradictory 'required' error piled on top."""
    form = ContactForm(data={"name": "a", "with_contact": "on", "email": "x" * 150})
    assert form.is_valid() is False
    assert len(form.errors["email"]) == 1, form.errors["email"]


def test_ui_field_toggle_is_injected_and_not_a_model_field():
    class UIForm(ConditionalGroupFormMixin, forms.ModelForm):
        cv_conditional_groups = [
            ConditionalGroup(toggle=UIFieldToggle("has_contact"), fields=["email"]),
        ]

        class Meta:
            model = Profile
            fields = ["name", "email"]

    form = UIForm(data={"name": "a"})
    assert "has_contact" in form.fields
    assert form.fields["email"].required is False
    assert form.is_valid() is True
    assert form.cleaned_data["email"] is None


@pytest.mark.parametrize("active", [False, True])
@pytest.mark.parametrize(
    "field_factory",
    [
        lambda: forms.TypedChoiceField(choices=[("1", "One")], coerce=int),
        lambda: forms.SplitDateTimeField(),
        lambda: forms.JSONField(),
    ],
    ids=["typed-choice", "multi-value", "json"],
)
def test_request_added_unsupported_field_is_configuration_error_even_when_active(active, field_factory):
    class Dynamic(ConditionalGroupFormMixin, forms.Form):
        active = forms.BooleanField(required=False)
        cv_conditional_groups = [ConditionalGroup(ModelFieldToggle("active"), ["dynamic"])]

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields["dynamic"] = field_factory()

    assert "dynamic" not in Dynamic.base_fields
    form = Dynamic(data={"active": "on"} if active else {})
    with pytest.raises(ImproperlyConfigured, match=r"active.*dynamic.*empty_values"):
        form.is_valid()


@pytest.mark.parametrize("empty", [False, None, "", []])
def test_plain_form_custom_field_accepts_explicit_native_falsy_values(empty):
    class Custom(forms.Field):
        pass

    class Plain(ConditionalGroupFormMixin, forms.Form):
        value = Custom()
        cv_conditional_groups = [ConditionalGroup(UIFieldToggle("enabled"), ["value"], empty_values={"value": empty})]

    form = Plain(data={"value": "forged"})
    assert form.is_valid(), form.errors
    assert form.cleaned_data["value"] is empty


@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("kind", ["consumer", "wholesale", "distributor"])
def test_value_groups_disjoint(kind, reverse):
    matrix = {
        "preferences": ["consumer"],
        "business": ["wholesale", "distributor"],
        "terms": ["wholesale"],
        "distribution": ["distributor"],
    }

    class Multi(ConditionalGroupFormMixin, forms.Form):
        kind = forms.ChoiceField(choices=[(value, value) for value in ("consumer", "wholesale", "distributor")])
        preferences = forms.CharField()
        business = forms.CharField()
        terms = forms.CharField()
        distribution = forms.CharField()
        outside = forms.CharField()
        cv_conditional_groups = [
            ConditionalGroup(ValueToggle("kind", values), [name]) for name, values in matrix.items()
        ]

    if reverse:
        Multi.cv_conditional_groups.reverse()
    form = Multi(data={"kind": kind, "outside": "unchanged", **dict.fromkeys(matrix, "provided")})
    assert form.is_valid(), form.errors
    assert form.cleaned_data == {
        "kind": kind,
        "outside": "unchanged",
        **{name: "provided" if kind in values else "" for name, values in matrix.items()},
    }


@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("conflict", ["overlap", "value-controller", "checkbox-controller", "self", "required"])
def test_value_group_conflicts(conflict, reverse):
    value = ConditionalGroup(ValueToggle("kind", ["a"]), ["detail"])
    checkbox = ConditionalGroup(UIFieldToggle("enabled"), ["other"])
    if conflict == "overlap":
        checkbox.fields = ["detail"]
    elif conflict == "value-controller":
        checkbox.fields = ["kind"]
        checkbox.empty_values = {"kind": "b"}
    elif conflict == "checkbox-controller":
        value.fields = ["enabled"]
    elif conflict == "self":
        value.fields = ["kind"]
        value.empty_values = {"kind": "b"}
    else:
        value.required = ["other"]

    class Invalid(ConditionalGroupFormMixin, forms.Form):
        kind = forms.ChoiceField(choices=[("a", "A"), ("b", "B")])
        detail = forms.CharField()
        other = forms.CharField()
        cv_conditional_groups = [value, checkbox][:: -1 if reverse else 1]

    with pytest.raises(ImproperlyConfigured, match=r"ValueToggle.*kind"):
        Invalid(data={"kind": "invalid", "detail": "forged"})
    # Class fields were not disarmed while attempting construction.
    assert Invalid.base_fields["detail"].required


@pytest.mark.parametrize("missing", ["kind", "detail"])
def test_value_group_runtime_fields_missing(missing):
    class Dynamic(ConditionalGroupFormMixin, forms.Form):
        kind = forms.ChoiceField(choices=[("a", "A")])
        detail = forms.CharField()
        cv_conditional_groups = [ConditionalGroup(ValueToggle("kind", ["a"]), ["detail"])]

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            del self.fields[missing]

    with pytest.raises(ImproperlyConfigured, match=missing):
        Dynamic(data={"kind": "a"}).is_valid()


@pytest.mark.parametrize("kind", ["a", "b", "invalid"])
def test_value_group_runtime_fields_added_and_optional(kind):
    class Dynamic(ConditionalGroupFormMixin, forms.Form):
        detail = forms.CharField()
        cv_conditional_groups = [ConditionalGroup(ValueToggle("kind", ["a"]), ["detail"], required=[])]

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields["kind"] = forms.ChoiceField(choices=[("a", "A"), ("b", "B")])

    form = Dynamic(data={"kind": kind, "detail": ""})
    assert form.is_valid() is (kind != "invalid")
    assert form.cleaned_data["detail"] == ""
    if kind == "invalid":
        assert form.errors.as_data()["kind"][0].code == "invalid_choice"


def test_value_group_runtime_fields_wrong_kind():
    class Dynamic(ConditionalGroupFormMixin, forms.Form):
        detail = forms.CharField()
        cv_conditional_groups = [ConditionalGroup(ValueToggle("kind", ["a"]), ["detail"])]

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields["kind"] = forms.CharField()

    with pytest.raises(ImproperlyConfigured, match="ChoiceField"):
        Dynamic(data={"kind": "a"}).is_valid()


def test_checkbox_only_overlaps_keep_legacy_behavior():
    class Legacy(ConditionalGroupFormMixin, forms.Form):
        detail = forms.CharField()
        cv_conditional_groups = [
            ConditionalGroup(UIFieldToggle("one"), ["detail"]),
            ConditionalGroup(UIFieldToggle("two"), ["detail", "absent"]),
        ]

    form = Legacy(data={"detail": "forged"})
    assert form.is_valid()
    assert form.cleaned_data["detail"] == ""


def test_value_group_runtime_callable_is_rejected_before_native_clean():
    def choices():
        raise AssertionError("conditional validation must reject callable choices before field cleaning")

    class Dynamic(ConditionalGroupFormMixin, forms.Form):
        detail = forms.CharField()
        cv_conditional_groups = [ConditionalGroup(ValueToggle("kind", ["a"]), ["detail"])]

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields["kind"] = forms.ChoiceField(choices=choices)

    with pytest.raises(ImproperlyConfigured, match="callable choices"):
        Dynamic(data={"kind": "a", "detail": "forged"}).is_valid()


def test_value_group_runtime_controlled_field_added_optional():
    class Dynamic(ConditionalGroupFormMixin, forms.Form):
        kind = forms.ChoiceField(choices=[("a", "A")])
        cv_conditional_groups = [ConditionalGroup(ValueToggle("kind", ["a"]), ["detail"], required=[])]

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields["detail"] = forms.CharField()

    form = Dynamic(data={"kind": "a"})
    assert form.is_valid(), form.errors


@pytest.mark.parametrize("empty", [False, True])
def test_value_group_inherited_clean_replaces_cleaned_mapping(empty):
    class Parent(forms.Form):
        kind = forms.ChoiceField(choices=[("a", "A")])
        detail = forms.CharField()

        def clean(self):
            # Django permits returning a replacement mapping, not only mutating it.
            if empty:
                return {}
            return {name: value for name, value in super().clean().items() if name != "kind"}

    class Child(ConditionalGroupFormMixin, Parent):
        cv_conditional_groups = [ConditionalGroup(ValueToggle("kind", ["a"]), ["detail"])]

    form = Child(data={"kind": "a", "detail": "forged"})
    assert form.is_valid(), form.errors
    assert form.cleaned_data == {"detail": ""}


@pytest.mark.parametrize("kind", ["a", "b"])
@pytest.mark.parametrize("detail", ["submitted", ""])
@pytest.mark.parametrize("parent_error", [False, True])
def test_value_group_inherited_clean_returns_none(kind, detail, parent_error):
    class Parent(forms.Form):
        kind = forms.ChoiceField(choices=[("a", "A"), ("b", "B")])
        detail = forms.CharField()
        outside = forms.CharField()

        def clean(self):
            super().clean()
            self.cleaned_data["outside"] = "parent normalized"
            if parent_error:
                self.add_error(None, forms.ValidationError("Parent rejected input", code="parent_error"))
            # Returning None legally preserves Django's existing cleaned mapping.

    class Child(ConditionalGroupFormMixin, Parent):
        cv_conditional_groups = [ConditionalGroup(ValueToggle("kind", ["a"]), ["detail"])]

    form = Child(data={"kind": kind, "detail": detail, "outside": "submitted"})
    missing_required = kind == "a" and not detail
    assert form.is_valid() is (not parent_error and not missing_required)
    assert form.cleaned_data["outside"] == "parent normalized"
    assert form.cleaned_data["kind"] == kind
    if missing_required:
        assert form.errors["detail"] == [form.fields["detail"].error_messages["required"]]
    else:
        assert form.cleaned_data["detail"] == (detail if kind == "a" else "")
    if parent_error:
        assert form.errors.as_data()["__all__"][0].code == "parent_error"
