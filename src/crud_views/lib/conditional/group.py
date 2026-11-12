from __future__ import annotations

from contextlib import suppress
from typing import Any, ClassVar

from django import forms
from django.core.exceptions import FieldDoesNotExist, ImproperlyConfigured, ValidationError
from django.db import models
from django.forms import BooleanField

from .toggle import CallableChoiceIterator, ToggleSource, ValueToggle, _choice_token


def _native_choice_conversion(form_field, model_field):
    """Recognize static scalar choices and unchanged conversion hooks only."""
    if (
        type(form_field) not in (forms.ChoiceField, forms.TypedChoiceField)
        or not isinstance(model_field.choices, (list, tuple))
        or not model_field.choices
        or isinstance(form_field.choices, CallableChoiceIterator)
        or getattr(model_field.to_python, "__func__", None) is not type(model_field).to_python
        or getattr(form_field.to_python, "__func__", None) is not type(form_field).to_python
    ):
        return False
    if type(form_field) is forms.TypedChoiceField and form_field.coerce not in (str, int, model_field.to_python):
        return False
    try:
        # Reject unusual scalar keys rather than guessing their native empty state.
        for value, _label in model_field.flatchoices:
            if value in ("", None):
                continue
            token = _choice_token(value)
            if _choice_token(model_field.to_python(token)) != token:
                return False
    except (ImproperlyConfigured, TypeError, ValueError, ValidationError):
        return False
    return True


def validate_value_groups(groups, fields, model=None):
    """Validate value-involved declarations without constructing forms or querying.

    ``fields=None`` checks structure before initialization mutates fields. Static
    callers may omit request-added fields; runtime callers check their presence.
    """
    for group in groups:
        if not isinstance(group.toggle, ValueToggle):
            continue
        controller = group.toggle.field_name()
        controlled = set(group.fields)
        outside = set(group.required_fields) - controlled
        if outside:
            raise ImproperlyConfigured(
                f"ValueToggle '{controller}' required fields {sorted(outside)} must belong to its controlled fields."
            )
        for other in groups:
            other_controller = other.toggle.field_name()
            conflicts = controlled & set(other.fields) if other is not group else set()
            if controller in other.fields:
                conflicts.add(controller)
            if other_controller in controlled:
                conflicts.add(other_controller)
            if conflicts:
                raise ImproperlyConfigured(
                    f"ValueToggle '{controller}' conflicts with group '{other_controller}' on fields "
                    f"{sorted(conflicts)}; use disjoint controlled fields and never control a group controller."
                )
        if fields is not None and controller in fields:
            model_field = None
            if model is not None:
                with suppress(FieldDoesNotExist):
                    model_field = model._meta.get_field(controller)
            group.toggle.validate_field(fields[controller], model_field)


def resolve_conditional_empty_value(form_field, model_field, group, field_name):
    """Resolve a native off value for a bounded, standard Django field pair.

    Private runtime/checks seam. Callers must handle trusted disabled fields first.
    Explicit values are native persistence instructions, including falsy values.
    """
    if field_name in group.empty_values:
        return group.empty_values[field_name]

    text_forms = (forms.CharField, forms.EmailField, forms.URLField, forms.SlugField, forms.RegexField)
    text_models = (models.CharField, models.TextField, models.EmailField, models.URLField, models.SlugField)
    integer_models = (
        models.IntegerField,
        models.SmallIntegerField,
        models.BigIntegerField,
        models.PositiveIntegerField,
        models.PositiveSmallIntegerField,
        models.PositiveBigIntegerField,
    )
    scalar_pairs = {
        models.IntegerField: forms.IntegerField,
        models.SmallIntegerField: forms.IntegerField,
        models.BigIntegerField: forms.IntegerField,
        models.PositiveIntegerField: forms.IntegerField,
        models.PositiveSmallIntegerField: forms.IntegerField,
        models.PositiveBigIntegerField: forms.IntegerField,
        models.FloatField: forms.FloatField,
        models.DecimalField: forms.DecimalField,
        models.DateField: forms.DateField,
        models.TimeField: forms.TimeField,
        models.DateTimeField: forms.DateTimeField,
        models.DurationField: forms.DurationField,
        models.UUIDField: forms.UUIDField,
        models.ForeignKey: forms.ModelChoiceField,
    }
    if model_field is None:
        if type(form_field) in text_forms:
            return form_field.empty_value
        if type(form_field) is forms.MultipleChoiceField:
            return []
        if type(form_field) is forms.BooleanField:
            return False
        if type(form_field) is forms.NullBooleanField:
            return None
    else:
        # Exact classes plus native hooks: custom subclasses/overrides need an explicit value.
        native_hook = getattr(type(model_field), "save_form_data", None)
        hook = getattr(model_field.save_form_data, "__func__", None)
        if hook is native_hook:
            if type(model_field) in (*text_models, *integer_models) and _native_choice_conversion(
                form_field, model_field
            ):
                if model_field.null:
                    return None
                if type(model_field) in text_models and model_field.blank:
                    return ""
            if type(model_field) in text_models and type(form_field) in text_forms:
                if model_field.null:
                    return None
                if model_field.blank:
                    return ""
            if type(model_field) is models.BooleanField:
                expected = forms.NullBooleanField if model_field.null else forms.BooleanField
                if type(form_field) is expected:
                    return None if model_field.null else False
            if (
                type(model_field) in scalar_pairs
                and type(form_field) is scalar_pairs[type(model_field)]
                and model_field.null
            ):
                return None
            file_pairs = {models.FileField: forms.FileField, models.ImageField: forms.ImageField}
            if type(model_field) in file_pairs and type(form_field) is file_pairs[type(model_field)]:
                return False
            if type(model_field) is models.ManyToManyField and type(form_field) is forms.ModelMultipleChoiceField:
                return []
    raise ImproperlyConfigured(
        f"Conditional group '{group.toggle.field_name()}' field '{field_name}' has no supported automatic "
        "empty value; configure empty_values explicitly."
    )


class ConditionalGroup:
    """A group of form fields governed by a single boolean toggle.

    When the toggle is on, ``required`` fields are enforced. When off, editable
    fields are cleared and their ordinary field errors suppressed. Inherited
    nonfield errors and model validation still apply to the resulting state.
    """

    def __init__(
        self,
        toggle: ToggleSource,
        fields: list[str],
        required: list[str] | None = None,
        empty_values: dict[str, Any] | None = None,
    ):
        self.toggle = toggle
        self.fields = list(fields)
        self.required = list(required) if required is not None else None
        self.empty_values = empty_values or {}

    @property
    def required_fields(self) -> list[str]:
        return self.required if self.required is not None else self.fields

    def is_on(self, form) -> bool:
        return self.toggle.is_on(form)

    def empty_value_for(self, name: str) -> Any:
        return self.empty_values.get(name, None)


class ConditionalGroupFormMixin:
    """Server-side authority for conditional field-groups.

    Mix in *before* the concrete Form/ModelForm. JS is irrelevant to the
    outcome: an off group is always cleared, an on group always enforces its
    required fields, regardless of what the client submitted.
    """

    cv_conditional_groups: ClassVar[list[ConditionalGroup]] = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        validate_value_groups(self.cv_conditional_groups, None)
        self._cv_conditional_original_values = {}
        for group in self.cv_conditional_groups:
            # Inject transient UI toggle fields that are not model fields.
            tname = group.toggle.field_name()
            if group.toggle.inject and tname not in self.fields:
                self.fields[tname] = BooleanField(required=False)
            # Disarm Django's premature field-level required check; clean() owns it.
            for name in group.fields:
                if name in self.fields and not self.fields[name].disabled:
                    self.fields[name].required = False

    def clean(self):
        # Configuration must support switching off even for an active submission.
        # Run here to include fields added by request-dependent subclass __init__
        # methods, without constructing arbitrary forms during startup checks.
        validate_value_groups(
            self.cv_conditional_groups, self.fields, getattr(getattr(self, "_meta", None), "model", None)
        )
        for group in self.cv_conditional_groups:
            if isinstance(group.toggle, ValueToggle):
                missing = (set(group.fields) | {group.toggle.field_name()}) - self.fields.keys()
                if missing:
                    raise ImproperlyConfigured(
                        f"ValueToggle '{group.toggle.field_name()}' fields {sorted(missing)} are missing from the form."
                    )
            for name in group.fields:
                if name in self.fields and not self.fields[name].disabled:
                    resolve_conditional_empty_value(self.fields[name], self._cv_model_field(name), group, name)
        cleaned = super().clean()
        for group in self.cv_conditional_groups:
            if group.is_on(self):
                self._cv_enforce_required(group, cleaned)
            else:
                self._cv_clear_group(group, cleaned)
        return cleaned

    def full_clean(self):
        self._cv_conditional_values = {}
        self._cv_conditional_requires_save = False
        return super().full_clean()

    def _cv_model_field(self, name):
        if not isinstance(self, forms.ModelForm):
            return None
        try:
            return self._meta.model._meta.get_field(name)
        except FieldDoesNotExist:
            return None

    def _post_clean(self):
        # Native ModelForm construction can skip omitted empty fields with defaults.
        # Set their resolved state first, so model clean/uniqueness sees the final value.
        if isinstance(self, forms.ModelForm):
            for name, value in self._cv_conditional_values.items():
                field = self._cv_model_field(name)
                if field is not None and field.many_to_many:
                    if not self.instance._state.adding:
                        previous = self._cv_conditional_original_values.setdefault(
                            name, {obj.pk for obj in field.value_from_object(self.instance)}
                        )
                        resolved = {getattr(obj, "pk", obj) for obj in value}
                        if previous != resolved:
                            self._cv_conditional_requires_save = True
                elif field is not None:
                    previous = self._cv_conditional_original_values.setdefault(
                        name, field.value_from_object(self.instance)
                    )
                    field.save_form_data(self.instance, value)
                    if previous != field.value_from_object(self.instance):
                        self._cv_conditional_requires_save = True
        super()._post_clean()

    def _cv_enforce_required(self, group, cleaned):
        for name in group.required_fields:
            # A field that already failed its own validation keeps that error;
            # piling a "required" error on top would contradict it.
            if name in self.fields and name not in self.errors and cleaned.get(name) in self.fields[name].empty_values:
                self.add_error(name, self.fields[name].error_messages["required"])

    def _cv_clear_group(self, group, cleaned):
        for name in group.fields:
            if name in self.fields and not self.fields[name].disabled:
                # Off skips validation entirely: drop field-level errors too,
                # the submitted value is discarded either way.
                self.errors.pop(name, None)
                value = resolve_conditional_empty_value(self.fields[name], self._cv_model_field(name), group, name)
                cleaned[name] = value
                self._cv_conditional_values[name] = value


from crud_views.lib.crispy import CrispyModelForm  # noqa: E402  (placed at end to avoid cycle)


class ConditionalGroupModelForm(ConditionalGroupFormMixin, CrispyModelForm):
    """CrispyModelForm with conditional field-group support."""

    pass
