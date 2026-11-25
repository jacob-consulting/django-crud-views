"""Private link checks: parent gates, then own permission, then state.

Built from the request gate's pieces, these functions decide links only. They never authorize a request,
load an ancestor, or store a decision. Callers supply the target's own object and known ancestors separately.
"""

from __future__ import annotations

from crud_views.lib import ancestors
from crud_views.lib.ancestor_db import _check_nested_auth

_LINK_ALLOWED = "allowed"
_LINK_PERMISSION = "permission"
_LINK_STATE = "state"
_PARENT_UNSET = object()


def _known_link_ancestors(target, rendering_view, *, immediate_parent=_PARENT_UNSET):
    """Align already-resolved objects to the target's ancestry, preserving unknown levels.

    Child links supply their URL object explicitly. An explicit None is an unknown
    parent, not permission to fall back to guard state, relations, or a lookup.
    """
    return tuple(
        immediate_parent
        if index == 0 and immediate_parent is not _PARENT_UNSET
        else ancestors._resolved_ancestor(rendering_view, ancestor.name)
        for index, (_, ancestor) in enumerate(ancestors._walk_ancestors(target.cv_viewset))
    )


def _higher_ancestor_gates(target, user, known_ancestors) -> bool:
    """Gate supplied higher levels outermost first, without a rendering view.

    A None element is absent and is not gated. With no level to gate, allow before any actor rule.
    Otherwise validate the operation pair, admit the actor, then check each level's auth database,
    permission name and provider, in the request's order. An anonymous or inactive actor therefore does
    not report a higher level's missing permission key or non-default auth database; the nearest gate
    keeps _immediate_parent_access's validation-first order.

    Migrated consumers supply known higher ancestors aligned with the target's declared ancestry.
    """
    viewset = target.cv_viewset
    chain = ancestors._walk_ancestors(viewset)
    selected = ancestors._selected_gates(viewset, chain)
    levels = [
        index
        for index in selected
        if 1 <= index < min(len(known_ancestors), len(chain)) and known_ancestors[index] is not None
    ]
    if not levels:
        return True
    pair = ancestors._operation_requirements(target)
    if not (user.is_authenticated and user.is_active):
        return False
    for index in sorted(levels, reverse=True):
        _, ancestor = chain[index]
        obj = known_ancestors[index]
        key = pair.nearest if selected[index] == "nearest" else pair.higher
        _check_nested_auth(
            target, actor=user, model=ancestor.model, obj=obj, provider=ancestors._effective_provider(ancestor)
        )
        permission = ancestors._permission_name(viewset, ancestor, key, ancestors._registered_key(target))
        if not ancestor._ancestor_has_permission(user, permission, obj, view=None):
            return False
    return True


def _link_permission(target, user, obj=None, known_ancestors=(), *, rendering_view=None) -> bool:
    """Check supplied parent gates and own permission; a missing nearest parent denies every nested target."""
    nested = target.cv_viewset.has_parent
    parent = known_ancestors[0] if nested and known_ancestors else None
    if nested and parent is None:
        return False
    if nested and len(known_ancestors) > 1 and not _higher_ancestor_gates(target, user, known_ancestors):
        return False
    own = obj if target.cv_object else None
    return bool(target._cv_link_permission(user, own, parent, rendering_view=rendering_view))


def _link_access(target, user, obj=None, known_ancestors=(), *, rendering_view=None) -> str:
    """Evaluate state only after permission passes, using the request's action-object rule."""
    if not _link_permission(target, user, obj, known_ancestors, rendering_view=rendering_view):
        return _LINK_PERMISSION
    action_obj = obj if target.cv_object else known_ancestors[0] if target.cv_viewset.has_parent else None
    return _LINK_ALLOWED if target.cv_action_enabled(user, action_obj) else _LINK_STATE


def _link_ctx(outcome: str) -> dict:
    """Stamp the existing visibility fields; permission denial leaves state unevaluated."""
    return {"cv_access": outcome != _LINK_PERMISSION, "cv_action_enabled": outcome != _LINK_STATE}
