"""Private, immutable presentation data for one object-detail render."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING
from uuid import uuid4

from django.core.exceptions import ImproperlyConfigured

if TYPE_CHECKING:
    from crud_views_object_detail.lib.resolvers import ResolvedGroup

_SCOPE_KEY = "_cv_od_render_scope"


@dataclass(frozen=True)
class GroupPresentation:
    group: ResolvedGroup
    control_id: str
    panel_id: str
    selected: bool


@dataclass(frozen=True)
class ComponentPresentation:
    id: str
    tablist_id: str
    content_id: str
    groups: tuple[GroupPresentation, ...]


def _validate_id_token(value, label):
    if not isinstance(value, str) or re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", value) is None:
        raise ImproperlyConfigured(f"{label} must match [A-Za-z][A-Za-z0-9_-]*; got {value!r}")
    return value


def _render_scope(context):
    """Share identity only for the outer render and explicitly transported children."""
    transported = context.get(_SCOPE_KEY)
    if transported is not None:
        return transported
    frames = context.render_context.dicts
    if len(frames) < 2:
        # A direct tag call has no Template.render lifetime; don't retain its scope.
        return set()
    # Includes push their own frames; inheritance may reuse one. The first active
    # frame belongs to the outer render and is popped even when rendering raises.
    # Never write into frame zero: it survives when callers reuse their Context.
    return frames[1].setdefault(_SCOPE_KEY, set())


def _project_component(groups, component_id=None, scope=None):
    token = "g" + uuid4().hex if component_id is None else _validate_id_token(component_id, "component_id")
    base = f"cvod-c{len(token)}-{token}"
    entries = []
    group_keys = set()
    for index, group in enumerate(groups):
        key = group.id
        if key is not None:
            _validate_id_token(key, "group id")
            if key in group_keys:
                raise ImproperlyConfigured(
                    f"Duplicate object-detail group id {key!r} in component_id {token!r}; "
                    "distinct group ids are required"
                )
            group_keys.add(key)
        suffix = f"s{len(key)}-{key}" if key is not None else f"i{index}"
        entries.append(GroupPresentation(group, f"{base}-{suffix}-control", f"{base}-{suffix}-panel", index == 0))
    component = ComponentPresentation(f"{base}-root", f"{base}-tabs", f"{base}-content", tuple(entries))
    ids = [component.id, component.tablist_id, component.content_id]
    ids.extend(value for entry in entries for value in (entry.control_id, entry.panel_id))
    if len(ids) != len(set(ids)) or (scope is not None and scope.intersection(ids)):
        raise ImproperlyConfigured(
            f"Duplicate object-detail identity in component_id {token!r}; "
            f"distinct component/group ids are required in the shared render scope: {ids!r}"
        )
    if scope is not None:
        scope.update(ids)
    return component
