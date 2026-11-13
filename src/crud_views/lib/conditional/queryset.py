"""Opt-in category membership for native model-choice controllers."""

import contextlib
from dataclasses import dataclass
from inspect import getattr_static
from uuid import UUID

from django import forms
from django.core.exceptions import FieldDoesNotExist, ImproperlyConfigured
from django.db import models
from django.forms.models import ModelChoiceIterator

from .toggle import ToggleSource

_RENDER_PROJECTIONS = object()


def _category_token(value):
    if isinstance(value, bool) or not isinstance(value, (str, int, UUID)) or value == "":
        raise ImproperlyConfigured("QuerysetConditions keys must be nonempty strings, integers or UUIDs.")
    return str(value)


@dataclass(frozen=True)
class QuerysetConditions:
    """Declare the offered categories of a single ModelChoiceField.

    Keys with no membership activate no fields. Register even an all-no-fields
    source with ``ConditionalGroup(source.when(), fields=[], required=[])``.
    Its base form helper or ordinary InlineFormSet.get_helper_layout_fields must
    also include ``ToggleGroup(source.when())``, with the controller outside.
    Omitting that guard omits render coverage; selected-object validation still
    runs, but that custom helper is an incomplete integration.
    """

    controller: str
    conditional_key: str
    keys: tuple[str, ...]
    allow_unmatched: bool

    def __init__(self, controller, *, conditional_key, keys, allow_unmatched=False):
        if not isinstance(controller, str) or not controller:
            raise ImproperlyConfigured("QuerysetConditions requires a controller field name.")
        if not isinstance(conditional_key, str) or not conditional_key.isidentifier() or "__" in conditional_key:
            raise ImproperlyConfigured("QuerysetConditions requires a direct category attribute or annotation.")
        if isinstance(keys, (str, bytes)):
            raise ImproperlyConfigured("QuerysetConditions keys must be a collection.")
        try:
            normalized = tuple(_category_token(key) for key in keys)
        except TypeError as exc:
            raise ImproperlyConfigured("QuerysetConditions keys must be a collection.") from exc
        if len(set(normalized)) != len(normalized):
            raise ImproperlyConfigured("QuerysetConditions keys must be unique after normalization.")
        object.__setattr__(self, "controller", controller)
        object.__setattr__(self, "conditional_key", conditional_key)
        object.__setattr__(self, "keys", normalized)
        object.__setattr__(self, "allow_unmatched", allow_unmatched)

    def when(self, *keys):
        values = tuple(_category_token(key) for key in keys)
        if not set(values) <= set(self.keys):
            raise ImproperlyConfigured(f"QuerysetConditions '{self.controller}' membership uses undeclared keys.")
        return _QuerysetToggle(self, values)

    def category_for(self, obj):
        value = getattr(obj, self.conditional_key, None)
        # Missing/empty categories belong to actual objects, not blank selectors.
        if isinstance(value, (str, int, UUID)) and not isinstance(value, bool) and value != "":
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
        native = forms.ModelChoiceField
        if (
            not isinstance(field, native)
            or isinstance(field, forms.ModelMultipleChoiceField)
            or type(field.widget) is not forms.Select
            or field.widget.template_name != forms.Select.template_name
            or field.widget.option_template_name != forms.Select.option_template_name
            or field.iterator is not ModelChoiceIterator
            or getattr_static(field, "choices") is not native.choices
            or "_choices" in vars(field)
            or any(
                getattr(getattr(field, hook), "__func__", None) is not getattr(native, hook)
                for hook in ("prepare_value", "to_python", "validate", "clean")
            )
            or type(field.widget.choices) is not ModelChoiceIterator
            or field.widget.choices.field is not field
            or field.widget.choices.queryset is not field.queryset
        ):
            raise ImproperlyConfigured(
                f"QuerysetConditions '{self.name}' requires a native ModelChoiceField and single Select."
            )
        key = field.to_field_name
        identity = None
        if field.queryset is not None and (key is None or (isinstance(key, str) and "__" not in key)):
            with contextlib.suppress(FieldDoesNotExist):
                identity = field.queryset.model._meta.get_field(key) if key else field.queryset.model._meta.pk
        if (
            identity is None
            or not identity.concrete
            or identity.is_relation
            or not identity.unique
            or not isinstance(identity, (models.IntegerField, models.CharField, models.TextField, models.UUIDField))
        ):
            raise ImproperlyConfigured(
                f"QuerysetConditions '{self.name}' requires a concrete unique integer/text/UUID scalar selection key."
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
        """Project current offered options once per source in this render only.

        Native widget rendering owns labels. The projection reads only the
        direct category and prepare_value(), never field.choices or raw POST.
        """
        field = form.fields[self.name]
        self.validate_field(field)
        cache = context.render_context.get(_RENDER_PROJECTIONS)
        if cache is None:
            cache = context.render_context[_RENDER_PROJECTIONS] = {}
        key = (form, field, self.source, field.queryset)
        if key not in cache:
            projection = []
            error = None
            try:
                # A clone prevents an earlier render's queryset result cache
                # from concealing changed categories on a later render.
                for obj in field.queryset.all():
                    category = self.source.category_for(obj)
                    projection.append((category, str(field.prepare_value(obj))))
            except QuerysetConditionCoverageError as exc:
                error = exc
            cache[key] = (projection, error)
        projection, error = cache[key]
        if error is not None:
            raise error
        return [token for category, token in projection if category in self.values]
