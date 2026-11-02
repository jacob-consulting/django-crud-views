# tests/test1/test_conditional_group.py
import pytest
from django import forms
from django.core.exceptions import ImproperlyConfigured

from crud_views.lib.conditional.group import ConditionalGroup, ConditionalGroupFormMixin
from crud_views.lib.conditional.toggle import ModelFieldToggle, UIFieldToggle
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
