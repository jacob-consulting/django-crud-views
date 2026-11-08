"""
Phase 06.18 plan 02 Task 1 — bounded ancestry walks and declared relationship structure.

Every supported ancestry walk (URL construction, the parent URL-argument/attribute helpers, the parent path,
the scoped queryset and the request guard) uses one bounded metadata walk. Self/two-node cycles and unresolved
parent references fail with an actionable ``ImproperlyConfigured`` naming the chain — through the actual
``urlpatterns`` and an actually imported URLconf, not only through checks — and without any database access.
A child declared before its parent stays valid and routes once the parent is registered.

Declared relationships are validated from Django model metadata only: forward FK/one-to-one, reverse relations
and declared many-to-many ``many_to_many_through_attribute`` pairs are supported; missing, non-relational,
mis-targeted, path-shaped or generic relations are rejected. A Resource may only be the requested leaf; a
Resource parent keeps its single existing ``viewset.E261`` check message and still fails URL/request use.

Isolation: every test builds uniquely named ViewSets and restores the registry and URL caches afterwards. The
``bounded`` fixture turns any runaway walk into a hard failure (a registry-lookup budget), so termination is
asserted from the raised error itself rather than from a timeout.
"""

from __future__ import annotations

import sys
import uuid
from types import SimpleNamespace

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.db import connections
from django.test import Client, override_settings
from django.urls import clear_url_caches, get_resolver, include, path, reverse

from crud_views.lib.viewset import _REGISTRY, _REGISTRY_LOCK, ParentViewSet, ViewSet
from tests.test1.app.models import Book, BookNote, Genre, Publisher
from tests.test1.app.resources import PublisherFile

# ── isolation and sentinels ─────────────────────────────────────────────────


class _UnboundedWalk(BaseException):  # deliberately not an Exception subclass: nothing may swallow it
    """Raised by the ``bounded`` fixture when a walk performs far more parent lookups than any real chain."""


@pytest.fixture
def sfx():
    return uuid.uuid4().hex[:8]


@pytest.fixture(autouse=True)
def registry():
    """Snapshot the ViewSet registry and restore it (and the URL caches) afterwards."""
    with _REGISTRY_LOCK:
        snapshot = dict(_REGISTRY)
    try:
        yield
    finally:
        with _REGISTRY_LOCK:
            _REGISTRY.clear()
            _REGISTRY.update(snapshot)
        clear_url_caches()


@pytest.fixture
def bounded(monkeypatch):
    """Budget the parent-registry lookups of one test; a runaway walk raises ``_UnboundedWalk``."""
    original = ParentViewSet.viewset
    budget = {"left": 200}

    def guarded(self):
        budget["left"] -= 1
        if budget["left"] < 0:
            raise _UnboundedWalk(f"unbounded ancestry walk through ParentViewSet({self.name!r})")
        return original.fget(self)

    monkeypatch.setattr(ParentViewSet, "viewset", property(guarded))
    return budget


@pytest.fixture
def no_db():
    """Fail on any SQL statement (on top of pytest-django's block for tests without database access)."""

    def blocker(execute, sql, params, many, context):
        raise AssertionError(f"structural ancestry work queried the database: {sql}")

    wrappers = [conn.execute_wrapper(blocker) for conn in connections.all()]
    for wrapper in wrappers:
        wrapper.__enter__()
    try:
        yield
    finally:
        for wrapper in reversed(wrappers):
            wrapper.__exit__(None, None, None)


def _viewset(model, name: str, parent: ParentViewSet | None = None, *, key_views=("list",)) -> ViewSet:
    """A ViewSet with plain views registered (urlpatterns needs at least one view)."""
    from crud_views.lib.views import DetailView, ListView

    vs = ViewSet(model=model, name=name, parent=parent)
    bases = {"list": ListView, "detail": DetailView}
    for key in key_views:
        type(
            f"V_{name}_{key}",
            (bases[key],),
            {"cv_viewset": vs, "cv_list_actions": [], "cv_context_actions": [], "__module__": __name__},
        )
    return vs


def _resource_viewset(name: str, parent: ParentViewSet | None = None) -> ViewSet:
    from crud_views.lib.resource import ResourceViewMixin
    from crud_views.lib.views import ListView

    vs = ViewSet(model=PublisherFile, name=name, parent=parent)
    type(
        f"V_{name}_list",
        (ResourceViewMixin, ListView),
        {"cv_viewset": vs, "cv_list_actions": [], "cv_context_actions": [], "__module__": __name__},
    )
    return vs


def _structure_messages(*viewsets):
    """The ancestor-structure system-check messages that concern ``viewsets``."""
    from crud_views.checks import check_ancestor_declarations

    names = {vs.name for vs in viewsets}
    return [m for m in check_ancestor_declarations() if getattr(m.obj, "name", None) in names]


# ── cyclic and unresolved ancestry shapes ───────────────────────────────────


def _self_cycle(sfx):
    name = f"st_self_{sfx}"
    vs = _viewset(Book, name, ParentViewSet(name=name, attribute="publisher"))
    return SimpleNamespace(viewsets=[vs], target=vs, chain=rf"{name} -> {name}", kind="cycle")


def _two_cycle(sfx):
    a, b = f"st_a_{sfx}", f"st_b_{sfx}"
    vs_a = _viewset(Book, a, ParentViewSet(name=b, attribute="publisher"))  # forward reference to b
    vs_b = _viewset(Publisher, b, ParentViewSet(name=a, attribute="books"))
    return SimpleNamespace(viewsets=[vs_a, vs_b], target=vs_a, chain=rf"{a} -> {b} -> {a}", kind="cycle")


def _missing(sfx):
    name, missing = f"st_orphan_{sfx}", f"st_nowhere_{sfx}"
    vs = _viewset(Book, name, ParentViewSet(name=missing, attribute="publisher"))
    return SimpleNamespace(viewsets=[vs], target=vs, chain=rf"{name} -> {missing}", kind="missing")


SHAPES = {"self_cycle": _self_cycle, "two_node_cycle": _two_cycle, "missing_parent": _missing}


@pytest.mark.parametrize("shape", SHAPES)
def test_urlpatterns_fails_bounded_and_names_the_chain(shape, sfx, bounded, no_db):
    case = SHAPES[shape](sfx)
    for vs in case.viewsets:
        with pytest.raises(ImproperlyConfigured) as excinfo:
            _ = vs.urlpatterns
        message = str(excinfo.value)
        assert vs.name in message
    with pytest.raises(ImproperlyConfigured, match=case.chain):
        _ = case.target.urlpatterns


@pytest.mark.parametrize("shape", SHAPES)
def test_actual_urlconf_import_fails_bounded(shape, sfx, bounded, no_db, tmp_path, monkeypatch):
    case = SHAPES[shape](sfx)
    modname = f"st_urls_{shape}_{sfx}"
    (tmp_path / f"{modname}.py").write_text(
        "from crud_views.lib.viewset import ViewSet\n"
        f"urlpatterns = ViewSet.get_viewset({case.target.name!r}).urlpatterns\n"
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    try:
        with override_settings(ROOT_URLCONF=modname):
            clear_url_caches()
            with pytest.raises(ImproperlyConfigured, match=case.chain):
                _ = get_resolver().url_patterns
    finally:
        sys.modules.pop(modname, None)
        clear_url_caches()


HELPERS = {
    "get_parent_url_args": lambda vs: vs.get_parent_url_args(),
    "get_parent_attributes": lambda vs: vs.get_parent_attributes(),
    "get_path_parent": lambda vs: vs.get_path_parent(),
    "get_queryset": lambda vs: vs.get_queryset(view=SimpleNamespace(kwargs={})),
}


@pytest.mark.parametrize("helper", HELPERS)
@pytest.mark.parametrize("shape", SHAPES)
def test_helper_walks_fail_bounded(shape, helper, sfx, bounded, no_db):
    case = SHAPES[shape](sfx)
    with pytest.raises(ImproperlyConfigured, match=case.chain):
        HELPERS[helper](case.target)


@pytest.mark.parametrize("helper", ["get_parent_url_args", "get_parent_attributes"])
def test_first_only_helpers_stay_bounded(helper, sfx, bounded, no_db):
    # the immediate edge of a two-node cycle is resolvable: first_only answers without walking the chain
    case = _two_cycle(sfx)
    a, b = case.viewsets
    value = getattr(a, helper)(first_only=True)
    assert value == {"get_parent_url_args": f"{b.name}_pk", "get_parent_attributes": "publisher"}[helper]
    # a self-cycle and a missing immediate parent fail at the first edge, still bounded and actionable
    self_case = _self_cycle(sfx + "x")
    with pytest.raises(ImproperlyConfigured, match=self_case.chain):
        getattr(self_case.target, helper)(first_only=True)
    missing_case = _missing(sfx + "y")
    with pytest.raises(ImproperlyConfigured, match=missing_case.chain):
        getattr(missing_case.target, helper)(first_only=True)


def test_forward_reference_registers_and_routes_once_resolved(sfx, bounded, no_db):
    pub_name, book_name = f"st_fpub_{sfx}", f"st_fbook_{sfx}"
    # the child is constructed (and its view registered) before its parent exists
    book_vs = _viewset(
        Book, book_name, ParentViewSet(name=pub_name, attribute="publisher"), key_views=("list", "detail")
    )
    assert pub_name not in _REGISTRY
    pub_vs = _viewset(Publisher, pub_name)
    assert book_vs.get_parent_url_args() == [f"{pub_name}_pk"]
    assert book_vs.get_parent_attributes() == ["publisher"]

    modname = f"tests.test1._st_fwd_urls_{sfx}"
    module = type(sys)(modname)
    module.urlpatterns = [*pub_vs.urlpatterns, *book_vs.urlpatterns, path("", include("tests.test1.project.urls"))]
    sys.modules[modname] = module
    try:
        with override_settings(ROOT_URLCONF=modname):
            clear_url_caches()
            assert (
                reverse(book_vs.get_router_name("list"), kwargs={f"{pub_name}_pk": 7}) == f"/{pub_name}/7/{book_name}/"
            )
            assert (
                reverse(book_vs.get_router_name("detail"), kwargs={f"{pub_name}_pk": 7, "pk": 3})
                == f"/{pub_name}/7/{book_name}/3/detail/"
            )
    finally:
        sys.modules.pop(modname, None)
        clear_url_caches()


# ── request guard: structure is validated before actor or lookup work ───────


@pytest.fixture
def routed_chain(sfx):
    """A valid core Publisher → plain Book list behind a temporary ROOT_URLCONF."""
    pub_vs = _viewset(Publisher, f"st_rpub_{sfx}")
    book_vs = _viewset(Book, f"st_rbook_{sfx}", ParentViewSet(name=pub_vs.name, attribute="publisher"))
    modname = f"tests.test1._st_req_urls_{sfx}"
    module = type(sys)(modname)
    module.urlpatterns = [*pub_vs.urlpatterns, *book_vs.urlpatterns, path("", include("tests.test1.project.urls"))]
    sys.modules[modname] = module
    try:
        with override_settings(ROOT_URLCONF=modname):
            clear_url_caches()
            url = reverse(book_vs.get_router_name("list"), kwargs={f"{pub_vs.name}_pk": 1})
            yield SimpleNamespace(pub_vs=pub_vs, book_vs=book_vs, url=url)
    finally:
        sys.modules.pop(modname, None)
        clear_url_caches()


def _break_missing(chain):
    with _REGISTRY_LOCK:
        _REGISTRY.pop(chain.pub_vs.name)
    return rf"{chain.book_vs.name} -> {chain.pub_vs.name}"


def _break_cycle(chain):
    chain.pub_vs.parent = ParentViewSet(name=chain.book_vs.name, attribute="books")
    return rf"{chain.book_vs.name} -> {chain.pub_vs.name} -> {chain.book_vs.name}"


def _break_relation(chain):
    chain.book_vs.parent = ParentViewSet(name=chain.pub_vs.name, attribute="title")
    return r"title"


def _break_resource_parent(chain):
    resource_vs = _resource_viewset(f"{chain.pub_vs.name}_res")
    chain.book_vs.parent = ParentViewSet(name=resource_vs.name, attribute="publisher")
    return rf"{resource_vs.name}.*Resource"


BREAKS = {
    "missing_parent": _break_missing,
    "cycle": _break_cycle,
    "non_relational_attribute": _break_relation,
    "resource_parent": _break_resource_parent,
}


@pytest.mark.parametrize("breakage", BREAKS)
def test_request_fails_before_any_query_or_lookup(breakage, routed_chain, bounded, no_db, monkeypatch):
    lookups = []
    original = ViewSet.get_queryset

    def spy(self, view):
        lookups.append(self.name)
        return original(self, view)

    monkeypatch.setattr(ViewSet, "get_queryset", spy)
    expected = BREAKS[breakage](routed_chain)  # broken after URL construction, so the route still exists
    # no database access at all: this test has none (pytest-django blocks it) and ``no_db`` fails any SQL
    with pytest.raises(ImproperlyConfigured, match=expected):
        Client().get(routed_chain.url)
    assert lookups == []


# ── declared relationships, from model metadata only ────────────────────────


def _pub(sfx):
    return _viewset(Publisher, f"st_p_{sfx}")


INVALID_RELATIONS = {
    "missing_field": (Book, {"attribute": "nonexistent"}, r"no field 'nonexistent'"),
    "default_attribute_is_not_a_field": (Book, {}, r"no field 'st_p_"),
    "non_relational_field": (Book, {"attribute": "title"}, r"'title' is not a relation"),
    "relation_path": (Book, {"attribute": "publisher__books"}, r"relation path"),
    "wrong_target_model": (BookNote, {"attribute": "book"}, r"points to Book, not Publisher"),
    "through_on_foreign_key": (
        Book,
        {"attribute": "publisher", "many_to_many_through_attribute": "genres"},
        r"many_to_many_through_attribute requires",
    ),
    "through_missing": (
        Genre,
        {"attribute": "publishers", "many_to_many_through_attribute": "nonexistent"},
        r"no field 'nonexistent'",
    ),
    "through_wrong_target": (
        Genre,
        {"attribute": "publishers", "many_to_many_through_attribute": "books"},
        r"'books' .*not a many-to-many relation to Genre",
    ),
}


@pytest.mark.parametrize("case", INVALID_RELATIONS)
def test_invalid_relationship_fails_check_and_request_before_lookup(case, sfx, bounded, no_db, monkeypatch):
    """Relationship errors are a system-check error plus a request guard (v2 validation table); URL
    construction only requires a finite, resolved, Resource-free chain, so the route itself still builds."""
    from crud_views.lib.ancestors import _validate_ancestor_structure

    model, edge, expected = INVALID_RELATIONS[case]
    pub_vs = _pub(sfx)
    child = _viewset(model, f"st_c_{sfx}", ParentViewSet(name=pub_vs.name, **edge))
    with pytest.raises(ImproperlyConfigured, match=expected):
        _validate_ancestor_structure(child)
    messages = _structure_messages(child)
    assert [m.id for m in messages] == ["viewset.E266"]
    assert child.name in messages[0].msg

    lookups = []
    original = ViewSet.get_queryset
    monkeypatch.setattr(ViewSet, "get_queryset", lambda self, view: lookups.append(self.name) or original(self, view))
    modname = f"tests.test1._st_rel_urls_{sfx}"
    module = type(sys)(modname)
    module.urlpatterns = [*pub_vs.urlpatterns, *child.urlpatterns, path("", include("tests.test1.project.urls"))]
    sys.modules[modname] = module
    try:
        with override_settings(ROOT_URLCONF=modname):
            clear_url_caches()
            url = reverse(child.get_router_name("list"), kwargs={child.parent.get_pk_name(): 1})
            with pytest.raises(ImproperlyConfigured, match=expected):
                Client().get(url)
    finally:
        sys.modules.pop(modname, None)
        clear_url_caches()
    assert lookups == []


def test_supported_relationships_validate(sfx, bounded, no_db):
    from crud_views.lib.ancestors import _validate_ancestor_structure

    pub_vs = _pub(sfx)
    book_vs = _viewset(Book, f"st_b_{sfx}", ParentViewSet(name=pub_vs.name, attribute="publisher"))  # forward FK
    note_vs = _viewset(BookNote, f"st_n_{sfx}", ParentViewSet(name=book_vs.name, attribute="book"))  # three levels
    genre_vs = _viewset(  # declared M2M with its through attribute on the parent (a reverse M2M accessor)
        Genre,
        f"st_g_{sfx}",
        ParentViewSet(name=pub_vs.name, attribute="publishers", many_to_many_through_attribute="genres"),
    )
    reverse_vs = _viewset(Publisher, f"st_r_{sfx}", ParentViewSet(name=book_vs.name, attribute="books"))  # reverse FK
    leaf_vs = _resource_viewset(f"st_f_{sfx}", ParentViewSet(name=pub_vs.name))  # Resource leaf, app-scoped
    for vs in (book_vs, note_vs, genre_vs, reverse_vs, leaf_vs):
        chain = _validate_ancestor_structure(vs)
        assert [ancestor.name for _, ancestor in chain] == [edge.name for edge, _ in chain]
        assert vs.urlpatterns
    assert [a.name for _, a in _validate_ancestor_structure(note_vs)] == [book_vs.name, pub_vs.name]
    assert _structure_messages(pub_vs, book_vs, note_vs, genre_vs, reverse_vs, leaf_vs) == []


def test_resource_parent_keeps_single_e261_and_fails_use(sfx, bounded, no_db):
    from crud_views.lib.ancestors import _validate_ancestor_structure

    resource_vs = _resource_viewset(f"st_res_{sfx}")
    child = _viewset(Book, f"st_rc_{sfx}", ParentViewSet(name=resource_vs.name, attribute="publisher"))
    grandchild = _viewset(BookNote, f"st_rg_{sfx}", ParentViewSet(name=child.name, attribute="book"))

    e261 = [m.id for vs in (resource_vs, child, grandchild) for c in vs.checks() for m in c.messages()]
    assert e261.count("viewset.E261") == 1
    assert [m.id for c in child.checks() for m in c.messages()].count("viewset.E261") == 1
    # the shared walk adds no second diagnostic for the same Resource-parent edge
    assert _structure_messages(resource_vs, child, grandchild) == []
    for vs in (child, grandchild):
        with pytest.raises(ImproperlyConfigured, match=rf"{resource_vs.name}.*Resource"):
            _validate_ancestor_structure(vs)
        with pytest.raises(ImproperlyConfigured, match=rf"{resource_vs.name}.*Resource"):
            _ = vs.urlpatterns


@pytest.mark.parametrize("shape", SHAPES)
def test_cycle_and_missing_parent_are_check_errors(shape, sfx, bounded, no_db):
    case = SHAPES[shape](sfx)
    messages = _structure_messages(*case.viewsets)
    assert messages, "expected a completed-registry structure error"
    assert {m.id for m in messages} == {"viewset.E266"}
    assert any(case.target.name in m.msg for m in messages)


def test_e261_check_survives_missing_parent(sfx, bounded, no_db):
    case = _missing(sfx)
    ids = [m.id for c in case.target.checks() for m in c.messages()]
    assert "viewset.E261" not in ids  # the missing reference is reported by E266, not as a crash here
