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

from django.core.exceptions import FieldDoesNotExist, ImproperlyConfigured, PermissionDenied
from django.http import Http404

from crud_views.lib.ancestor_policy import AncestorPermissions
from crud_views.lib.exceptions import ViewSetNotFoundError
from crud_views.lib.settings import crud_views_settings

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


class _AncestryError(ImproperlyConfigured):
    """A declared ancestry that cannot be walked or expressed. ``kind`` is one of ``"missing"``, ``"cycle"``,
    ``"resource_parent"`` or ``"relation"`` (the system check maps kinds to its messages)."""

    def __init__(self, message: str, *, kind: str):
        super().__init__(message)
        self.kind = kind


def _walk_ancestors(viewset: ViewSet, *, first_only: bool = False) -> list[tuple[ParentViewSet, ViewSet]]:
    """Declared ancestry of ``viewset``, nearest first, as ``(edge, ancestor)`` pairs.

    ``edge`` is the ``ParentViewSet`` declaration pointing at ``ancestor`` (its URL PK name and the relation
    attribute on the model below it). The walk is bounded by the visited ViewSet names: a missing or repeated
    ViewSet raises ``ImproperlyConfigured`` naming the chain instead of looping. ``first_only`` stops after the
    immediate edge. It reads only the registry and declarations — no database.

    Every supported ancestry walk (URL construction, the parent URL-argument/attribute helpers, the scoped
    queryset and the request guard) goes through this function.
    """
    chain: list[tuple[ParentViewSet, ViewSet]] = []
    seen = [viewset.name]
    edge = viewset.parent
    while edge is not None:
        try:
            ancestor = edge.viewset
        except ViewSetNotFoundError as exc:
            raise _AncestryError(
                f"ViewSet {viewset.name!r}: parent ViewSet {edge.name!r} is not registered "
                f"(ancestry {' -> '.join(seen)} -> {edge.name})",
                kind="missing",
            ) from exc
        if ancestor.name in seen:
            raise _AncestryError(
                f"ViewSet {viewset.name!r}: ancestry cycle {' -> '.join(seen)} -> {ancestor.name}", kind="cycle"
            )
        seen.append(ancestor.name)
        chain.append((edge, ancestor))
        if first_only:
            break
        edge = ancestor.parent
    return chain


def _validate_ancestor_structure(viewset: ViewSet, *, relations: bool = True) -> list[tuple[ParentViewSet, ViewSet]]:
    """The bounded ancestry of ``viewset`` (see ``_walk_ancestors``) after validating every declared edge.

    A Resource may only be the requested leaf: a Resource ancestor is rejected. With ``relations`` each ORM edge
    must name one supported relation on the model below it (see ``_validate_relationship``); the edge below a
    Resource leaf is application-scoped and not inspected. Model metadata only — no database, no permission
    vocabulary. URL construction passes ``relations=False``: it needs a finite, Resource-free chain, while
    relationships are enforced by the system check and by the request guard before any lookup.
    """
    chain = _walk_ancestors(viewset)
    below = viewset
    for edge, ancestor in chain:
        if ancestor.is_resource:
            names = " -> ".join([viewset.name, *(a.name for _, a in chain)])
            raise _AncestryError(
                f"ViewSet {viewset.name!r}: ancestor ViewSet {ancestor.name!r} is Resource-based — a Resource can "
                f"only be the requested leaf (ancestry {names})",
                kind="resource_parent",
            )
        if relations and not below.is_resource:
            _validate_relationship(viewset, below, edge, ancestor)
        below = ancestor
    return chain


def _validate_relationship(viewset: ViewSet, below: ViewSet, edge: ParentViewSet, ancestor: ViewSet) -> None:
    """``edge`` must name one relation on ``below.model`` that points to ``ancestor.model``.

    Supported: a forward FK/one-to-one, a reverse relation or a many-to-many (forward or reverse), queried as
    ``<attribute>__pk``. A declared ``many_to_many_through_attribute`` must be a many-to-many relation on the
    ancestor model pointing back to ``below.model`` (the create attachment uses it). Rejected: a missing field,
    a non-relational or generic field, a relation to another model and a ``__`` relation path.
    """
    model, target = below.model, ancestor.model
    attribute = edge.get_attribute()
    where = f"ViewSet {viewset.name!r}: relation {below.name!r} -> parent ViewSet {ancestor.name!r}"
    if "__" in attribute:
        raise _AncestryError(
            f"{where}: a relation path ({attribute!r}) is not supported; set ParentViewSet(attribute=...) to the "
            f"single field of {model.__name__} pointing at {target.__name__}",
            kind="relation",
        )
    try:
        field = model._meta.get_field(attribute)
    except FieldDoesNotExist:
        raise _AncestryError(
            f"{where}: {model.__name__} has no field {attribute!r}; set ParentViewSet(attribute=...) to the field "
            f"of {model.__name__} pointing at {target.__name__}",
            kind="relation",
        ) from None
    related = getattr(field, "related_model", None)
    if not field.is_relation or not isinstance(related, type):
        raise _AncestryError(
            f"{where}: {model.__name__} field {attribute!r} is not a relation to {target.__name__} "
            f"(generic relations are not supported)",
            kind="relation",
        )
    if not issubclass(target, related):
        raise _AncestryError(
            f"{where}: {model.__name__}.{attribute} points to {related.__name__}, not {target.__name__}",
            kind="relation",
        )
    through = edge.many_to_many_through_attribute
    if through is None:
        return
    if not field.many_to_many:
        raise _AncestryError(
            f"{where}: many_to_many_through_attribute requires attribute {attribute!r} to be a many-to-many "
            f"relation, but {model.__name__}.{attribute} is not",
            kind="relation",
        )
    try:
        back = target._meta.get_field(through)
    except FieldDoesNotExist:
        raise _AncestryError(
            f"{where}: {target.__name__} has no field {through!r} (many_to_many_through_attribute)", kind="relation"
        ) from None
    back_related = getattr(back, "related_model", None)
    if not back.many_to_many or not isinstance(back_related, type) or not issubclass(model, back_related):
        raise _AncestryError(
            f"{where}: many_to_many_through_attribute {through!r} of {target.__name__} is not a many-to-many "
            f"relation to {model.__name__}",
            kind="relation",
        )


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
        return policy.read or crud_views_settings.ancestor_read_permissions
    if family == "write":
        return policy.write or crud_views_settings.ancestor_write_permissions
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
        cascade = crud_views_settings.ancestor_permission_cascade
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
    # static validation first: structure and relationships, before any actor, object or permission work
    chain = _validate_ancestor_structure(viewset)
    pair = _operation_requirements(type(view))
    if pair is None:
        return None
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
