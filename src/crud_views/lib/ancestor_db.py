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
  protection hooks and deletion.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.core.exceptions import ImproperlyConfigured
from django.db import DEFAULT_DB_ALIAS
from django.db.models import QuerySet

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
