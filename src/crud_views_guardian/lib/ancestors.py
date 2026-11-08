"""
Guardian ancestor provider (phase 06.18).

A ``GuardianViewSet`` checked as an *ancestor* of a nested request is a strict object-permission gate: the shared
engine (``crud_views.lib.ancestors``) resolves the ancestor object and the required permission string from this
ancestor's own permission map (Guardian's configured content-type semantics), then calls this provider through
``GuardianViewSet._ancestor_has_permission``.

* An inactive authenticated actor is denied before any shortcut (superuser, model fallback, checker query).
* With the ancestor's own ``AncestorPolicy.accept_global_perms``, the required *model* permission is accepted as an
  alternative (``user.has_perm(permission)`` without an object — Django's ``ModelBackend`` answers nothing once an
  object is passed). The endpoint view's ``cv_guardian_accept_global_perms`` is never consulted here.
* Otherwise a direct or group object grant on the resolved ancestor (Guardian's ``ObjectPermissionChecker``;
  active superusers keep Guardian's superuser semantics).

The checker is reused only within the requested (or rendering) view instance of one request; helpers called
without a view use a fresh checker. Nothing outlives the request, so a revoked grant takes effect on the next
request.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.db.models import Model

    from crud_views.lib.view import CrudView
    from crud_views_guardian.lib.viewset import GuardianViewSet


def _request_checker(view: CrudView | None, user):
    """The view-local ``ObjectPermissionChecker`` for ``user`` (created on first use); a fresh one when a helper
    runs without a view."""
    from guardian.core import ObjectPermissionChecker

    if view is None:
        return ObjectPermissionChecker(user)
    cached = getattr(view, "_cv_guardian_ancestor_checker", None)
    if cached is None or cached[0] is not user:
        cached = (user, ObjectPermissionChecker(user))
        view._cv_guardian_ancestor_checker = cached
    return cached[1]


def _guardian_ancestor_has_permission(
    viewset: GuardianViewSet, user, permission: str, obj: Model, *, view: CrudView | None
) -> bool:
    """Whether ``user`` satisfies the Guardian ancestor gate ``permission`` on the resolved ancestor ``obj``."""
    from crud_views_guardian.lib.mixins import _guardian_inactive_actor

    if not getattr(user, "is_authenticated", False) or _guardian_inactive_actor(user):
        return False
    if viewset.ancestor_policy.accept_global_perms and user.has_perm(permission):
        return True
    return _request_checker(view, user).has_perm(permission, obj)
