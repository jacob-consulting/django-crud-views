"""
Shared ancestor authorization for nested ViewSet requests (phase 06.18).

One request engine, ``_authorize_ancestors(view)``, runs before an endpoint's own work:

1. Top-level requests return immediately: no ancestor work at all.
2. Static validation and selection, without database access: the declared ancestry and its relationships, the
   action declarations, the requested operation's permission pair, each ancestor's effective provider and the
   levels selected for a permission gate (full cascade: every protected ancestor; nearest-only: the nearest
   protected one).
3. Actor admission, before any ancestor lookup, through the endpoint's private
   ``_cv_ancestor_actor_response(protected=...)`` adapter. Protected ancestry (a gate is selected): anonymous
   actors get the endpoint's anonymous response (login redirect by default; Guardian keeps its configured
   403/404), inactive authenticated actors 403. All-none ancestry: only the endpoint's own early admission
   rule applies (core permission-required views ask their model permission, plain views admit everybody,
   Guardian keeps its explicit actor rules, manage its settings); it never calls a child- or state-loading
   ``has_permission()``.
4. Outermost inward, each ancestor is resolved through its own ViewSet queryset (called with the real child
   view), constrained to the URL PK and to the already resolved outer ancestor; missing → 404. A selected
   level's gate is checked immediately, before the next deeper lookup; denial → 403.
5. On success the resolved chain is stored on the view instance (request-local) and the request continues
   through its existing path; ``cv_get_parent_object()`` reuses the resolved immediate parent.
6. The ORM child itself is checked against that immediate structural parent where it is consumed, so a child
   ``get_queryset`` override that omits the parent filter cannot reach another parent's data:
   ``CrudView.get_object`` validates a reached object (``_validate_child_parent``, 404 on mismatch, before
   state hooks, forms and writes) and list views scope the collection they render
   (``_scope_child_queryset``, applied to ``object_list`` in ``CrudView.get_context_data``). Resource leaves
   are skipped: their loading and membership stay application-owned (``cv_get_items`` / ``cv_get_item``).

Every shipped composition reaches the engine before its own local work: plain views through
``CrudView.dispatch``, permission-required views through ``CrudViewPermissionRequiredMixin.dispatch`` (before
Django's ``PermissionRequiredMixin`` runs the state-loading ``has_permission()``), Guardian views through
``GuardianParentPermissionMixin.dispatch`` and manage views through ``ManageView.dispatch``. The engine runs
once per request: a later bridge reuses the stored result.

Operations come from a finite family table (``_operation_family``); an endpoint outside it — a generic action,
custom form, workflow or other custom view — needs an exact ``actions`` entry when nested, otherwise the request
fails with ``ImproperlyConfigured`` (and the system check reports viewset.E268).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from django.core.exceptions import FieldDoesNotExist, ImproperlyConfigured, PermissionDenied
from django.db.models import QuerySet
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


_READ = "read"
_WRITE = "write"


def _family_table() -> tuple[tuple[type, str], ...]:
    """The finite shipped endpoint families (core classes only, imported lazily). Rich ObjectDetail and the
    polymorphic detail/create/update/delete views inherit the core Detail/Create/Update/Delete classes; the
    polymorphic type selector carries the inherited ``_cv_ancestor_operation`` marker instead, so core never
    imports an optional package. Django's generic DetailView is deliberately absent: custom forms and
    workflow inherit it."""
    from crud_views.lib.views.action_ordered import OrderedDownView, OrderedUpView
    from crud_views.lib.views.card import CardListView
    from crud_views.lib.views.child import RedirectChildView
    from crud_views.lib.views.create import CreateView
    from crud_views.lib.views.delete import DeleteView
    from crud_views.lib.views.detail import DetailView
    from crud_views.lib.views.list import ListView
    from crud_views.lib.views.manage import ManageView
    from crud_views.lib.views.update import UpdateView

    return (
        (ListView, _READ),
        (CardListView, _READ),
        (DetailView, _READ),
        (RedirectChildView, _READ),
        (ManageView, _READ),
        (CreateView, _WRITE),
        (UpdateView, _WRITE),
        (DeleteView, _WRITE),
        (OrderedUpView, _WRITE),
        (OrderedDownView, _WRITE),
    )


def _operation_family(view_class: type) -> str | None:
    """'read' / 'write' for a shipped family (including permission variants and ordinary subclasses), else
    None. Decided by class only — never by the registered key, the HTTP method or the local permission."""
    marker = getattr(view_class, "_cv_ancestor_operation", None)
    if marker is not None:
        return marker
    for base, family in _family_table():
        if issubclass(view_class, base):
            return family
    return None


def _registered_key(view_class: type[CrudView]) -> str:
    """The key ``view_class`` is literally registered under at its ViewSet (else its ``cv_key``)."""
    for key, registered in view_class.cv_viewset.get_all_views().items():
        if registered is view_class:
            return key
    return view_class.cv_key


def _missing_action_message(viewset: ViewSet, key: str, view_class: type) -> str:
    return (
        f"ViewSet {viewset.name!r} view {key!r} ({view_class.__name__}) is a nested endpoint outside the "
        f"built-in Read/Write families: declare ancestor_policy.actions[{key!r}] = "
        f"AncestorPermissions(nearest=..., higher=...) on ViewSet {viewset.name!r}"
    )


def _action_declaration_problems(viewset: ViewSet) -> list[tuple[str, str]]:
    """``(check id, message)`` for the action declarations of a nested ViewSet, from its completed registry:

    * ``E267``: an ``actions`` key that is not literally registered (Card's ``list`` navigation alias is no
      registration);
    * ``E268``: a registered unclassified endpoint without its exact ``actions`` entry.

    Top-level ViewSets have none (construction rejects their nonempty ``actions``). No database.
    """
    if viewset.parent is None:
        return []
    policy = viewset.ancestor_policy
    problems = []
    for key in policy.actions:
        if viewset.is_view_registered(key):
            continue
        hint = ""
        if key == "list" and viewset.is_view_registered("card"):
            hint = "; the 'card' endpoint answers list navigation but is registered as 'card': use actions['card']"
        registered = ", ".join(repr(k) for k in viewset.get_all_views()) or "none"
        problems.append(
            (
                "E267",
                f"ViewSet {viewset.name!r}: ancestor_policy.actions[{key!r}] names no registered endpoint "
                f"(registered: {registered}){hint}",
            )
        )
    for key, view_class in viewset.get_all_views().items():
        if key not in policy.actions and _operation_family(view_class) is None:
            problems.append(("E268", _missing_action_message(viewset, key, view_class)))
    return problems


def _validate_action_declarations(viewset: ViewSet) -> None:
    """Runtime guard: every ``actions`` key of a nested ViewSet is literally registered (``ImproperlyConfigured``
    otherwise). A missing entry is enforced per requested endpoint by ``_operation_requirements``."""
    for code, message in _action_declaration_problems(viewset):
        if code == "E267":
            raise ImproperlyConfigured(message)


def _operation_requirements(view_class: type[CrudView]) -> AncestorPermissions:
    """The permission pair required of ancestors for a nested request to ``view_class``.

    The exact ``actions`` entry for its registered key wins; otherwise the family's pair (the ViewSet's
    ``read``/``write`` override, else the global default). An unclassified endpoint without an entry is a
    configuration error in every cascade mode, even with all-none ancestry.
    """
    viewset = view_class.cv_viewset
    policy = viewset.ancestor_policy
    key = _registered_key(view_class)
    if key in policy.actions:
        return policy.actions[key]
    family = _operation_family(view_class)
    if family == _READ:
        return policy.read or crud_views_settings.ancestor_read_permissions
    if family == _WRITE:
        return policy.write or crud_views_settings.ancestor_write_permissions
    raise ImproperlyConfigured(_missing_action_message(viewset, key, view_class))


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


def _protected_actor_response(view: CrudView):
    """Actor rule of protected ancestry: anonymous → the endpoint's anonymous response, authenticated inactive
    (superusers included) → 403, else None. Used by the views' ``_cv_ancestor_actor_response`` adapters."""
    user = view.request.user
    if not user.is_authenticated:
        return _deny_anonymous(view)
    if not user.is_active:
        raise PermissionDenied
    return None


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
    # static validation first: structure, relationships and declarations, before any actor/object/permission work
    chain = _validate_ancestor_structure(viewset)
    _validate_action_declarations(viewset)
    pair = _operation_requirements(type(view))
    selected = _selected_gates(viewset, chain)

    # actor admission before any lookup; all-none ancestry keeps only the endpoint's own early rule
    response = view._cv_ancestor_actor_response(protected=bool(selected))
    if response is not None:
        return response

    user = view.request.user
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


def _resolved_ancestor(view: CrudView, name: str) -> Model | None:
    """The ancestor of ViewSet ``name`` resolved by a successful guard on this request, or None (no guard state,
    or ``name`` is not in the view's ancestry). Lets request helpers reuse the resolved identity."""
    state = getattr(view, "_cv_ancestor_state", None)
    if state is None:
        return None
    for (_, ancestor), obj in zip(_walk_ancestors(view.cv_viewset), state.objects, strict=True):
        if ancestor.name == name:
            return obj
    return None


def _child_edge(view: CrudView) -> tuple[str, Model] | None:
    """``(relation attribute, resolved immediate parent)`` of a guarded nested ORM request, else None (top-level,
    Resource leaf, or no successful guard on this view, e.g. outside a request)."""
    viewset = view.cv_viewset
    state = getattr(view, "_cv_ancestor_state", None)
    if state is None or viewset is None or viewset.parent is None or viewset.is_resource:
        return None
    return viewset.parent.get_attribute(), state.parent


def _validate_child_parent(view: CrudView, obj):
    """A reached ORM child object must belong to the request's resolved immediate parent; 404 otherwise.

    Called by ``CrudView.get_object``, so it runs wherever the object is consumed (the permission phase's
    ``cv_get_action_object`` included) and before state hooks, forms and writes. A forward FK/one-to-one compares
    the stored key, without a query; an M2M or reverse relation checks membership of this row with one query.
    An object of another model is application-owned and returned unchanged.
    """
    edge = _child_edge(view)
    model = view.cv_viewset.model if edge is not None else None
    if edge is None or not isinstance(obj, model):
        return obj
    attribute, parent = edge
    field = model._meta.get_field(attribute)
    if field.concrete and (field.many_to_one or field.one_to_one):
        belongs = getattr(obj, field.attname) == getattr(parent, field.target_field.attname)
    else:
        rows = type(obj)._base_manager.using(obj._state.db)
        belongs = rows.filter(pk=obj.pk, **{f"{attribute}__pk": parent.pk}).exists()
    if not belongs:
        raise Http404(f"{model._meta.verbose_name} not found")
    return obj


def _scope_child_queryset(view: CrudView, queryset):
    """A nested ORM child collection restricted to the request's resolved immediate parent.

    Applied where list views consume ``object_list`` (``CrudView.get_context_data``), so a ``get_queryset``
    override that omits the parent filter still renders only this parent's children. The default ViewSet
    queryset already carries the filter; adding it again does not change its rows. Anything that is not a
    queryset of the ViewSet's model (application-owned data) is returned unchanged.
    """
    edge = _child_edge(view)
    if edge is None or not isinstance(queryset, QuerySet) or not issubclass(queryset.model, view.cv_viewset.model):
        return queryset
    attribute, parent = edge
    return queryset.filter(**{f"{attribute}__pk": parent.pk})


def _same_row(a: Model, b: Model) -> bool:
    """The same database row: concrete model, primary key and database alias."""
    return type(a)._meta.concrete_model is type(b)._meta.concrete_model and a.pk == b.pk and a._state.db == b._state.db


def _immediate_parent_access(
    view_class: type[CrudView], user, parent_obj: Model | None, *, rendering_view=None
) -> bool:
    """Bounded parent gate for rendering and access helpers of a nested ``view_class``.

    Only the immediate structural parent is consulted: its own provider (and Guardian fallback) with the
    *nearest* key of ``view_class``'s operation pair. A farther ancestor is never evaluated and nothing is
    looked up — the request itself still runs the full ancestor guard, so a visible control can lead to a
    request denied higher up (first-wave UI limitation).

    * ``parent_obj`` None (context unavailable) → False.
    * Immediate parent provider ``"none"`` → True: only this gate is skipped; callers keep their actor, state
      and custom checks.
    * The rendering view's request-resolved parent replaces an equal ``parent_obj`` (same row), so helpers
      reuse the request identity.
    * A key missing from the parent's permission map, or a nested endpoint without operation requirements,
      raises ``ImproperlyConfigured``.
    """
    if parent_obj is None:
        return False
    viewset = view_class.cv_viewset
    ((_, parent_vs),) = _walk_ancestors(viewset, first_only=True)
    if rendering_view is not None:
        resolved = _resolved_parent(rendering_view)
        if resolved is not None and resolved is not parent_obj and _same_row(resolved, parent_obj):
            parent_obj = resolved
    if _effective_provider(parent_vs) == "none":
        return True
    key = _operation_requirements(view_class).nearest
    permission = _permission_name(viewset, parent_vs, key, _registered_key(view_class))
    return parent_vs._ancestor_has_permission(user, permission, parent_obj, view=rendering_view)
