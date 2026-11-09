"""
Phase 06.18 plan 05 task 2 — Resource leaves beneath ORM ancestors.

A Resource may be the requested leaf of an ORM chain (one or three ORM ancestors here). The shared ancestor
guard resolves and authorizes the ORM chain first — for plain and permission-required Resource views, in both
cascade modes — and only then does the existing application-owned loader run (``cv_get_items`` /
``cv_get_item`` with the URL kwargs). The framework does not validate Resource membership: the application's
loader scopes the rows, and a row of another parent stays a 404 from that loader.

* Denied, anonymous, missing or mismatched ancestry never calls a loader.
* Successful ancestry still meets the Resource view's own local permission and the application's membership.
* A Resource used as a parent (of an ORM ViewSet or of another Resource) is a configuration error before any
  loading or query.
* A top-level Resource keeps its existing path: no ancestor queryset, no ancestor query, the same loading.

Every fixture builds fresh, uniquely named ViewSets behind a temporary ROOT_URLCONF (``isolated_routes``).
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import ClassVar

import pytest
from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured
from django.db import connection
from django.test import Client, RequestFactory
from django.test.utils import CaptureQueriesContext

from crud_views.lib.resource import Resource, ResourceViewMixin
from crud_views.lib.viewset import AncestorPolicy, ParentViewSet, ViewSet
from tests.lib.helper.user import user_viewset_permission
from tests.test1.app.models import Book, BookNote, Publisher
from tests.test1.test_ancestor_authorization import _client, _url, _user, isolated_routes
from tests.test1.test_ancestor_resolution import _register_project_viewsets

BUCKET: list[dict] = []  # application data: rows carry the ancestor scope they belong to
EVENTS: list[tuple] = []  # ordered ViewSet queryset calls and Resource loads


class _ChainFile(Resource):
    """Application-scoped rows: a row belongs to ``<scope_arg>=<pk>`` of its nearest ORM ancestor."""

    key: str
    size: int = 0
    scope: str = ""

    scope_arg: ClassVar[str | None] = None

    class Meta:
        verbose_name = "chain file"
        verbose_name_plural = "chain files"
        app_label = "app"
        pk_field = "key"
        pk_type = r"[a-z0-9\-]+"

    def __str__(self) -> str:
        return self.key

    @classmethod
    def cv_get_items(cls, request, **url_kwargs):
        EVENTS.append(("load", "items", cls.__name__, dict(url_kwargs)))
        if cls.scope_arg is None:
            return [cls.model_validate(row) for row in BUCKET]
        scope = f"{cls.scope_arg}={url_kwargs[cls.scope_arg]}"
        return [cls.model_validate(row) for row in BUCKET if row["scope"] == scope]

    @classmethod
    def cv_get_item(cls, request, pk, **url_kwargs):
        EVENTS.append(("load", "item", cls.__name__, dict(url_kwargs)))
        return super().cv_get_item(request, pk, **url_kwargs)


class TopFile(_ChainFile):
    pass


class PublisherChainFile(_ChainFile):
    pass


class NoteChainFile(_ChainFile):
    pass


def _loads():
    return [event for event in EVENTS if event[0] == "load"]


def _querysets():
    return [event[1] for event in EVENTS if event[0] == "queryset"]


@pytest.fixture
def events(monkeypatch):
    EVENTS.clear()
    original = ViewSet.get_queryset

    def spy(self, view):
        EVENTS.append(("queryset", self.name))
        return original(self, view)

    monkeypatch.setattr(ViewSet, "get_queryset", spy)
    yield EVENTS
    EVENTS.clear()


@pytest.fixture
def chains():
    from crud_views.lib.views import (
        DetailView,
        DetailViewPermissionRequired,
        ListView,
        ListViewPermissionRequired,
        ListViewTableMixin,
    )
    from tests.test1.app.resources import S3FileTable

    def resource_views(vs, composition):
        list_base = ListViewPermissionRequired if composition == "permission" else ListView
        detail_base = DetailViewPermissionRequired if composition == "permission" else DetailView
        common = {"cv_viewset": vs, "cv_context_actions": []}
        type(
            "FileList",
            (ResourceViewMixin, ListViewTableMixin, list_base),
            {**common, "table_class": S3FileTable, "cv_list_actions": []},
        )
        type("FileDetail", (ResourceViewMixin, detail_base), {**common, "template_name": "app/s3file_detail.html"})

    def resource_viewsets(model, name, parent):
        out = {}
        for composition in ("plain", "permission"):
            vs = ViewSet(
                model=model,
                name=f"{name}{composition}",
                parent=ParentViewSet(name=parent.name) if parent is not None else None,
                resource_permissions={"view": "app.view_s3file"},
            )
            resource_views(vs, composition)
            out[composition] = vs
        return out

    def build(sfx):
        pub = ViewSet(model=Publisher, name=f"rrpub{sfx}")
        book = ViewSet(model=Book, name=f"rrbook{sfx}", parent=ParentViewSet(name=pub.name, attribute="publisher"))
        note = ViewSet(model=BookNote, name=f"rrnote{sfx}", parent=ParentViewSet(name=book.name, attribute="book"))
        PublisherChainFile.scope_arg = f"{pub.name}_pk"
        NoteChainFile.scope_arg = f"{note.name}_pk"
        ns = SimpleNamespace(
            pub=pub,
            book=book,
            note=note,
            depth={
                1: SimpleNamespace(
                    vs=resource_viewsets(PublisherChainFile, f"rrfile1{sfx}", pub),
                    ancestors=[pub],
                    grants=[(Publisher, "view")],
                    scope_arg=PublisherChainFile.scope_arg,
                ),
                3: SimpleNamespace(
                    vs=resource_viewsets(NoteChainFile, f"rrfile3{sfx}", note),
                    ancestors=[pub, book, note],
                    grants=[(Publisher, "view"), (Book, "view"), (BookNote, "view")],
                    scope_arg=NoteChainFile.scope_arg,
                ),
            },
            top=resource_viewsets(TopFile, f"rrtop{sfx}", None)["permission"],
        )
        routed = [pub, book, note, *ns.depth[1].vs.values(), *ns.depth[3].vs.values(), ns.top]
        return ns, routed

    _register_project_viewsets()
    BUCKET.clear()
    try:
        with isolated_routes(build) as ns:
            yield ns
    finally:
        BUCKET.clear()
        PublisherChainFile.scope_arg = NoteChainFile.scope_arg = None


@pytest.fixture
def world(db, chains):
    penguin = Publisher.objects.create(name="Penguin")
    other = Publisher.objects.create(name="Other")
    book = Book.objects.create(title="Own", publisher=penguin)
    foreign_book = Book.objects.create(title="Foreign", publisher=other)
    note = BookNote.objects.create(book=book, note="mine")
    foreign_note = BookNote.objects.create(book=foreign_book, note="theirs")
    one, three = chains.depth[1], chains.depth[3]
    BUCKET.extend(
        [
            {"key": "own-1", "scope": f"{one.scope_arg}={penguin.pk}"},
            {"key": "foreign-1", "scope": f"{one.scope_arg}={other.pk}"},
            {"key": "own-3", "scope": f"{three.scope_arg}={note.pk}"},
            {"key": "foreign-3", "scope": f"{three.scope_arg}={foreign_note.pk}"},
        ]
    )
    one.own, one.foreign, one.objects, one.foreign_objects = "own-1", "foreign-1", [penguin], [other]
    three.own, three.foreign = "own-3", "foreign-3"
    three.objects, three.foreign_objects = [penguin, book, note], [other, foreign_book, foreign_note]
    return SimpleNamespace(penguin=penguin, other=other, book=book, foreign_book=foreign_book, note=note)


def _kwargs(chain, objects):
    return {f"{vs.name}_pk": obj.pk for vs, obj in zip(chain.ancestors, objects, strict=True)}


def _actor(name, chain, composition, *, ancestors=True, local=True, grants=None):
    user = _user(name, *(chain.grants if grants is None and ancestors else grants or []))
    if local and composition == "permission":
        user_viewset_permission(user, chain.vs["permission"], "view")
    return user


DEPTHS = pytest.mark.parametrize("depth", [1, 3], ids=["one-ancestor", "three-ancestors"])
COMPOSITIONS = pytest.mark.parametrize("composition", ["plain", "permission"])
MODES = pytest.mark.parametrize("cascade", [True, False], ids=["full", "nearest"])


def _apply_mode(vs, cascade):
    vs.ancestor_policy = AncestorPolicy(cascade=cascade)


def _keys(response):
    return [row.key for row in response.context["object_list"]]


# ── allowed ancestry: the application-scoped loader runs after the ORM chain ──


@pytest.mark.django_db
@MODES
@COMPOSITIONS
@DEPTHS
def test_allowed_ancestry_reaches_the_application_scoped_loader(chains, world, events, depth, composition, cascade):
    chain = chains.depth[depth]
    vs = chain.vs[composition]
    _apply_mode(vs, cascade)
    client = _client(_actor(f"rr_ok_{depth}_{composition}_{cascade}", chain, composition))
    kwargs = _kwargs(chain, chain.objects)

    listed = client.get(_url(vs, "list", **kwargs))
    assert listed.status_code == 200
    assert _keys(listed) == [chain.own]  # the application's scoping, not a framework membership filter
    first_load = next(i for i, event in enumerate(events) if event[0] == "load")
    ancestor_names = [a.name for a in chain.ancestors]
    assert _querysets()[: len(ancestor_names)] == ancestor_names  # outermost first, all before the loader
    assert all(events.index(("queryset", name)) < first_load for name in ancestor_names)
    assert all(load[3] == {k: str(v) for k, v in kwargs.items()} for load in _loads())  # URL kwargs unchanged

    events.clear()
    detail = client.get(_url(vs, "detail", pk=chain.own, **kwargs))
    assert detail.status_code == 200 and chain.own in detail.content.decode()
    assert _loads() and _querysets() == ancestor_names

    # another parent's row: reached, and the application's loader answers 404
    events.clear()
    assert client.get(_url(vs, "detail", pk=chain.foreign, **kwargs)).status_code == 404
    assert _loads()


# ── denied, missing or mismatched ancestry never loads ───────────────────────


@pytest.mark.django_db
@MODES
@COMPOSITIONS
@DEPTHS
@pytest.mark.parametrize("op", ["list", "detail"])
def test_denied_ancestry_never_calls_the_loader(chains, world, events, depth, composition, cascade, op):
    chain = chains.depth[depth]
    vs = chain.vs[composition]
    _apply_mode(vs, cascade)
    kwargs = _kwargs(chain, chain.objects)
    extra = {"pk": chain.own} if op == "detail" else {}
    url = _url(vs, op, **kwargs, **extra)

    anonymous = Client().get(url)
    assert anonymous.status_code == 302 and anonymous["Location"].startswith("/accounts/login/")
    assert events == []  # no ancestor lookup and no loader

    ungranted = _client(_actor(f"rr_deny_{depth}_{composition}_{cascade}_{op}", chain, composition, ancestors=False))
    assert ungranted.get(url).status_code == 403
    assert _loads() == []
    if cascade:  # full cascade: the outermost gate denies before any deeper ancestor is probed
        assert _querysets() == [chain.ancestors[0].name]

    if depth == 3:  # only the nearest grant is missing: every outer gate passes, still no loader
        events.clear()
        partial = _actor(f"rr_near_{composition}_{cascade}_{op}", chain, composition, grants=chain.grants[:2])
        assert _client(partial).get(url).status_code == 403
        assert _loads() == [] and _querysets() == [a.name for a in chain.ancestors]


@pytest.mark.django_db
@MODES
@COMPOSITIONS
@DEPTHS
def test_missing_or_mismatched_ancestry_is_404_without_loading(chains, world, events, depth, composition, cascade):
    chain = chains.depth[depth]
    vs = chain.vs[composition]
    _apply_mode(vs, cascade)
    client = _client(_actor(f"rr_404_{depth}_{composition}_{cascade}", chain, composition))
    missing = _kwargs(chain, chain.objects)
    missing[f"{chain.ancestors[0].name}_pk"] = world.penguin.pk + 1000
    assert client.get(_url(vs, "list", **missing)).status_code == 404
    assert client.get(_url(vs, "detail", pk=chain.own, **missing)).status_code == 404
    if depth == 3:  # the Book belongs to another Publisher; the BookNote belongs to that Book
        mismatched = _kwargs(chain, [world.penguin, *chain.foreign_objects[1:]])
        assert client.get(_url(vs, "list", **mismatched)).status_code == 404
        assert client.get(_url(vs, "detail", pk=chain.foreign, **mismatched)).status_code == 404
    assert _loads() == []


# ── the Resource view's own permission after successful ancestry ─────────────


@pytest.mark.django_db
@MODES
@DEPTHS
def test_local_resource_permission_still_denies_after_ancestry(chains, world, events, depth, cascade):
    chain = chains.depth[depth]
    vs = chain.vs["permission"]
    _apply_mode(vs, cascade)
    client = _client(_actor(f"rr_local_{depth}_{cascade}", chain, "permission", local=False))
    kwargs = _kwargs(chain, chain.objects)
    for op, extra in (("list", {}), ("detail", {"pk": chain.own})):
        events.clear()
        assert client.get(_url(vs, op, **kwargs, **extra)).status_code == 403
        assert _querysets() == [a.name for a in chain.ancestors]  # ancestry ran and passed first
        assert _loads() == []


# ── Resource parents are configuration errors ────────────────────────────────


@pytest.fixture
def resource_parent():
    from crud_views.lib.views import ListView

    def build(sfx):
        parent = ViewSet(model=TopFile, name=f"rrrparent{sfx}", resource_permissions={"view": "app.view_s3file"})
        orm_child = ViewSet(model=Book, name=f"rrormchild{sfx}", parent=ParentViewSet(name=parent.name))
        res_child = ViewSet(
            model=PublisherChainFile,
            name=f"rrreschild{sfx}",
            parent=ParentViewSet(name=parent.name),
            resource_permissions={"view": "app.view_s3file"},
        )
        common = {"cv_list_actions": [], "cv_context_actions": []}
        ns = SimpleNamespace(
            parent=parent,
            orm_child=orm_child,
            res_child=res_child,
            OrmList=type("List", (ListView,), {"cv_viewset": orm_child, **common}),
            ResList=type("List", (ResourceViewMixin, ListView), {"cv_viewset": res_child, **common}),
        )
        return ns, []  # nothing beneath a Resource can be routed

    _register_project_viewsets()
    with isolated_routes(build) as ns:
        yield ns


@pytest.mark.django_db
@pytest.mark.parametrize("child", ["orm", "resource"])
def test_resource_parent_is_a_configuration_error_before_any_loading(resource_parent, events, child):
    vs = resource_parent.orm_child if child == "orm" else resource_parent.res_child
    view_class = resource_parent.OrmList if child == "orm" else resource_parent.ResList
    with pytest.raises(ImproperlyConfigured, match="Resource-based"):
        vs.urlpatterns  # noqa: B018 - URL construction rejects the Resource ancestor
    request = RequestFactory().get("/")
    request.user = User.objects.create_superuser(username=f"rr_rparent_{child}", password="pw")
    view = view_class()
    view.setup(request, **{f"{resource_parent.parent.name}_pk": "own-1"})
    with CaptureQueriesContext(connection) as captured, pytest.raises(ImproperlyConfigured, match="Resource-based"):
        view._cv_ancestor_guard()
    assert captured.captured_queries == [] and events == []


# ── top-level Resource: existing path, no ancestor work ──────────────────────


@pytest.mark.django_db
def test_top_level_resource_is_unchanged(chains, world, events):
    user = _user("rr_top")
    user_viewset_permission(user, chains.top, "view")
    client = _client(user)
    with CaptureQueriesContext(connection) as captured:
        listed = client.get(_url(chains.top, "list"))
    assert listed.status_code == 200
    assert sorted(_keys(listed)) == sorted(row["key"] for row in BUCKET)
    assert _querysets() == []  # no ancestor queryset
    assert not [q for q in captured.captured_queries if '"app_publisher"' in q["sql"]]
    top_loads = len(_loads())
    events.clear()
    detail = client.get(_url(chains.top, "detail", pk="own-1"))
    assert detail.status_code == 200 and _querysets() == []

    # the same loading as a nested leaf once its ancestry passed
    chain = chains.depth[1]
    events.clear()
    nested = _client(_actor("rr_top_nested", chain, "permission"))
    assert nested.get(_url(chain.vs["permission"], "list", **_kwargs(chain, chain.objects))).status_code == 200
    assert len(_loads()) == top_loads
