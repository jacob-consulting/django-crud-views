from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, field_validator

from .toggle import ToggleSource, ValueToggle


class ConditionalFormSet(BaseModel, arbitrary_types_allowed=True):
    """Governs whether an entire first-level formset is shown/validated.

    Declared on a ``FormSet`` via ``conditional=``. When the parent-form toggle
    is off, the formset is excluded from the validity gate; on save, ``skip``
    leaves existing rows untouched while ``purge`` deletes them.
    """

    toggle: ToggleSource
    on_off: Literal["skip", "purge"] = "skip"

    @field_validator("toggle")
    @classmethod
    def reject_value_toggle(cls, toggle):
        if isinstance(toggle, ValueToggle):
            raise ValueError(
                "ValueToggle supports ConditionalGroup only; whole-formset activation requires "
                "a checkbox ModelFieldToggle or UIFieldToggle."
            )
        return toggle
