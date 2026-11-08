"""Ancestry metadata of nested ViewSets: the bounded parent walk, relationship validation and operation pairs.

Everything here reads only declarations and model metadata: no request, user, object, permission or ContentType,
and no database access. Failures raise ``ImproperlyConfigured`` naming the affected ViewSet; ``crud_views.checks``
reports the same rules as system-check errors (E320 structure/relationships, E321 action declarations).

- ``walk_ancestors()`` is the one parent walk. Every other walk over ``ViewSet.parent`` uses it, so a cycle or an
  unresolved parent name fails at once instead of looping or failing halfway.
- ``validate_relationships()`` checks that each ORM edge of the chain is a declared, unambiguous relation.
- ``operation_permissions()`` maps an endpoint to its ancestor pair: an exact ``ancestor_policy.actions`` entry,
  else the Read/Write pair of a finite set of shipped view families, else a configuration error.
"""

import sys
from typing import TYPE_CHECKING

from django.core.exceptions import FieldDoesNotExist, ImproperlyConfigured
from django.db.models import ForeignObjectRel

from ..ancestor_policy import AncestorPermissions
from ..exceptions import ViewSetNotFoundError
from ..settings import crud_views_settings

if TYPE_CHECKING:
    from ..view import CrudView
    from . import ViewSet
    from .parentviewset import ParentViewSet


def walk_ancestors(viewset: "ViewSet") -> tuple["ParentViewSet", ...]:
    """The ``ParentViewSet`` declarations of ``viewset``'s ancestors, nearest first.

    The whole chain is resolved before returning: a parent name that is not registered or a cycle (including one
    through ``viewset`` itself) raises ``ImproperlyConfigured`` naming the walked chain. A child may be declared
    before its parent; the reference only has to resolve once ancestry is needed (URLs, checks, requests).
    """
    chain: list[ParentViewSet] = []
    names = [viewset.name]
    parent = viewset.parent
    while parent is not None:
        if parent.name in names:
            path = " → ".join([*names, parent.name])
            raise ImproperlyConfigured(f"ViewSet {viewset.name!r} has a cycle in its parent chain: {path}")
        try:
            parent_viewset = parent.viewset
        except ViewSetNotFoundError:
            path = " → ".join([*names, parent.name])
            raise ImproperlyConfigured(
                f"parent ViewSet {parent.name!r} of ViewSet {names[-1]!r} is not registered "
                f"(parent chain of {viewset.name!r}: {path})"
            ) from None
        names.append(parent.name)
        chain.append(parent)
        parent = parent_viewset.parent
    return tuple(chain)


def _forward_m2m(field):
    """The declaring ``ManyToManyField`` of either end of a many-to-many relation."""
    return field.field if isinstance(field, ForeignObjectRel) else field


def parent_relationship_problem(viewset: "ViewSet") -> str | None:
    """Why the edge from ``viewset`` to its immediate parent is unsupported, or ``None``.

    Requires a resolvable parent. Supported edges:

    - a Resource child (a leaf): no ORM relation is needed, the application scopes the Resource by URL kwargs;
    - a forward ``ForeignKey``/``OneToOneField`` ``attribute`` to the parent model, without
      ``many_to_many_through_attribute``;
    - a many-to-many ``attribute`` (either end) to the parent model; a declared ``many_to_many_through_attribute``
      must be the opposite end of the same relation on the parent model.

    A Resource parent is never supported (Resources are leaves); ``ViewSet.checks()`` reports it as E261.
    """
    parent = viewset.parent
    parent_viewset = parent.viewset
    if parent_viewset.is_resource:
        return (
            f"parent ViewSet {parent.name!r} of ViewSet {viewset.name!r} is Resource-based — Resources can only be "
            f"leaves in the nesting hierarchy"
        )
    if viewset.is_resource:
        return None

    model, parent_model = viewset.model, parent_viewset.model
    attribute = parent.get_attribute()
    through = parent.many_to_many_through_attribute
    where = f"ViewSet {viewset.name!r}: ParentViewSet(name={parent.name!r})"
    try:
        field = model._meta.get_field(attribute)
    except FieldDoesNotExist:
        return f"{where} attribute {attribute!r} is no field of {model.__name__}"
    if not field.is_relation or field.related_model is None:
        return f"{where} attribute {attribute!r} of {model.__name__} is no relation to {parent_model.__name__}"
    if not issubclass(parent_model, field.related_model):
        return (
            f"{where} attribute {attribute!r} of {model.__name__} relates to {field.related_model.__name__}, "
            f"not to the parent model {parent_model.__name__}"
        )

    if field.many_to_many:
        if through is None:
            return None  # the child-side field alone determines the relation to the parent model
        try:
            parent_field = parent_model._meta.get_field(through)
        except FieldDoesNotExist:
            return f"{where} many_to_many_through_attribute {through!r} is no field of {parent_model.__name__}"
        if (
            not parent_field.many_to_many
            or parent_field is field
            or _forward_m2m(parent_field) is not _forward_m2m(field)
        ):
            return (
                f"{where} many_to_many_through_attribute {through!r} of {parent_model.__name__} is not the other end "
                f"of the many-to-many relation {attribute!r} of {model.__name__}"
            )
        return None

    if isinstance(field, ForeignObjectRel) or not (field.many_to_one or field.one_to_one):
        return (
            f"{where} attribute {attribute!r} of {model.__name__} is not a ForeignKey/OneToOneField or a "
            f"many-to-many relation to {parent_model.__name__}"
        )
    if through is not None:
        return (
            f"{where} many_to_many_through_attribute {through!r} is set, but attribute {attribute!r} is a "
            f"ForeignKey/OneToOneField, not a many-to-many relation"
        )
    return None


def validate_relationships(viewset: "ViewSet") -> None:
    """Validate the structure and every declared relationship of ``viewset``'s ancestor chain."""
    child = viewset
    for parent in walk_ancestors(viewset):
        problem = parent_relationship_problem(child)
        if problem is not None:
            if child is not viewset:
                problem = f"{problem} (ancestor of ViewSet {viewset.name!r})"
            raise ImproperlyConfigured(problem)
        child = parent.viewset


def _operation_family(view_class: type["CrudView"]) -> str | None:
    """``"read"``/``"write"`` for the shipped families, ``None`` for an endpoint needing an action entry.

    The order matters: CustomForm (and Workflow) inherit DetailView, the ordered actions inherit ActionView.
    """
    from ..views import (
        ActionView,
        CardListView,
        CreateView,
        DeleteView,
        DetailView,
        ListView,
        OrderedDownView,
        OrderedUpView,
        RedirectChildView,
        UpdateView,
    )
    from ..views.form import CustomFormNoObjectView, CustomFormView
    from ..views.manage import ManageView

    if issubclass(view_class, (CustomFormView, CustomFormNoObjectView)):
        return None
    if issubclass(view_class, (OrderedUpView, OrderedDownView)):
        return "write"
    if issubclass(view_class, ActionView):
        return None
    if issubclass(view_class, (CreateView, UpdateView, DeleteView)):
        return "write"
    # the polymorphic type selection is no CreateView; its module is loaded whenever a subclass exists
    create_select = sys.modules.get("crud_views_polymorphic.lib.create_select")
    if create_select is not None and issubclass(view_class, create_select.PolymorphicCreateSelectView):
        return "write"
    if issubclass(view_class, (ListView, CardListView, DetailView, RedirectChildView, ManageView)):
        return "read"
    return None


def operation_permissions(view_class: type["CrudView"]) -> AncestorPermissions | None:
    """The ancestor pair a request to ``view_class`` requires; ``None`` for a top-level endpoint.

    An exact entry of the ViewSet's ``ancestor_policy.actions`` under the view's registered key wins; otherwise the
    ViewSet's (or the global) Read or Write pair of the view's family applies. A nested endpoint outside the shipped
    families without an entry raises ``ImproperlyConfigured``.
    """
    viewset = view_class.cv_viewset
    if viewset.parent is None:
        return None
    policy = viewset.ancestor_policy
    key = view_class.cv_key  # the key CrudViewMetaClass registered the view under
    if key in policy.actions:
        return policy.actions[key]
    family = _operation_family(view_class)
    if family == "read":
        return policy.read if policy.read is not None else crud_views_settings.ancestor_read_permissions
    if family == "write":
        return policy.write if policy.write is not None else crud_views_settings.ancestor_write_permissions
    raise ImproperlyConfigured(_missing_action_message(viewset, key, view_class))


def _missing_action_message(viewset: "ViewSet", key: str, view_class: type["CrudView"]) -> str:
    return (
        f"nested view {key!r} ({view_class.__name__}) of ViewSet {viewset.name!r} has no built-in ancestor "
        f"operation: declare ancestor_policy.actions[{key!r}] = AncestorPermissions(nearest=..., higher=...)"
    )


def registered_action_problems(viewset: "ViewSet") -> list[str]:
    """Action-declaration problems of a nested ViewSet, judged against its literal registrations.

    Run it once registration is complete: an entry may precede the definition of its view class.
    """
    if viewset.parent is None:
        return []
    views = viewset.get_all_views()  # literal keys: no list → card navigation alias
    actions = viewset.ancestor_policy.actions
    problems = [
        f"ancestor_policy.actions[{key!r}] of ViewSet {viewset.name!r} names no registered view "
        f"(registered: {', '.join(sorted(views)) or 'none'})"
        for key in actions
        if key not in views
    ]
    problems.extend(
        _missing_action_message(viewset, key, view_class)
        for key, view_class in views.items()
        if key not in actions and _operation_family(view_class) is None
    )
    return problems


def validate_registered_actions(viewset: "ViewSet") -> None:
    """Raise ``ImproperlyConfigured`` listing every action-declaration problem of ``viewset``."""
    problems = registered_action_problems(viewset)
    if problems:
        raise ImproperlyConfigured("; ".join(problems))
