"""
Phase 06.18 plan 06 — the reached default-database boundary of nested ViewSet requests (ANCE-06).

Wave one supports only ``default`` for a nested request's ORM data: its ancestor lookups, the child's own
querysets and objects, and its writes. A nondefault selection is a configuration error *where it is reached* —
an explicit ``.using()`` (which wins over any router), a router answer, an instance hint or a view's alias
override — and nothing strips the selection, forces ``default`` or retries on another database. An explicit
``.using("default")`` is valid. Top-level ViewSets keep their routed behaviour.

Rows collide on purpose: ``default`` and ``shard`` hold the same primary keys with different contents, so a
wrong-copy read or write is visible instead of silently "working". Query captures on both aliases prove that a
refused consumer issued no SQL, and that an earlier actor/ancestor denial never reaches a later invalid route.

The router below is module-local and hint-aware: ``routes.read[Model]`` / ``routes.write[Model]`` map a model to
an alias or to ``callable(hints) -> alias``; unmapped models (auth, sessions, content types) get no answer, which
is Django's default routing.

Fixtures build fresh, uniquely named ViewSets behind a temporary ROOT_URLCONF and restore registry, URL and
ContentType caches afterwards (``isolated_routes``; the project URLconf is imported first).
"""

from __future__ import annotations

from contextlib import contextmanager
from types import SimpleNamespace

import django_filters
import pytest
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured
from django.db import connections, router
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.list import MultipleObjectMixin

from crud_views.lib.viewset import AncestorPolicy, ParentViewSet, ViewSet
from tests.test1.app.models import Book, BookNote, Publisher
from tests.test1.test_ancestor_authorization import _client, _url, _user, isolated_routes
from tests.test1.test_ancestor_resolution import _register_project_viewsets

pytestmark = pytest.mark.django_db(transaction=True, databases=["default", "shard"])
ALIASES = ("default", "shard")
REFUSED = r"nested ViewSets support only the 'default' database"


# ── routing, rows and captures ──────────────────────────────────────────────


@pytest.fixture
def routes(monkeypatch):
    """Module-local hint-aware router; every consulted (operation, model) is recorded in ``calls``."""
    table = SimpleNamespace(read={}, write={}, calls=[])

    def pick(mapping, operation, model, hints):
        table.calls.append((operation, model))
        choice = mapping.get(model)
        return choice(hints) if callable(choice) else choice

    class Router:
        def db_for_read(self, model, **hints):
            return pick(table.read, "read", model, hints)

        def db_for_write(self, model, **hints):
            return pick(table.write, "write", model, hints)

    monkeypatch.setattr(router, "routers", [Router()])
    ContentType.objects.clear_cache()
    yield table
    ContentType.objects.clear_cache()


def _hinted(alias):
    """A write route that answers ``alias`` only when Django passes an instance hint."""
    return lambda hints: alias if hints.get("instance") is not None else None


def _rows(using):
    """Colliding identities: the same primary keys on both aliases, contents naming their database."""
    publisher = Publisher.objects.using(using).create(pk=41, name=f"{using} publisher")
    book = Book.objects.using(using).create(pk=71, publisher_id=publisher.pk, title=f"{using} child")
    note = BookNote.objects.using(using).create(pk=91, book_id=book.pk, note=f"{using} note")
    return SimpleNamespace(publisher=publisher, book=book, note=note)


@pytest.fixture
def worlds():
    return {alias: _rows(alias) for alias in ALIASES}


@contextmanager
def captured():
    with CaptureQueriesContext(connections["default"]) as default, CaptureQueriesContext(connections["shard"]) as shard:
        yield SimpleNamespace(default=default, shard=shard)


def _sql(capture, table=None) -> list[str]:
    return [q["sql"] for q in capture.captured_queries if table is None or f'"{table}"' in q["sql"]]


def _superclient(name="ad_super"):
    return _client(User.objects.create_superuser(username=name, password="pw"))


# ── dynamic ViewSets ─────────────────────────────────────────────────────────


class BookFilter(django_filters.FilterSet):
    class Meta:
        model = Book
        fields = ["title"]


class DefaultUsingViewSet(ViewSet):
    """An ancestor ViewSet whose queryset carries an explicit ``.using("default")`` selection."""

    def get_queryset(self, view):
        return super().get_queryset(view).using("default")


class ShardUsingViewSet(ViewSet):
    """An ancestor ViewSet whose queryset carries an explicit ``.using("shard")`` selection."""

    def get_queryset(self, view):
        return super().get_queryset(view).using("shard")


def _using_queryset(alias):
    def get_queryset(self):
        return self.cv_viewset.get_queryset(view=self).using(alias)

    return get_queryset


def _selection_attrs(style, alias):
    """A child view whose own queryset selects ``alias``: an override, or Django's ``queryset`` attribute path."""
    if style == "override":
        return {"get_queryset": _using_queryset(alias)}
    return {"queryset": Book.objects.using(alias), "get_queryset": SingleObjectMixin.get_queryset}


SELECTION_STYLES = ["override", "queryset-attribute"]


@pytest.fixture
def dbv():
    from crud_views.lib.views import DeleteView, DetailView, ListView, ListViewTableFilterMixin, UpdateView

    def view(base, vs, **attrs):
        return type(base.__name__, (base,), {"cv_viewset": vs, "cv_context_actions": [], **attrs})

    def lst(vs, **attrs):
        return view(ListView, vs, cv_list_actions=[], **attrs)

    def build(sfx):
        ns = SimpleNamespace()
        edge = {"attribute": "publisher"}

        # top-level Publisher (also the routed top-level control) -> Book -> BookNote
        ns.pub = ViewSet(model=Publisher, name=f"adpub{sfx}")
        ns.PubList, ns.PubDetail = lst(ns.pub), view(DetailView, ns.pub)
        ns.PubDelete = view(DeleteView, ns.pub, cv_show_related_objects=True)
        ns.book = ViewSet(model=Book, name=f"adbook{sfx}", parent=ParentViewSet(name=ns.pub.name, **edge))
        ns.BookList, ns.BookDetail = lst(ns.book), view(DetailView, ns.book)
        # a filtered list: django-filter hands its collection to get_context_data as ``object_list``
        ns.fbook = ViewSet(model=Book, name=f"adfbook{sfx}", parent=ParentViewSet(name=ns.pub.name, **edge))
        ns.FBookList = type(
            "FilterList",
            (ListViewTableFilterMixin, ListView),
            {"cv_viewset": ns.fbook, "cv_list_actions": [], "cv_context_actions": [], "filterset_class": BookFilter},
        )
        ns.BookUpdate = view(UpdateView, ns.book, fields=["title"])
        ns.BookDelete = view(DeleteView, ns.book, cv_show_related_objects=True)
        ns.note = ViewSet(
            model=BookNote, name=f"adnote{sfx}", parent=ParentViewSet(name=ns.book.name, attribute="book")
        )
        ns.NoteList, ns.NoteDetail = lst(ns.note), view(DetailView, ns.note)

        # child views whose own querysets select an alias explicitly
        ns.sel = {}
        for style in SELECTION_STYLES:
            for alias in ALIASES:
                vs = ViewSet(
                    model=Book,
                    name=f"ad{style.replace('-', '')}{alias}{sfx}",
                    parent=ParentViewSet(name=ns.pub.name, **edge),
                )
                attrs = _selection_attrs(style, alias)
                list_attrs = (
                    attrs if style == "override" else {**attrs, "get_queryset": MultipleObjectMixin.get_queryset}
                )
                ns.sel[style, alias] = SimpleNamespace(
                    vs=vs, Detail=view(DetailView, vs, **attrs), List=lst(vs, **list_attrs)
                )

        # ancestors whose ViewSet queryset selects an alias explicitly; provider none (all-none ancestry)
        ns.dpub = DefaultUsingViewSet(model=Publisher, name=f"addpub{sfx}")
        ns.dbook = ViewSet(model=Book, name=f"addbook{sfx}", parent=ParentViewSet(name=ns.dpub.name, **edge))
        ns.DBookDetail = view(DetailView, ns.dbook, get_queryset=_using_queryset("default"))
        ns.spub = ShardUsingViewSet(model=Publisher, name=f"adspub{sfx}")
        ns.sbook = ViewSet(model=Book, name=f"adsbook{sfx}", parent=ParentViewSet(name=ns.spub.name, **edge))
        ns.SBookDetail = view(DetailView, ns.sbook)
        ns.npub = ViewSet(model=Publisher, name=f"adnpub{sfx}", ancestor_policy=AncestorPolicy(provider="none"))
        ns.nbook = ViewSet(model=Book, name=f"adnbook{sfx}", parent=ParentViewSet(name=ns.npub.name, **edge))
        ns.NBookDetail, ns.NBookList = view(DetailView, ns.nbook), lst(ns.nbook)

        # delete views with an alias override (custom delete database)
        ns.adel = {}
        for alias in ALIASES:
            vs = ViewSet(model=Book, name=f"addel{alias}{sfx}", parent=ParentViewSet(name=ns.pub.name, **edge))
            view(ListView, vs, cv_list_actions=[])
            ns.adel[alias] = SimpleNamespace(
                vs=vs,
                Delete=view(DeleteView, vs, cv_show_related_objects=True, cv_get_db_alias=lambda self, a=alias: a),
            )

        routed = [
            ns.pub,
            ns.book,
            ns.fbook,
            ns.note,
            *(entry.vs for entry in ns.sel.values()),
            ns.dpub,
            ns.dbook,
            ns.spub,
            ns.sbook,
            ns.npub,
            ns.nbook,
            *(entry.vs for entry in ns.adel.values()),
        ]
        return ns, routed

    _register_project_viewsets()
    with isolated_routes(build) as ns:
        yield ns


def _book_kwargs(ns_vs, parent_vs, world, *, pk=True):
    kwargs = {f"{parent_vs.name}_pk": world.publisher.pk}
    if pk:
        kwargs["pk"] = world.book.pk
    return kwargs


# ── Task 1: reached ancestor and child querysets ────────────────────────────


def test_nested_reads_on_default_succeed(dbv, worlds, routes):
    client = _superclient()
    world = worlds["default"]
    with captured() as sql:
        detail = client.get(_url(dbv.book, "detail", **_book_kwargs(dbv.book, dbv.pub, world)))
        listing = client.get(_url(dbv.book, "list", **_book_kwargs(dbv.book, dbv.pub, world, pk=False)))
    assert detail.status_code == 200 and detail.context["object"].title == "default child"
    assert listing.status_code == 200 and [b.title for b in listing.context["object_list"]] == ["default child"]
    assert _sql(sql.shard) == []


def test_missing_rows_keep_their_404_on_default(dbv, worlds, routes):
    client = _superclient()
    missing_book = {f"{dbv.pub.name}_pk": 41, "pk": 999}
    missing_publisher = {f"{dbv.pub.name}_pk": 999, "pk": 71}
    with captured() as sql:
        assert client.get(_url(dbv.book, "detail", **missing_book)).status_code == 404
        assert client.get(_url(dbv.book, "detail", **missing_publisher)).status_code == 404
    assert _sql(sql.shard) == []


def test_missing_ancestor_is_404_before_a_later_invalid_child_route(dbv, worlds, routes):
    """The ancestor lookup on default fails first: the child's shard route is never reached."""
    routes.read[Book] = "shard"
    client = _superclient()
    with captured() as sql:
        response = client.get(_url(dbv.book, "detail", **{f"{dbv.pub.name}_pk": 999, "pk": 71}))
    assert response.status_code == 404
    assert ("read", Book) not in routes.calls
    assert _sql(sql.shard) == []


def test_explicit_default_wins_over_a_shard_router(dbv, worlds, routes):
    """An explicit ``.using("default")`` on the ancestor and child querysets beats a router answering shard."""
    routes.read[Publisher] = routes.read[Book] = "shard"
    client = _superclient()
    kwargs = {f"{dbv.dpub.name}_pk": 41, "pk": 71}
    with captured() as sql:
        response = client.get(_url(dbv.dbook, "detail", **kwargs))
    assert response.status_code == 200
    obj = response.context["object"]
    assert (obj.title, obj._state.db) == ("default child", "default")
    assert _sql(sql.shard) == []


@pytest.mark.parametrize("kind", ["detail", "list"])
def test_router_selected_shard_ancestor_is_refused_before_it_is_read(dbv, worlds, routes, kind):
    routes.read[Publisher] = "shard"
    client = _superclient()
    with captured() as sql, pytest.raises(ImproperlyConfigured, match=REFUSED) as caught:
        client.get(_url(dbv.book, kind, **_book_kwargs(dbv.book, dbv.pub, worlds["default"], pk=kind == "detail")))
    assert dbv.book.name in str(caught.value) and f"ancestor ViewSet {dbv.pub.name!r}" in str(caught.value)
    assert "'shard'" in str(caught.value)
    assert _sql(sql.shard) == []
    assert _sql(sql.default, "app_publisher") == [] and _sql(sql.default, "app_book") == []


def test_filtered_list_collection_is_checked_where_it_is_consumed(dbv, worlds, routes):
    """django-filter passes its collection to get_context_data directly; that collection is still checked."""
    client = _superclient()
    kwargs = {f"{dbv.pub.name}_pk": 41}
    response = client.get(_url(dbv.fbook, "list", **kwargs))
    assert response.status_code == 200 and [b.title for b in response.context["object_list"]] == ["default child"]
    routes.read[Book] = "shard"
    with captured() as sql, pytest.raises(ImproperlyConfigured, match=REFUSED):
        client.get(_url(dbv.fbook, "list", **kwargs))
    assert _sql(sql.shard) == [] and _sql(sql.default, "app_book") == []


def test_explicit_shard_ancestor_queryset_is_refused(dbv, worlds, routes):
    client = _superclient()
    with captured() as sql, pytest.raises(ImproperlyConfigured, match=REFUSED):
        client.get(_url(dbv.sbook, "detail", **{f"{dbv.spub.name}_pk": 41, "pk": 71}))
    assert _sql(sql.shard) == []
    assert _sql(sql.default, "app_book") == []


@pytest.mark.parametrize("kind", ["detail", "list", "update", "delete"])
def test_router_selected_shard_child_is_refused(dbv, worlds, routes, kind):
    """The ancestor resolves on default; the child's routed read is refused before any Book SQL."""
    routes.read[Book] = "shard"
    client = _superclient()
    with captured() as sql, pytest.raises(ImproperlyConfigured, match=REFUSED) as caught:
        client.get(_url(dbv.book, kind, **_book_kwargs(dbv.book, dbv.pub, worlds["default"], pk=kind != "list")))
    assert "Book queryset" in str(caught.value)
    assert _sql(sql.shard) == []
    assert _sql(sql.default, "app_book") == []
    assert len(_sql(sql.default, "app_publisher")) == 1  # the ancestor itself was read once, on default


@pytest.mark.parametrize("style", SELECTION_STYLES)
@pytest.mark.parametrize("kind", ["Detail", "List"])
def test_explicit_child_selections(dbv, worlds, routes, style, kind):
    """A child view's own ``.using("shard")`` cannot bypass the guard; its ``.using("default")`` works even when
    the router answers shard."""
    routes.read[Book] = "shard"
    client = _superclient()
    shard, default = dbv.sel[style, "shard"], dbv.sel[style, "default"]
    key = kind.lower()
    with captured() as sql, pytest.raises(ImproperlyConfigured, match=REFUSED):
        client.get(_url(shard.vs, key, **_book_kwargs(shard.vs, dbv.pub, worlds["default"], pk=kind == "Detail")))
    assert _sql(sql.shard) == []
    with captured() as sql:
        response = client.get(
            _url(default.vs, key, **_book_kwargs(default.vs, dbv.pub, worlds["default"], pk=kind == "Detail"))
        )
    assert response.status_code == 200
    rows = [response.context["object"]] if kind == "Detail" else list(response.context["object_list"])
    assert [(row.title, row._state.db) for row in rows] == [("default child", "default")]
    assert _sql(sql.shard) == []


def test_colliding_rows_expose_a_wrong_copy_without_the_boundary(dbv, worlds, routes, monkeypatch):
    """Mutation check: with the boundary disabled the same request serves the shard copy of the same PKs, so
    the refusal above is what keeps the wrong row out."""
    routes.read[Book] = "shard"
    monkeypatch.setattr("crud_views.lib.ancestor_db._require_default_alias", lambda alias, **kw: None)
    response = _superclient().get(_url(dbv.book, "detail", **_book_kwargs(dbv.book, dbv.pub, worlds["default"])))
    assert response.status_code == 200
    assert (response.context["object"].title, response.context["object"]._state.db) == ("shard child", "shard")


def test_all_none_ancestry_still_validates_data_aliases(dbv, worlds, routes):
    routes.read[Book] = "shard"
    client = _client(None)  # all-none: a plain endpoint admits everybody, the data path is still checked
    for kind in ("detail", "list"):
        kwargs = {f"{dbv.npub.name}_pk": 41, **({"pk": 71} if kind == "detail" else {})}
        with captured() as sql, pytest.raises(ImproperlyConfigured, match=REFUSED):
            client.get(_url(dbv.nbook, kind, **kwargs))
        assert _sql(sql.shard) == []


@pytest.mark.parametrize("actor", ["anonymous", "inactive"])
def test_prior_actor_denial_hides_a_later_invalid_route(dbv, worlds, routes, actor):
    routes.read[Publisher] = routes.read[Book] = "shard"
    allow_inactive = "django.contrib.auth.backends.AllowAllUsersModelBackend"
    client = _client(None)
    with override_settings(AUTHENTICATION_BACKENDS=[allow_inactive]), captured() as sql:
        if actor == "inactive":
            user = _user("ad_inactive", superuser=True)
            user.is_active = False
            user.save()
            client.force_login(user, backend=allow_inactive)
        response = client.get(_url(dbv.book, "detail", **_book_kwargs(dbv.book, dbv.pub, worlds["default"])))
    assert response.status_code == (302 if actor == "anonymous" else 403)
    assert ("read", Publisher) not in routes.calls and ("read", Book) not in routes.calls
    assert _sql(sql.shard) == []


def test_outer_denial_hides_a_deeper_invalid_route(dbv, worlds, routes):
    """Publisher -> Book -> BookNote with Book reads routed to shard: a denied Publisher gate stops before the
    Book queryset is built; once the Publisher gate passes, the Book lookup is refused."""
    routes.read[Book] = "shard"
    kwargs = {f"{dbv.pub.name}_pk": 41, f"{dbv.book.name}_pk": 71, "pk": 91}
    denied = _client(_user("ad_denied", (Book, "view"), (BookNote, "view")))
    with captured() as sql:
        assert denied.get(_url(dbv.note, "detail", **kwargs)).status_code == 403
    assert ("read", Book) not in routes.calls
    assert _sql(sql.shard) == []
    reader = _client(_user("ad_reader", (Publisher, "view"), (Book, "view"), (BookNote, "view")))
    with captured() as sql, pytest.raises(ImproperlyConfigured, match=f"ancestor ViewSet {dbv.book.name!r}"):
        reader.get(_url(dbv.note, "detail", **kwargs))
    assert _sql(sql.shard) == []


def test_top_level_routed_reads_are_unchanged(dbv, worlds, routes):
    routes.read[Publisher] = "shard"
    client = _superclient()
    detail = client.get(_url(dbv.pub, "detail", pk=41))
    listing = client.get(_url(dbv.pub, "list"))
    assert detail.status_code == 200 and detail.context["object"].name == "shard publisher"
    assert [p.name for p in listing.context["object_list"]] == ["shard publisher"]


# ── Task 1: delete preview alias ─────────────────────────────────────────────


@pytest.fixture
def collector(monkeypatch):
    """Poison every preview-collection step of DeleteView."""
    from crud_views.lib.views import delete as delete_module

    def poison(*args, **kwargs):
        raise AssertionError("delete preview collection reached")

    monkeypatch.setattr(delete_module, "inspect_deletion", poison)
    monkeypatch.setattr(delete_module, "merge_delete_preview", poison)
    return poison


def test_nested_delete_preview_refuses_a_shard_delete_alias_before_collection(dbv, worlds, routes, collector):
    """A default-loaded target whose instance-aware delete alias selects shard (colliding related rows exist on
    both aliases) is refused before protection hooks, preview contributions or related-object queries."""
    routes.write[Book] = _hinted("shard")
    for hook in ("cv_check_delete_protection", "cv_get_delete_preview", "cv_filter_related_objects"):
        setattr(dbv.BookDelete, hook, collector)
    client = _superclient()
    with captured() as sql, pytest.raises(ImproperlyConfigured, match=REFUSED) as caught:
        client.get(_url(dbv.book, "delete", **_book_kwargs(dbv.book, dbv.pub, worlds["default"])))
    assert "delete" in str(caught.value) and "'shard'" in str(caught.value)
    assert _sql(sql.shard) == []
    assert _sql(sql.default, "app_booknote") == []
    assert ("write", Book) in routes.calls  # the existing instance-aware selector was consulted, not replaced


def test_nested_delete_preview_custom_alias(dbv, worlds, routes):
    """A delete alias override is validated as selected: shard refused, explicit default previews default rows
    even when the router answers shard."""
    routes.write[Book] = _hinted("shard")
    client = _superclient()
    shard, default = dbv.adel["shard"], dbv.adel["default"]
    with captured() as sql, pytest.raises(ImproperlyConfigured, match=REFUSED):
        client.get(_url(shard.vs, "delete", **_book_kwargs(shard.vs, dbv.pub, worlds["default"])))
    assert _sql(sql.shard) == []
    with captured() as sql:
        response = client.get(_url(default.vs, "delete", **_book_kwargs(default.vs, dbv.pub, worlds["default"])))
    assert response.status_code == 200
    assert response.context["related_summary"]
    assert _sql(sql.shard) == []


def test_pinned_delete_alias_is_refused_when_consumed(dbv, worlds, routes, collector, rf):
    """The refusal applies to a cached (pinned) alias too, not only to a newly selected one."""
    view = dbv.BookDelete()
    request = rf.get("/")
    request.user = User.objects.create_superuser(username="ad_pinned", password="pw")
    view.setup(request, **_book_kwargs(dbv.book, dbv.pub, worlds["default"]))
    view.object = Book.objects.get(pk=71)
    view._cv_delete_db_alias = "shard"
    with captured() as sql, pytest.raises(ImproperlyConfigured, match=REFUSED):
        view._cv_inspect_deletion()
    assert _sql(sql.shard) == [] and _sql(sql.default) == []


def test_delete_preview_after_an_ancestor_denial_selects_no_alias(dbv, worlds, routes, collector, monkeypatch):
    routes.write[Book] = _hinted("shard")
    monkeypatch.setattr(dbv.BookDelete, "cv_get_db_alias", lambda self: pytest.fail("delete alias selected"))
    client = _client(_user("ad_viewer", (Publisher, "view"), (Book, "delete")))  # write needs Publisher change
    response = client.get(_url(dbv.book, "delete", **_book_kwargs(dbv.book, dbv.pub, worlds["default"])))
    assert response.status_code == 403


def test_top_level_shard_delete_preview_is_unchanged(dbv, worlds, routes):
    routes.read[Publisher] = routes.write[Publisher] = "shard"
    routes.read[Book] = routes.write[Book] = "shard"
    response = _superclient().get(_url(dbv.pub, "delete", pk=41))
    assert response.status_code == 200
    assert response.context["object"].name == "shard publisher"
    assert response.context["related_summary"]
