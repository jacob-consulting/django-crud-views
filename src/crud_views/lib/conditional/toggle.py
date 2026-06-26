from __future__ import annotations

from django.forms import BaseForm

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
