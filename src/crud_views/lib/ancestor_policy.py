"""
Ancestor authorization policy values (phase 06.18).

``AncestorPermissions`` and ``AncestorPolicy`` are small typed configuration values: they hold no request,
user, object or grant state and have no evaluation methods. The request engine lives in
``crud_views.lib.ancestors``. This module imports neither ``ViewSet`` nor Guardian, so the settings module can
use it to validate global defaults.

- ``provider`` / ``accept_global_perms`` describe the owning ViewSet when it is used as an *ancestor*.
- ``cascade`` / ``read`` / ``write`` / ``actions`` describe requests that *target* the owning ViewSet.
"""

from typing import Literal

from pydantic import BaseModel, Field

AncestorProvider = Literal["model", "guardian", "none"]

# Package defaults of the global settings (CRUD_VIEWS_ANCESTOR_*).
DEFAULT_CASCADE = True
DEFAULT_READ_PERMISSIONS = {"nearest": "view", "higher": "view"}
DEFAULT_WRITE_PERMISSIONS = {"nearest": "change", "higher": "view"}


class AncestorPermissions(BaseModel):
    """A complete pair of permission-map keys: ``nearest`` for the nearest protected ancestor, ``higher`` for
    every farther protected ancestor (full cascade only). Each key is resolved against the selected ancestor's
    own permission map."""

    nearest: str
    higher: str


class AncestorPolicy(BaseModel):
    """Per-ViewSet ancestor policy. See the module docstring for the two scopes of its fields."""

    provider: AncestorProvider | None = None  # None: the owning ViewSet class default
    accept_global_perms: bool = False  # Guardian ancestor: also accept the required model permission
    cascade: bool | None = None  # None: inherit the global setting
    read: AncestorPermissions | None = None  # None: inherit the global Read pair
    write: AncestorPermissions | None = None  # None: inherit the global Write pair
    actions: dict[str, AncestorPermissions] = Field(default_factory=dict)  # exact registered view key -> pair
