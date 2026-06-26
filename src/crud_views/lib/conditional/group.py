from __future__ import annotations

from typing import Any

from django.forms import BooleanField

from .toggle import ToggleSource


class ConditionalGroup:
    """A group of form fields governed by a single boolean toggle.

    When the toggle is on, ``required`` fields are enforced. When off, every
    field in the group is cleared to its empty value and never validated.
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

    cv_conditional_groups: list[ConditionalGroup] = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for group in self.cv_conditional_groups:
            # Inject transient UI toggle fields that are not model fields.
            tname = group.toggle.field_name()
            if group.toggle.inject and tname not in self.fields:
                self.fields[tname] = BooleanField(required=False)
            # Disarm Django's premature field-level required check; clean() owns it.
            for name in group.fields:
                if name in self.fields:
                    self.fields[name].required = False

    def clean(self):
        cleaned = super().clean()
        for group in self.cv_conditional_groups:
            if group.is_on(self):
                for name in group.required_fields:
                    if cleaned.get(name) in self.fields[name].empty_values:
                        self.add_error(name, self.fields[name].error_messages["required"])
            else:
                for name in group.fields:
                    cleaned[name] = group.empty_value_for(name)
        return cleaned
