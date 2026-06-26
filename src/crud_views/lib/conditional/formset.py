from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from .toggle import ToggleSource


class ConditionalFormSet(BaseModel, arbitrary_types_allowed=True):
    """Governs whether an entire first-level formset is shown/validated.

    Declared on a ``FormSet`` via ``conditional=``. When the parent-form toggle
    is off, the formset is excluded from the validity gate; on save, ``skip``
    leaves existing rows untouched while ``purge`` deletes them.
    """

    toggle: ToggleSource
    on_off: Literal["skip", "purge"] = "skip"
