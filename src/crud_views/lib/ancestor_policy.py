"""Configuration types of ancestor authorization for nested ViewSets.

These are small, strictly validated values: they hold no request, user, object or grant state and evaluate no
permission. ``ViewSet`` validates how its own policy is used (owning class, provider, top-level scope) before
registration; request enforcement reads the values later. This module imports no view or ViewSet code, so
``crud_views.lib.settings`` can use the pair type for the global defaults.
"""

from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, StrictBool, StrictStr


def _permission_key(value: str) -> str:
    """A permission-map key or action key: nonempty and not padded with whitespace."""
    if not value or value != value.strip():
        raise ValueError(f"must be a nonempty key without surrounding whitespace, got {value!r}")
    return value


PermissionKey = Annotated[StrictStr, AfterValidator(_permission_key)]


class AncestorPermissions(BaseModel):
    """Permission-map keys required on the nearest protected ancestor and on every higher selected one.

    A pair is always complete and replaces an inherited pair whole; there is no partial merge or ``None`` skip.
    """

    model_config = ConfigDict(extra="forbid")

    nearest: PermissionKey
    higher: PermissionKey


class AncestorPolicy(BaseModel):
    """Ancestor authorization of one ViewSet.

    ``provider`` and ``accept_global_perms`` describe this ViewSet when it is checked as an ancestor of a
    descendant. ``cascade``, ``read``, ``write`` and ``actions`` describe requests targeting this ViewSet and are
    only meaningful on a nested ViewSet. ``None`` means: the owning class default (``provider``) or the global
    setting (``cascade``, ``read``, ``write``).
    """

    model_config = ConfigDict(extra="forbid")

    provider: Literal["model", "guardian", "none"] | None = None
    accept_global_perms: StrictBool = False
    cascade: StrictBool | None = None
    read: AncestorPermissions | None = None
    write: AncestorPermissions | None = None
    actions: dict[PermissionKey, AncestorPermissions] = Field(default_factory=dict)
