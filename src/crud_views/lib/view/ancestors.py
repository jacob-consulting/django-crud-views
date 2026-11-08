"""Request enforcement of ancestor authorization for nested ViewSets.

``authorize_ancestors(view)`` runs once per nested request, before any endpoint-local work: the dispatch bridges call
``CrudView._cv_authorize_ancestors()``, which calls it. It works in this order and stops at the first failure:

1. Static: the ancestor chain, its relationships and the operation's ``AncestorPermissions`` pair; the gates are
   selected from configuration only (providers and cascade depth). No database access.
2. Actor: with a protected (selected) ancestor, an anonymous actor gets the endpoint's no-permission response (a login
   redirect by default) and an inactive one 403. With all-``none`` ancestry only the endpoint's own early actor rule
   applies (``CrudView._cv_ancestor_actor_response()``).
3. Outermost ancestor first, one level at a time: resolve the URL pk through that ancestor ViewSet's
   ``get_queryset(view=<requested view>)`` on the default database (missing/excluded → 404), validate the declared
   relationship to the level above (mismatch → 404), then evaluate the level's gate if it is selected (denial → 403).

On success the resolved objects are stored on the view instance (``_cv_ancestor_objects``, ViewSet name → object) so
``cv_get_parent_object()`` and the create/state helpers reuse the same identities. Nothing outlives the request.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.db.models import ForeignObjectRel
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404

from ..ancestor_databases import require_default_database, validate_authorization_databases
from ..settings import crud_views_settings
from ..viewset.ancestry import operation_permissions, validate_relationships, walk_ancestors

if TYPE_CHECKING:
    from django.db.models import Model

    from ..ancestor_policy import AncestorPermissions
    from ..viewset import ViewSet
    from ..viewset.parentviewset import ParentViewSet
    from .base import CrudView


def authorize_ancestors(view: CrudView) -> HttpResponse | None:
    """Authorize the ancestors of a nested request; a denial response, ``None`` on success.

    Raises ``PermissionDenied`` (403), ``Http404`` or ``ImproperlyConfigured`` for the reached failure.
    """
    viewset = view.cv_viewset
    chain = walk_ancestors(viewset)  # nearest first
    validate_relationships(viewset)
    gates = selected_gates(viewset, chain, operation_permissions(type(view)))

    response = _actor_response(view, protected=bool(gates))
    if response is not None:
        return response

    resolved: dict[str, Model] = {}
    outer = None
    for index in reversed(range(len(chain))):  # outermost first
        ancestor = chain[index].viewset
        obj = _resolve(view, chain[index], ancestor)
        if outer is not None and not _related(obj, ancestor.parent, outer):
            raise Http404(f"{ancestor.model.__name__} does not belong to the {outer._meta.model_name} in the URL")
        if index in gates:
            _check_gate(view, ancestor, obj, gates[index])
        resolved[ancestor.name] = obj
        outer = obj
    view._cv_ancestor_objects = resolved
    return None


def selected_gates(viewset: ViewSet, chain: tuple[ParentViewSet, ...], pair: AncestorPermissions) -> dict[int, str]:
    """Chain index → required permission key of every ancestor whose gate is evaluated.

    The nearest protected ancestor (provider other than ``none``) requires ``pair.nearest``; with cascade, every
    farther protected ancestor requires ``pair.higher``. Only the requested ViewSet's cascade (or the global
    setting) decides the depth.
    """
    cascade = viewset.ancestor_policy.cascade
    if cascade is None:
        cascade = crud_views_settings.ancestor_permission_cascade
    gates: dict[int, str] = {}
    for index, parent in enumerate(chain):
        if parent.viewset._ancestor_provider() == "none":
            continue
        if not gates:
            gates[index] = pair.nearest
        elif cascade:
            gates[index] = pair.higher
        else:
            break
    return gates


def _actor_response(view: CrudView, *, protected: bool) -> HttpResponse | None:
    """The early actor decision; never loads a child or evaluates action state."""
    if not protected:
        return view._cv_ancestor_actor_response()
    user = view.request.user
    if user.is_authenticated:
        if not user.is_active:
            raise PermissionDenied
        return None
    response = view._cv_ancestor_actor_response()
    if response is not None:
        return response
    if hasattr(view, "handle_no_permission"):  # AccessMixin: honors raise_exception, login URL and redirect field
        return view.handle_no_permission()
    return redirect_to_login(view.request.get_full_path())


def _resolve(view: CrudView, parent: ParentViewSet, ancestor: ViewSet) -> Model:
    """The ancestor object of the URL, visible through the ancestor ViewSet's queryset for the requested view."""
    queryset = ancestor.get_queryset(view=view)
    require_default_database(queryset.db, context=f"ancestor ViewSet {ancestor.name!r} of {view.cv_viewset.name!r}")
    return get_object_or_404(queryset, pk=view.kwargs[parent.get_pk_name()])


def _related(obj: Model, parent: ParentViewSet, parent_obj: Model) -> bool:
    """Whether ``obj`` belongs to ``parent_obj`` through the declared relationship (FK/one-to-one or M2M).

    ``ParentViewSet.attribute`` is a field / query name (what ``_meta.get_field()`` takes). A reverse many-to-many
    end is reached on the instance through its accessor, which differs from the query name without ``related_name``
    (``user`` / ``user_set``) or with a separate ``related_query_name``. FK/one-to-one compares values, no query.
    """
    field = type(obj)._meta.get_field(parent.get_attribute())
    if field.many_to_many:
        accessor = field.get_accessor_name() if isinstance(field, ForeignObjectRel) else field.name
        return getattr(obj, accessor).filter(pk=parent_obj.pk).exists()
    return getattr(obj, field.attname) == getattr(parent_obj, field.target_field.attname)


def _check_gate(view: CrudView, ancestor: ViewSet, obj: Model, key: str) -> None:
    """Resolve ``key`` in the ancestor's own permission map and evaluate its provider; deny with 403.

    The auth records this provider reads are validated first, at this reached gate (an outer denial never validates
    a deeper gate's routes); a nondefault route is a configuration error, never a denial from another database.
    """
    _validate_gate_databases(view.request.user, ancestor)
    permission = _permission(type(view), ancestor, key)
    if not ancestor._ancestor_has_permission(view.request.user, obj, permission):
        raise PermissionDenied


def _validate_gate_databases(user, ancestor: ViewSet) -> None:
    validate_authorization_databases(user, provider=ancestor._ancestor_provider(), model=ancestor.model)


def _permission(view_class: type[CrudView], ancestor: ViewSet, key: str) -> str:
    """The fully qualified permission of ``key`` in the ancestor's own map; a missing key is a configuration error."""
    permission = ancestor.permissions.get(key)
    if permission is None:
        raise ImproperlyConfigured(
            f"ancestor ViewSet {ancestor.name!r} has no permission {key!r}, required by view {view_class.cv_key!r} "
            f"of ViewSet {view_class.cv_viewset.name!r} (available: {', '.join(ancestor.permissions) or 'none'})"
        )
    return permission


def immediate_parent_has_permission(view_class: type[CrudView], user, parent_obj: Model | None) -> bool:
    """Whether ``user`` passes the immediate parent's gate for a request to ``view_class`` (rendering helpers).

    The target's nearest requirement, resolved in the immediate parent's permission map and evaluated by that
    parent's provider (and its own ancestor fallback). A ``none`` parent returns True without walking farther: the
    request itself still authorizes the whole chain. Missing parent context (``None``) returns False; the caller
    never invents a parent. Actor, state and custom denials stay with the callers.

    The configuration is resolved first, so an undeclared nested custom endpoint or a requirement key missing from
    the parent's permission map raises ``ImproperlyConfigured`` whatever the parent input or provider.
    """
    ancestor = view_class.cv_viewset.parent.viewset
    key = operation_permissions(view_class).nearest
    protected = ancestor._ancestor_provider() != "none"
    permission = _permission(view_class, ancestor, key) if protected else None
    if parent_obj is None:
        return False
    if not protected:
        return True
    _validate_gate_databases(user, ancestor)
    return ancestor._ancestor_has_permission(user, parent_obj, permission)
