"""
Default-database boundary of nested ViewSet requests (phase 06.18, ANCE-06).

Wave one supports only the ``default`` database for a nested request's ORM data: its ancestor lookups, the
child's own querysets and objects, and the child's writes. The helpers below look at the database a consumer has
*already* selected — an explicit ``.using()`` (which wins over routers), a router answer, an instance hint, or a
view's ``cv_get_db_alias()`` override — right before that consumer touches the database, and raise
``ImproperlyConfigured`` for anything but ``default``. They never select, strip or replace an alias and never retry
on another database. Top-level ViewSets and the application-owned loading of Resource leaves are not checked.

The reached consumers that call them:

* ``ancestors._resolve_ancestor`` — every ancestor queryset, before it is evaluated;
* ``CrudView.get_object`` / ``CrudView.get_context_data`` — the child queryset before the object lookup, and the
  list collection before pagination and tables read it;
* ``DeleteView.cv_get_delete_db_alias`` — the delete alias, newly selected or pinned, before preview collection,
  protection hooks and deletion;
* ``CrudView._cv_check_nested_write`` (``_check_nested_write``) — the write alias, the written instance and its
  parent attachments: in each POST after the object (or form instance) is resolved and before the first hook,
  and again at the write wrapper (``cv_form_valid_process``) for callers that drive it directly. A guard only in
  ``cv_get_atomic()`` would not do: hooks run before it, and ``cv_atomic = False`` selects no alias there.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

from django.core.exceptions import ImproperlyConfigured
from django.db import DEFAULT_DB_ALIAS, router
from django.db.models import Model, QuerySet

if TYPE_CHECKING:
    from crud_views.lib.view import CrudView


def _is_nested_orm(view: CrudView) -> bool:
    """A request to a nested ORM ViewSet (the scope of the default-database boundary)."""
    viewset = getattr(view, "cv_viewset", None)
    return viewset is not None and viewset.parent is not None and not viewset.is_resource


def _require_default_alias(alias, *, view: CrudView, operation: str) -> None:
    """``alias`` must be ``default``; otherwise ``ImproperlyConfigured`` naming the ViewSet, view and operation."""
    if alias == DEFAULT_DB_ALIAS:
        return
    raise ImproperlyConfigured(
        f"ViewSet {view.cv_viewset.name!r} view {view.cv_key!r}: {operation} selected database {alias!r}; "
        f"nested ViewSets support only the {DEFAULT_DB_ALIAS!r} database (the selection is not rerouted)"
    )


def _check_nested_queryset(view: CrudView, queryset):
    """A nested ORM child queryset must read ``default``; returned unchanged. ``queryset.db`` is the effective
    alias Django will query (explicit ``.using()`` first, else the router with the queryset's hints) and is read
    without evaluating anything. Top-level views and non-queryset collections pass unchanged."""
    if _is_nested_orm(view) and isinstance(queryset, QuerySet):
        _require_default_alias(queryset.db, view=view, operation=f"{queryset.model.__name__} queryset")
    return queryset


def _check_nested_alias(view: CrudView, alias, *, operation: str):
    """A database alias a nested ORM view selected (e.g. its delete alias) must be ``default``; returned
    unchanged. Top-level views pass unchanged."""
    if _is_nested_orm(view):
        _require_default_alias(alias, view=view, operation=operation)
    return alias


def _check_nested_write(view: CrudView, *, instance: Model | None = None, related: Iterable = ()) -> None:
    """Default-database boundary of a nested write, checked before any hook or write runs.

    * the view's selected write alias (``view._cv_write_alias()``: transaction and commit-callback alias);
    * ``instance`` — the row the write saves or deletes: its database if loaded, and the alias its own
      ``save()`` would route to (``router.db_for_write(model, instance=instance)``);
    * ``related`` — ``(model, hint)`` attachment routes, e.g. the parent FK assignment (``(child model,
      parent)``) or the M2M through write (``(through model, parent)``), exactly as Django routes them.

    Every value is recomputed on each call (no success cache), so a hint that changed is seen. Nothing is
    rerouted. Top-level views return immediately.
    """
    if not _is_nested_orm(view):
        return
    _require_default_alias(view._cv_write_alias(), view=view, operation="write transaction alias")
    if instance is not None:
        name = type(instance).__name__
        if instance._state.db is not None:
            _require_default_alias(instance._state.db, view=view, operation=f"{name} instance database")
        route = router.db_for_write(type(instance), instance=instance)
        _require_default_alias(route, view=view, operation=f"{name} write route")
    for model, hint in related:
        if hint._state.db is not None:
            _require_default_alias(hint._state.db, view=view, operation=f"{type(hint).__name__} attachment database")
        route = router.db_for_write(model, instance=hint)
        _require_default_alias(route, view=view, operation=f"{model.__name__} attachment route")
