"""Private, immutable presentation data for one object-detail render."""

import re
from dataclasses import dataclass
from uuid import uuid4

from django.core.exceptions import ImproperlyConfigured

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
    transported = context.get(_SCOPE_KEY)
    if transported is not None:
        return transported
    if _SCOPE_KEY not in context.render_context:
        context.render_context[_SCOPE_KEY] = set()
    return context.render_context[_SCOPE_KEY]


def _project_component(groups, component_id=None, scope=None):
    token = "g" + uuid4().hex if component_id is None else _validate_id_token(component_id, "component_id")
    base = f"cvod-c{len(token)}-{token}"
    entries = []
    for index, group in enumerate(groups):
        key = getattr(group, "id", None)
        suffix = f"s{len(key)}-{key}" if key is not None else f"i{index}"
        entries.append(GroupPresentation(group, f"{base}-{suffix}-control", f"{base}-{suffix}-panel", index == 0))
    return ComponentPresentation(f"{base}-root", f"{base}-tabs", f"{base}-content", tuple(entries))
