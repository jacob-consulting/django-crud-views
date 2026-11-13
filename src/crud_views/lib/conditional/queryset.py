"""Opt-in category membership for native model-choice controllers."""

from dataclasses import dataclass

from django import forms
from django.core.exceptions import ImproperlyConfigured

from .toggle import ToggleSource, _choice_token


@dataclass(frozen=True, eq=False)
class QuerysetConditions:
    """Declare the offered categories of a single ModelChoiceField.

    Keys with no membership activate no fields. Register even an all-no-fields
    source with ``ConditionalGroup(source.when(), fields=[], required=[])``.
    """

    controller: str
    conditional_key: str
    keys: tuple[str, ...]
    allow_unmatched: bool

    def __init__(self, controller, *, conditional_key, keys, allow_unmatched=False):
        if not isinstance(controller, str) or not controller:
            raise ImproperlyConfigured("QuerysetConditions requires a controller field name.")
        if not isinstance(conditional_key, str) or not conditional_key or "__" in conditional_key:
            raise ImproperlyConfigured("QuerysetConditions requires a direct category attribute or annotation.")
        if isinstance(keys, (str, bytes)):
            raise ImproperlyConfigured("QuerysetConditions keys must be a collection.")
        normalized = tuple(_choice_token(key) for key in keys)
        if len(set(normalized)) != len(normalized):
            raise ImproperlyConfigured("QuerysetConditions keys must be unique after normalization.")
        object.__setattr__(self, "controller", controller)
        object.__setattr__(self, "conditional_key", conditional_key)
        object.__setattr__(self, "keys", normalized)
        object.__setattr__(self, "allow_unmatched", allow_unmatched)

    def when(self, *keys):
        values = tuple(_choice_token(key) for key in keys)
        if not set(values) <= set(self.keys):
            raise ImproperlyConfigured(f"QuerysetConditions '{self.controller}' membership uses undeclared keys.")
        return _QuerysetToggle(self, values)

    def category_for(self, obj):
        value = getattr(obj, self.conditional_key, None)
        # Missing/empty categories belong to actual objects, not blank selectors.
        if isinstance(value, (str, int)) and not isinstance(value, bool) and value != "":
            key = str(value)
            if key in self.keys:
                return key
        if not self.allow_unmatched:
            raise QuerysetConditionCoverageError(self.controller, value)
        return None


class QuerysetConditionCoverageError(ImproperlyConfigured):
    """An offered/selected object has no configured conditional category."""

    def __init__(self, controller, category):
        super().__init__(f"QuerysetConditions '{controller}' has unmatched category {category!r}.")


@dataclass(frozen=True, eq=False)
class _QuerysetToggle(ToggleSource):
    source: QuerysetConditions
    values: tuple[str, ...]

    @property
    def name(self):
        return self.source.controller

    def validate_field(self, field, model_field=None):
        if type(field) is not forms.ModelChoiceField or type(field.widget) is not forms.Select:
            raise ImproperlyConfigured(
                f"QuerysetConditions '{self.name}' requires a native ModelChoiceField and single Select."
            )

    def is_on(self, form):
        # Selection authority belongs exclusively to the final inherited clean mapping.
        obj = getattr(form, "cleaned_data", {}).get(self.name)
        if obj is None or not self.values:
            return False
        categories = getattr(form, "_cv_queryset_categories", {})
        category = categories[self.source] if self.source in categories else self.source.category_for(obj)
        return category in self.values

    def render_values(self, form, context):
        field = form.fields[self.name]
        self.validate_field(field)
        return [
            str(field.prepare_value(obj))
            for obj in field.queryset.all()
            if str(getattr(obj, self.source.conditional_key, None)) in self.values
        ]
