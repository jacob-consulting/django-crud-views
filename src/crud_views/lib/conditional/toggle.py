from __future__ import annotations

from django import forms
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.db import models
from django.forms import BaseForm

try:
    from django.utils.choices import CallableChoiceIterator
except ImportError:  # Django 4.2
    from django.forms.fields import CallableChoiceIterator

_FALSEY = {"", "false", "0", "off", "none"}


class ToggleSource:
    """Resolve a boolean toggle from a form's *submitted* data — never from JS.

    Subclasses differ only in whether the toggle field is a persisted model
    field (``ModelFieldToggle``) or a transient, injected UI field
    (``UIFieldToggle``).
    """

    inject: bool = False

    def __init__(self, name: str):
        self.name = name

    def field_name(self) -> str:
        return self.name

    def is_on(self, form: BaseForm) -> bool:
        # Prefer cleaned_data once the form has been validated.
        cleaned = getattr(form, "cleaned_data", None)
        if cleaned is not None and self.name in cleaned:
            return bool(cleaned[self.name])
        # Fall back to raw submitted data (checkbox semantics).
        raw = form.data.get(form.add_prefix(self.name)) if form.is_bound else None
        if raw is None:
            return False
        return str(raw).strip().lower() not in _FALSEY


class ModelFieldToggle(ToggleSource):
    """Toggle backed by a real field already present on the form/model."""

    inject = False


class UIFieldToggle(ToggleSource):
    """Toggle backed by a transient, non-model BooleanField.

    For field-groups (``ConditionalGroup``) the form mixin injects this field
    automatically. For conditional formsets the field must already exist on the
    parent form (declare it, or reuse the group mixin)."""

    inject = True


def _choice_token(value):
    """Use the exact string token native choice widgets submit (zero included)."""
    if isinstance(value, bool) or not isinstance(value, (str, int)) or value == "":
        raise ImproperlyConfigured(
            "ValueToggle values and choice keys must be nonempty strings or integers, not bool/None."
        )
    return str(value)


class ValueToggle(ToggleSource):
    """Activate a field group for explicit values of a native single-choice field."""

    def __init__(self, name: str, values):
        super().__init__(name)
        if isinstance(values, (str, bytes)):
            raise ImproperlyConfigured("ValueToggle values must be a nonempty collection, not a scalar string.")
        try:
            self.values = tuple(_choice_token(value) for value in values)
        except TypeError as exc:
            raise ImproperlyConfigured(
                "ValueToggle values must be a nonempty collection of strings or integers."
            ) from exc
        if not self.values or len(set(self.values)) != len(self.values):
            raise ImproperlyConfigured(
                "ValueToggle values must be nonempty and contain no duplicate normalized tokens."
            )

    def validate_field(self, field, model_field=None):
        """Reject declarations whose native HTML and cleaned tokens could disagree."""
        if type(field) not in (forms.ChoiceField, forms.TypedChoiceField) or type(field.widget) not in (
            forms.Select,
            forms.RadioSelect,
        ):
            raise ImproperlyConfigured(
                f"ValueToggle '{self.name}' requires a standard ChoiceField/TypedChoiceField and Select/RadioSelect."
            )
        if isinstance(field.choices, CallableChoiceIterator):
            raise ImproperlyConfigured(
                f"ValueToggle '{self.name}' does not support callable choices; use static choices."
            )
        coerce = str
        if type(field) is forms.TypedChoiceField:
            coerce = field.coerce
            owner = getattr(coerce, "__self__", None)
            native_models = (
                models.CharField,
                models.TextField,
                models.EmailField,
                models.URLField,
                models.SlugField,
                models.IntegerField,
                models.SmallIntegerField,
                models.BigIntegerField,
                models.PositiveIntegerField,
                models.PositiveSmallIntegerField,
                models.PositiveBigIntegerField,
            )
            if coerce not in (str, int) and not (
                type(owner) in native_models
                and getattr(coerce, "__func__", None) is type(owner).to_python
                and (model_field is None or type(owner) is type(model_field))
            ):
                raise ImproperlyConfigured(
                    f"ValueToggle '{self.name}' requires str/int or native text/integer coercion."
                )
        tokens = set()
        for key, label in field.choices:
            choices = label if isinstance(label, (list, tuple)) else [(key, label)]
            for value, _label in choices:
                # Django's generated blank option is absence, not an integer to coerce.
                if value == "" or value is None:
                    continue
                token = _choice_token(value)
                try:
                    canonical = _choice_token(coerce(token))
                except (TypeError, ValueError, ValidationError) as exc:
                    raise ImproperlyConfigured(f"ValueToggle '{self.name}' requires canonical choice tokens.") from exc
                if canonical != token or token in tokens:
                    raise ImproperlyConfigured(
                        f"ValueToggle '{self.name}' requires unique canonical choice tokens; invalid key {value!r}."
                    )
                tokens.add(token)
        if (
            type(field) is forms.TypedChoiceField
            and field.empty_value not in field.empty_values
            and _choice_token(field.empty_value) in tokens
        ):
            raise ImproperlyConfigured(f"ValueToggle '{self.name}' empty_value must not collide with a choice token.")
        if not set(self.values) <= tokens:
            raise ImproperlyConfigured(f"ValueToggle '{self.name}' values must match declared nonempty choices.")

    def is_on(self, form: BaseForm) -> bool:
        field = form.fields.get(self.name)
        if field is None:
            raise ImproperlyConfigured(f"ValueToggle controller '{self.name}' is missing from the form.")
        self.validate_field(field)
        value = form.cleaned_data.get(self.name) if hasattr(form, "cleaned_data") else form[self.name].value()
        if value in field.empty_values or (type(field) is forms.TypedChoiceField and value == field.empty_value):
            return False
        return _choice_token(value) in self.values
