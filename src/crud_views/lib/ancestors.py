"""
Shared ancestor authorization for nested ViewSet requests (phase 06.18).

One request engine, ``_authorize_ancestors(view)``, runs before an endpoint's own work:

1. Top-level requests return immediately: no ancestor work at all.
2. Static selection, without database access: the requested operation's permission pair, the declared
   ancestry, each ancestor's effective provider and the levels selected for a permission gate (full cascade:
   every protected ancestor; nearest-only: the nearest protected one).
3. Actor admission when a gate is selected: anonymous actors get the endpoint's login/no-permission response,
   inactive authenticated actors 403 — both before any ancestor lookup.
4. Outermost inward, each ancestor is resolved through its own ViewSet queryset (called with the real child
   view), constrained to the URL PK and to the already resolved outer ancestor; missing → 404. A selected
   level's gate is checked immediately, before the next deeper lookup; denial → 403.
5. On success the resolved chain is stored on the view instance (request-local) and the request continues
   through its existing path; ``cv_get_parent_object()`` reuses the resolved immediate parent.

Plan 06.18-01 classifies the core list/detail (Read) and create/update/delete (Write) families; the remaining
finite families and the custom-endpoint declaration rules arrive with plan 06.18-02. Until then an
unclassified nested endpoint without an exact ``actions`` entry performs no ancestor work.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.http import Http404

from crud_views.lib.ancestor_policy import (
    DEFAULT_CASCADE,
    DEFAULT_READ_PERMISSIONS,
    DEFAULT_WRITE_PERMISSIONS,
    AncestorPermissions,
)
from crud_views.lib.exceptions import ViewSetNotFoundError

if TYPE_CHECKING:
    from django.db.models import Model

    from crud_views.lib.view import CrudView
    from crud_views.lib.viewset import ParentViewSet, ViewSet


@dataclass(frozen=True)
class _AncestorState:
    """Request-local result of a successful guard: resolved ancestors, nearest first."""

    objects: tuple[Model, ...]

    @property
    def parent(self) -> Model:
        """The immediate structural parent (whether or not it is protected)."""
        return self.objects[0]


def _walk_ancestors(viewset: ViewSet) -> list[tuple[ParentViewSet, ViewSet]]:
    """Declared ancestry of ``viewset``, nearest first, as ``(edge, ancestor)`` pairs.

    ``edge`` is the ``ParentViewSet`` declaration pointing at ``ancestor`` (its URL PK name and the relation
    attribute on the model below it). The walk is bounded: a missing or repeated ViewSet raises
    ``ImproperlyConfigured`` instead of looping. It touches no database.
    """
    chain: list[tuple[ParentViewSet, ViewSet]] = []
    seen = [viewset.name]
    edge = viewset.parent
    while edge is not None:
        try:
            ancestor = edge.viewset
        except ViewSetNotFoundError as exc:
            raise ImproperlyConfigured(
                f"ViewSet {viewset.name!r}: parent ViewSet {edge.name!r} is not registered "
                f"(ancestry {' -> '.join(seen)} -> {edge.name})"
            ) from exc
        if ancestor.name in seen:
            raise ImproperlyConfigured(
                f"ViewSet {viewset.name!r}: ancestry cycle {' -> '.join(seen)} -> {ancestor.name}"
            )
        seen.append(ancestor.name)
        chain.append((edge, ancestor))
        edge = ancestor.parent
    return chain


def _family(view_class: type[CrudView]) -> str | None:
    """'read' / 'write' for the classified core families, None for anything else (see module docstring)."""
    from crud_views.lib.views.create import CreateView
    from crud_views.lib.views.delete import DeleteView
    from crud_views.lib.views.detail import DetailView
    from crud_views.lib.views.list import ListView
    from crud_views.lib.views.update import UpdateView

    if issubclass(view_class, (ListView, DetailView)):
        return "read"
    if issubclass(view_class, (CreateView, UpdateView, DeleteView)):
        return "write"
    return None


def _operation_requirements(view_class: type[CrudView]) -> AncestorPermissions | None:
    """The permission pair required of ancestors for a request to ``view_class``.

    An exact ``actions`` entry for the registered key wins; otherwise the family's pair (the ViewSet's
    ``read``/``write`` override, else the global default). None: not classified yet.
    """
    policy = view_class.cv_viewset.ancestor_policy
    if view_class.cv_key in policy.actions:
        return policy.actions[view_class.cv_key]
    family = _family(view_class)
    if family == "read":
        return policy.read or AncestorPermissions(**DEFAULT_READ_PERMISSIONS)
    if family == "write":
        return policy.write or AncestorPermissions(**DEFAULT_WRITE_PERMISSIONS)
    return None


def _effective_provider(viewset: ViewSet) -> str:
    provider = viewset.ancestor_policy.provider
    return provider if provider is not None else type(viewset)._ancestor_provider


def _selected_gates(viewset: ViewSet, chain: list[tuple[ParentViewSet, ViewSet]]) -> dict[int, str]:
    """Chain index → which half of the pair applies ('nearest' / 'higher'), for the levels to gate."""
    protected = [index for index, (_, ancestor) in enumerate(chain) if _effective_provider(ancestor) != "none"]
    if not protected:
        return {}
    cascade = viewset.ancestor_policy.cascade
    if cascade is None:
        cascade = DEFAULT_CASCADE
    selected = {protected[0]: "nearest"}
    if cascade:
        selected.update(dict.fromkeys(protected[1:], "higher"))
    return selected


def _deny_anonymous(view: CrudView):
    """The endpoint's supported anonymous response; a login redirect for plain views without AccessMixin."""
    handler = getattr(view, "handle_no_permission", None)
    if handler is not None:
        return handler()
    from django.contrib.auth.views import redirect_to_login

    return redirect_to_login(view.request.get_full_path())


def _resolve_ancestor(view: CrudView, edge: ParentViewSet, ancestor: ViewSet, outer: Model | None) -> Model:
    """Load one ancestor through its ViewSet queryset, constrained to its URL PK and to the resolved outer
    ancestor (so a queryset override cannot waive the declared relationship). Missing → 404."""
    queryset = ancestor.get_queryset(view=view).filter(pk=view.kwargs[edge.get_pk_name()])
    if outer is not None:
        queryset = queryset.filter(**{f"{ancestor.parent.get_attribute()}__pk": outer.pk})
    obj = queryset.first()
    if obj is None:
        raise Http404(f"{ancestor.model._meta.verbose_name} not found")
    return obj


def _permission_name(viewset: ViewSet, ancestor: ViewSet, key: str, view_key: str | None) -> str:
    permission = ancestor.permissions.get(key)
    if not permission:
        raise ImproperlyConfigured(
            f"ViewSet {viewset.name!r} view {view_key!r}: ancestor permission key {key!r} is not in the "
            f"permission map of ancestor ViewSet {ancestor.name!r}"
        )
    return permission


def _authorize_ancestors(view: CrudView):
    """Authorize the ancestors of a nested request; see the module docstring for the order.

    Returns None to continue the request or a response to return; raises Http404 / PermissionDenied /
    ImproperlyConfigured. Stores the request-local ``_cv_ancestor_state`` on success.
    """
    viewset = view.cv_viewset
    if viewset is None or viewset.parent is None:
        return None
    pair = _operation_requirements(type(view))
    if pair is None:
        return None
    chain = _walk_ancestors(viewset)
    selected = _selected_gates(viewset, chain)

    user = view.request.user
    if selected:
        if not user.is_authenticated:
            return _deny_anonymous(view)
        if not user.is_active:
            raise PermissionDenied

    resolved: list[Model] = []
    outer = None
    for index in reversed(range(len(chain))):
        edge, ancestor = chain[index]
        obj = _resolve_ancestor(view, edge, ancestor, outer)
        if index in selected:
            key = pair.nearest if selected[index] == "nearest" else pair.higher
            permission = _permission_name(viewset, ancestor, key, view.cv_key)
            if not ancestor._ancestor_has_permission(user, permission, obj, view=view):
                raise PermissionDenied
        resolved.insert(0, obj)
        outer = obj
    view._cv_ancestor_state = _AncestorState(objects=tuple(resolved))
    return None


def _resolved_parent(view: CrudView) -> Model | None:
    """The immediate parent resolved by a successful guard on this request, or None."""
    state = getattr(view, "_cv_ancestor_state", None)
    return state.parent if state is not None else None
