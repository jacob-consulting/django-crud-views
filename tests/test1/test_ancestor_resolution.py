"""
Phase 06.18 plan 05 task 1 — scoped ancestry, relationship identity and the structural parent.

* Every ancestor is read through its own ViewSet queryset, called with the *actual* requested child view (its
  request and unchanged URL kwargs), and constrained to that edge's configured URL argument and to the
  already resolved outer ancestor. A row excluded by the ancestor's manager or ViewSet scope is a 404 even
  for a superuser or a granted actor; nothing retries through an unfiltered manager and no ancestor endpoint
  is set up, dispatched or asked for its queryset.
* Relationships are identities, not matching numbers: int and UUID keys, explicit ``pk_name`` / ``attribute``
  declarations, FK and M2M edges, at every depth, including creates (refused before any form or attachment).
* A reached ORM child object must belong to the resolved immediate parent, and a nested child collection is
  scoped to it — also when the child view overrides ``get_queryset`` or restores Django's standard
  ``queryset`` attribute path without the parent filter (``ancestors._validate_child_parent`` at
  ``CrudView.get_object``; ``ancestors._scope_child_queryset`` where list views consume ``object_list``).
* Create attachment, parent-state hooks and supported request helpers reuse the guard's resolved immediate
  structural parent — the same model/PK/database identity — even when that parent is unprotected (provider
  ``none``) and a farther ancestor supplies the gate. Resolved objects live on the view instance only.

Every fixture builds fresh, uniquely named ViewSets behind a temporary ROOT_URLCONF (``isolated_routes``),
restoring registry, vocabulary, URL and ContentType caches afterwards.
"""

from __future__ import annotations

import re
from types import SimpleNamespace

import django_filters
import pytest
from django.contrib.auth.models import User
from django.db import connection, models
from django.test import Client, RequestFactory
from django.test.utils import CaptureQueriesContext, isolate_apps
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.list import MultipleObjectMixin

from crud_views.lib import ancestors
from crud_views.lib.table import Table
from crud_views.lib.viewset import AncestorPolicy, ParentViewSet, ViewSet
from tests.test1.app.models import Author, Book, BookNote, Genre, Publisher, UUIDFragmentRow
from tests.test1.test_ancestor_authorization import _client, _url, _user, isolated_routes


class TenantViewSet(ViewSet):
    """An ancestor ViewSet with its own visibility scope (tenant / soft-delete style): ``hidden*`` rows are
    excluded for every actor."""

    def get_queryset(self, view):
        return super().get_queryset(view).exclude(name__startswith="hidden")


class BookTitleFilter(django_filters.FilterSet):
    class Meta:
        model = Book
        fields = ["title"]


class BookTitleTable(Table):
    class Meta:
        model = Book
        fields = ["title"]


def _all_books(self):
    """A child ``get_queryset`` override that forgets the parent filter."""
    return Book.objects.all()


def _all_genres(self):
    return Genre.objects.all()


def _all_rows(self):
    return UUIDFragmentRow.objects.all()


# child queryset styles that omit the parent filter: an explicit override, and Django's standard ``queryset``
# attribute path restored on the view (SingleObjectMixin / MultipleObjectMixin.get_queryset)
OVERRIDE_STYLES = ["override", "queryset-attribute"]


def _detail_attrs(style, model, override):
    if style == "override":
        return {"get_queryset": override}
    return {"queryset": model.objects.all(), "get_queryset": SingleObjectMixin.get_queryset}


def _list_attrs(style, model, override):
    if style == "override":
        return {"get_queryset": override}
    return {"queryset": model.objects.all(), "get_queryset": MultipleObjectMixin.get_queryset}


def _register_project_viewsets():
    """Import the project URLconf (and with it the shared app ViewSets) before ``isolated_routes`` snapshots
    the registry; otherwise a first import inside the isolated block is dropped again on restore."""
    import tests.test1.project.urls  # noqa: F401


@pytest.fixture
def res():
    from crud_views.lib.views import (
        CreateView,
        CreateViewParentMixin,
        CreateViewPermissionRequired,
        DeleteViewPermissionRequired,
        DetailView,
        DetailViewPermissionRequired,
        ListView,
        ListViewTableFilterMixin,
        ListViewTableMixin,
        UpdateViewPermissionRequired,
    )
    from crud_views_guardian.lib.views import GuardianDetailViewPermissionRequired
    from crud_views_guardian.lib.viewset import GuardianViewSet

    def lst(vs, base=ListView, **attrs):
        return type("List", (base,), {"cv_viewset": vs, "cv_list_actions": [], "cv_context_actions": [], **attrs})

    def det(vs, base=DetailView, **attrs):
        return type("Detail", (base,), {"cv_viewset": vs, "cv_context_actions": [], **attrs})

    def create(vs, fields, base=CreateView, **attrs):
        return type(
            "Create",
            (CreateViewParentMixin, base),
            {"cv_viewset": vs, "cv_context_actions": [], "fields": fields, **attrs},
        )

    def build(sfx):
        ns = SimpleNamespace()
        # core Publisher with its own (never dispatched) endpoints
        ns.pub = ViewSet(model=Publisher, name=f"arpub{sfx}")
        ns.PubList, ns.PubDetail = lst(ns.pub), det(ns.pub)

        # Publisher -> Book (default child queryset) -> BookNote
        ns.book = ViewSet(
            model=Book, name=f"arbook{sfx}", parent=ParentViewSet(name=ns.pub.name, attribute="publisher")
        )
        ns.BookList, ns.BookDetail = lst(ns.book), det(ns.book)
        ns.BookCreate = create(ns.book, ["title"])
        ns.note = ViewSet(
            model=BookNote, name=f"arnote{sfx}", parent=ParentViewSet(name=ns.book.name, attribute="book")
        )
        ns.NoteList, ns.NoteDetail = lst(ns.note), det(ns.note)
        ns.NoteCreate = create(ns.note, ["note"])

        # Books whose child querysets omit the parent filter (local permission + state gate: superuser actors)
        ns.cbook = {}
        for style in OVERRIDE_STYLES:
            vs = ViewSet(
                model=Book,
                name=f"ar{style.replace('-', '')}{sfx}",
                parent=ParentViewSet(name=ns.pub.name, attribute="publisher"),
            )
            ns.cbook[style] = SimpleNamespace(
                vs=vs,
                List=lst(vs, ListView, **_list_attrs(style, Book, _all_books)),
                Detail=det(vs, DetailViewPermissionRequired, **_detail_attrs(style, Book, _all_books)),
                Update=type(
                    "Update",
                    (UpdateViewPermissionRequired,),
                    {
                        "cv_viewset": vs,
                        "cv_context_actions": [],
                        "fields": ["title"],
                        **_detail_attrs(style, Book, _all_books),
                    },
                ),
                Delete=type(
                    "Delete",
                    (DeleteViewPermissionRequired,),
                    {"cv_viewset": vs, "cv_context_actions": [], **_detail_attrs(style, Book, _all_books)},
                ),
            )

        # filtered lists (django-filter hands its collection to get_context_data as ``object_list``) whose child
        # querysets omit the parent filter: a plain filtered list and a table + filter list
        ns.fbook = {}
        for style in OVERRIDE_STYLES:
            for kind, bases, extra in (
                ("filter", (ListViewTableFilterMixin, ListView), {}),
                ("table", (ListViewTableMixin, ListViewTableFilterMixin, ListView), {"table_class": BookTitleTable}),
            ):
                vs = ViewSet(
                    model=Book,
                    name=f"arf{kind}{style.replace('-', '')}{sfx}",
                    parent=ParentViewSet(name=ns.pub.name, attribute="publisher"),
                )
                attrs = {"filterset_class": BookTitleFilter, **extra, **_list_attrs(style, Book, _all_books)}
                listing = type(
                    "FilterList", bases, {"cv_viewset": vs, "cv_list_actions": [], "cv_context_actions": [], **attrs}
                )
                ns.fbook[style, kind] = SimpleNamespace(vs=vs, List=listing)

        # explicit URL argument name and FK attribute
        ns.house = ViewSet(
            model=Book,
            name=f"arhouse{sfx}",
            parent=ParentViewSet(name=ns.pub.name, attribute="publisher", pk_name="house_pk"),
        )
        ns.HouseDetail = det(ns.house)

        # Publisher -> Genre through the declared M2M (default and filter-omitting child querysets)
        m2m = ParentViewSet(name=ns.pub.name, attribute="publishers", many_to_many_through_attribute="genres")
        ns.genre = ViewSet(model=Genre, name=f"argenre{sfx}", parent=m2m)
        ns.GenreList, ns.GenreDetail = lst(ns.genre), det(ns.genre)
        ns.GenreCreate = create(ns.genre, ["name"])
        ns.cgenre = ViewSet(model=Genre, name=f"arcgenre{sfx}", parent=m2m.model_copy())
        ns.CGenreList = lst(ns.cgenre, get_queryset=_all_genres)
        ns.CGenreDetail = det(ns.cgenre, get_queryset=_all_genres)

        # UUID Author -> UUIDFragmentRow
        ns.author = ViewSet(model=Author, name=f"arauthor{sfx}")
        ns.row = ViewSet(
            model=UUIDFragmentRow, name=f"arrow{sfx}", parent=ParentViewSet(name=ns.author.name, attribute="author")
        )
        ns.RowDetail = det(ns.row)
        ns.crow = ViewSet(
            model=UUIDFragmentRow, name=f"arcrow{sfx}", parent=ParentViewSet(name=ns.author.name, attribute="author")
        )
        ns.CRowDetail = det(ns.crow, get_queryset=_all_rows)

        # scoped ancestors: protected, and provider none
        ns.tpub = TenantViewSet(model=Publisher, name=f"artpub{sfx}")
        ns.tbook = ViewSet(
            model=Book, name=f"artbook{sfx}", parent=ParentViewSet(name=ns.tpub.name, attribute="publisher")
        )
        ns.TBookList, ns.TBookDetail = lst(ns.tbook), det(ns.tbook)
        ns.opub = TenantViewSet(model=Publisher, name=f"aropub{sfx}", ancestor_policy=AncestorPolicy(provider="none"))
        ns.obook = ViewSet(
            model=Book, name=f"arobook{sfx}", parent=ParentViewSet(name=ns.opub.name, attribute="publisher")
        )
        ns.OBookList, ns.OBookDetail = lst(ns.obook), det(ns.obook)

        # Publisher (protected) -> Book (provider none: structural parent only) -> BookNote
        ns.open_book = ViewSet(
            model=Book,
            name=f"aropenbook{sfx}",
            parent=ParentViewSet(name=ns.pub.name, attribute="publisher"),
            ancestor_policy=AncestorPolicy(provider="none"),
        )
        ns.OpenBookList = lst(ns.open_book)
        ns.open_note = ViewSet(
            model=BookNote, name=f"aropennote{sfx}", parent=ParentViewSet(name=ns.open_book.name, attribute="book")
        )
        ns.OpenNoteList = lst(ns.open_note)
        ns.OpenNoteCreate = create(ns.open_note, ["note"], CreateViewPermissionRequired)

        # Guardian child object view whose queryset omits the parent filter
        ns.gpub = GuardianViewSet(model=Publisher, name=f"argpub{sfx}")
        ns.gbook = GuardianViewSet(
            model=Book, name=f"argbook{sfx}", parent=ParentViewSet(name=ns.gpub.name, attribute="publisher")
        )
        ns.GBookDetail = det(ns.gbook, GuardianDetailViewPermissionRequired, get_queryset=_all_books)

        routed = [
            ns.pub,
            ns.book,
            ns.note,
            *(c.vs for c in ns.cbook.values()),
            *(f.vs for f in ns.fbook.values()),
            ns.house,
            ns.genre,
            ns.cgenre,
            ns.author,
            ns.row,
            ns.crow,
            ns.tpub,
            ns.tbook,
            ns.opub,
            ns.obook,
            ns.open_book,
            ns.open_note,
            ns.gpub,
            ns.gbook,
        ]
        return ns, routed

    _register_project_viewsets()
    with isolated_routes(build) as ns:
        yield ns


@pytest.fixture
def world(db):
    penguin = Publisher.objects.create(name="Penguin")
    other = Publisher.objects.create(name="Other")
    hidden = Publisher.objects.create(name="hidden-tenant")
    book = Book.objects.create(title="Own", publisher=penguin)
    foreign = Book.objects.create(title="Foreign", publisher=other)
    hidden_book = Book.objects.create(title="Hidden", publisher=hidden)
    note = BookNote.objects.create(book=book, note="mine")
    foreign_note = BookNote.objects.create(book=foreign, note="theirs")
    genre = Genre.objects.create(name="Fiction")
    genre.publishers.add(penguin)
    stranger = Genre.objects.create(name="Poetry")
    stranger.publishers.add(other)
    author = Author.objects.create(first_name="Douglas", last_name="Adams")
    other_author = Author.objects.create(first_name="Terry", last_name="Pratchett")
    row = UUIDFragmentRow.objects.create(author=author, text="own row")
    foreign_row = UUIDFragmentRow.objects.create(author=other_author, text="foreign row")
    return SimpleNamespace(**locals())


def _kw(vs, obj):
    return {f"{vs.name}_pk": obj.pk}


def _superclient(name="ar_super"):
    return _client(User.objects.create_superuser(username=name, password="pw"))


def _publisher_reads(captured) -> list[str]:
    return [q["sql"] for q in captured.captured_queries if re.search(r'FROM "app_publisher"', q["sql"])]


@pytest.fixture
def queryset_calls(monkeypatch):
    """Every ViewSet queryset call: (ViewSet name, view, request, kwargs)."""
    calls = []
    original = ViewSet.get_queryset

    def spy(self, view):
        calls.append(SimpleNamespace(name=self.name, view=view, request=view.request, kwargs=view.kwargs))
        return original(self, view)

    monkeypatch.setattr(ViewSet, "get_queryset", spy)
    return calls


def _poison_endpoints(monkeypatch, *classes):
    def poison(self, *args, **kwargs):
        raise AssertionError(f"ancestor endpoint {type(self).__name__} was used")

    for cls in classes:
        for name in ("setup", "dispatch", "get_queryset", "get_object"):
            monkeypatch.setattr(cls, name, poison, raising=False)


def _apply_mode(vs, cascade):
    vs.ancestor_policy = AncestorPolicy(cascade=cascade)


MODES = pytest.mark.parametrize("cascade", [True, False], ids=["full", "nearest"])


# ── actual child view, configured URL argument, no ancestor endpoint ─────────


@pytest.mark.django_db
def test_ancestor_querysets_receive_the_actual_child_view_and_kwargs(res, world, queryset_calls, monkeypatch):
    _poison_endpoints(monkeypatch, res.PubList, res.PubDetail, res.BookList, res.BookDetail)
    kwargs = {**_kw(res.pub, world.penguin), **_kw(res.book, world.book), "pk": world.note.pk}
    response = _superclient().get(_url(res.note, "detail", **kwargs))
    assert response.status_code == 200
    by_name = {}
    for call in queryset_calls:
        by_name.setdefault(call.name, []).append(call)
    leaf_view = by_name[res.note.name][0].view
    assert isinstance(leaf_view, res.NoteDetail)
    for name in (res.pub.name, res.book.name):
        (call,) = by_name[name]  # one scoped read per ancestor, no retry
        assert call.view is leaf_view and call.request is leaf_view.request
        assert call.kwargs is leaf_view.kwargs  # the unchanged URL kwargs, the leaf pk included
        assert call.kwargs == {key: str(value) for key, value in kwargs.items()}
    assert leaf_view.cv_key == "detail" and leaf_view.kwargs["pk"] == str(world.note.pk)


@pytest.mark.django_db
def test_explicit_url_argument_resolves_its_own_ancestor(res, world):
    client = _superclient()
    ok = client.get(_url(res.house, "detail", house_pk=world.penguin.pk, pk=world.book.pk))
    assert ok.status_code == 200
    assert ok.context["object"] == world.book
    # the leaf pk is never used as the ancestor identity
    assert client.get(_url(res.house, "detail", house_pk=world.other.pk, pk=world.book.pk)).status_code == 404


@pytest.mark.django_db
def test_matching_numeric_keys_across_models_are_not_relationship_identity(res, world):
    """A Book whose pk equals the URL Publisher pk, and a BookNote under a Book of another Publisher."""
    client = _superclient()
    twin = Book.objects.create(title="Twin", publisher=world.other)
    target = Publisher.objects.filter(pk=twin.pk).first() or Publisher.objects.create(pk=twin.pk, name="Twin pk")
    assert target.pk == twin.pk and twin.publisher_id != target.pk
    assert client.get(_url(res.book, "detail", **_kw(res.pub, target), pk=twin.pk)).status_code == 404
    kwargs = {**_kw(res.pub, world.penguin), **_kw(res.book, world.foreign)}
    assert client.get(_url(res.note, "detail", **kwargs, pk=world.foreign_note.pk)).status_code == 404
    assert client.get(_url(res.note, "list", **kwargs)).status_code == 404


@pytest.mark.django_db
def test_uuid_relationships(res, world):
    client = _superclient()
    ok = client.get(_url(res.row, "detail", **_kw(res.author, world.author), pk=world.row.pk))
    assert ok.status_code == 200 and ok.context["object"] == world.row
    assert (
        client.get(_url(res.row, "detail", **_kw(res.author, world.author), pk=world.foreign_row.pk)).status_code == 404
    )
    # a filter-omitting child queryset still cannot reach another Author's row
    url = _url(res.crow, "detail", **_kw(res.author, world.author), pk=world.foreign_row.pk)
    assert client.get(url).status_code == 404
    assert client.get(_url(res.crow, "detail", **_kw(res.author, world.author), pk=world.row.pk)).status_code == 200


# ── ancestor queryset scope ──────────────────────────────────────────────────


@pytest.mark.django_db
@pytest.mark.parametrize("actor", ["superuser", "granted"])
@pytest.mark.parametrize("ancestor", ["protected-full", "protected-nearest", "none"])
def test_scoped_ancestor_exclusion_is_404_despite_grants(res, world, queryset_calls, actor, ancestor):
    if ancestor == "none":
        child = res.obook
    else:
        child = res.tbook
        _apply_mode(child, ancestor == "protected-full")
    parent = res.opub if ancestor == "none" else res.tpub
    if actor == "superuser":
        client = _superclient(f"ar_super_{ancestor}")
    else:
        client = _client(_user(f"ar_granted_{ancestor}", (Publisher, "view"), (Publisher, "change"), (Book, "view")))
    for key, extra in (("list", {}), ("detail", {"pk": world.hidden_book.pk})):
        queryset_calls.clear()
        with CaptureQueriesContext(connection) as captured:
            response = client.get(_url(child, key, **_kw(parent, world.hidden), **extra))
        assert response.status_code == 404, key
        assert len(_publisher_reads(captured)) == 1  # the scoped lookup only: no unfiltered retry
        assert [call.name for call in queryset_calls] == [parent.name]  # the child queryset is never reached
    visible = client.get(_url(child, "list", **_kw(parent, world.penguin)))
    assert visible.status_code == 200
    assert list(visible.context["object_list"]) == [world.book]


@pytest.fixture
def manager_scope(db):
    """An ancestor whose model manager excludes ``hidden*`` rows (a proxy of Publisher, no table)."""
    from crud_views.lib.views import DetailView, ListView

    _register_project_viewsets()
    with isolate_apps("tests.test1.app"):

        class VisibleManager(models.Manager):
            def get_queryset(self):
                return super().get_queryset().exclude(name__startswith="hidden")

        class VisiblePublisher(Publisher):
            objects = VisibleManager()

            class Meta:
                proxy = True
                app_label = "app"

        def build(sfx):
            pub = ViewSet(model=VisiblePublisher, name=f"armpub{sfx}")
            book = ViewSet(model=Book, name=f"armbook{sfx}", parent=ParentViewSet(name=pub.name, attribute="publisher"))
            type("List", (ListView,), {"cv_viewset": book, "cv_list_actions": [], "cv_context_actions": []})
            type("Detail", (DetailView,), {"cv_viewset": book, "cv_context_actions": []})
            return SimpleNamespace(pub=pub, book=book), [pub, book]

        with isolated_routes(build) as ns:
            yield ns


@pytest.mark.django_db
def test_manager_scope_exclusion_is_404_for_a_superuser(manager_scope, world):
    client = _superclient("ar_manager_super")
    with CaptureQueriesContext(connection) as captured:
        response = client.get(_url(manager_scope.book, "list", **_kw(manager_scope.pub, world.hidden)))
    assert response.status_code == 404
    assert len(_publisher_reads(captured)) == 1
    url = _url(manager_scope.book, "detail", **_kw(manager_scope.pub, world.hidden), pk=world.hidden_book.pk)
    assert client.get(url).status_code == 404
    assert client.get(_url(manager_scope.book, "list", **_kw(manager_scope.pub, world.penguin))).status_code == 200


# ── deep relationships, creates refused before attachment ────────────────────


@pytest.mark.django_db
@MODES
def test_deep_mismatch_is_404_and_create_is_refused_before_any_form(res, world, monkeypatch, cascade):
    _apply_mode(res.note, cascade)
    forms = []
    original = res.NoteCreate.get_form

    def form_spy(self, *args, **kwargs):
        forms.append(type(self))
        return original(self, *args, **kwargs)

    monkeypatch.setattr(res.NoteCreate, "get_form", form_spy)
    user = _user(f"ar_deep_{cascade}", (Publisher, "view"), (Publisher, "change"), (Book, "view"), (Book, "change"))
    client = _client(user)
    mismatched = {**_kw(res.pub, world.penguin), **_kw(res.book, world.foreign)}
    assert client.get(_url(res.note, "list", **mismatched)).status_code == 404
    assert client.get(_url(res.note, "detail", **mismatched, pk=world.foreign_note.pk)).status_code == 404
    before = BookNote.objects.count()
    assert client.post(_url(res.note, "create", **mismatched), {"note": "smuggled"}).status_code == 404
    assert BookNote.objects.count() == before and forms == []
    # control: the matching chain creates and attaches to its own Book
    matched = {**_kw(res.pub, world.penguin), **_kw(res.book, world.book)}
    assert client.post(_url(res.note, "create", **matched), {"note": "attached"}).status_code == 302
    assert BookNote.objects.get(note="attached").book_id == world.book.pk and forms


# ── reached child objects and collections belong to the resolved parent ──────


@pytest.mark.django_db
@pytest.mark.parametrize("op", ["detail", "update", "delete"])
@pytest.mark.parametrize("style", OVERRIDE_STYLES)
def test_filter_omitting_child_queryset_cannot_return_a_wrong_parent_object(res, world, monkeypatch, style, op):
    family = res.cbook[style]
    view_class = {"detail": family.Detail, "update": family.Update, "delete": family.Delete}[op]
    states = []

    @classmethod
    def state_spy(cls, user, obj=None):
        states.append(obj)
        return True

    monkeypatch.setattr(view_class, "cv_action_enabled", state_spy)
    client = _superclient(f"ar_cq_{style}_{op}")
    foreign = client.get(_url(family.vs, op, **_kw(res.pub, world.penguin), pk=world.foreign.pk))
    assert foreign.status_code == 404
    assert world.foreign not in states  # rejected before the state hook
    own = client.get(_url(family.vs, op, **_kw(res.pub, world.penguin), pk=world.book.pk))
    assert own.status_code == 200
    assert states and all(obj == world.book for obj in states)
    if op == "delete":
        assert client.post(_url(family.vs, op, **_kw(res.pub, world.penguin), pk=world.foreign.pk)).status_code == 404
        assert Book.objects.filter(pk=world.foreign.pk).exists()


@pytest.mark.django_db
@pytest.mark.parametrize("style", OVERRIDE_STYLES)
def test_filter_omitting_child_collection_is_scoped_to_the_resolved_parent(res, world, style):
    family = res.cbook[style]
    response = _superclient(f"ar_cl_{style}").get(_url(family.vs, "list", **_kw(res.pub, world.penguin)))
    assert response.status_code == 200
    assert list(response.context["object_list"]) == [world.book]


@pytest.mark.django_db
@pytest.mark.parametrize("kind", ["filter", "table"])
@pytest.mark.parametrize("style", OVERRIDE_STYLES)
@pytest.mark.parametrize("query", ["", "?title=", "?title=Foreign"])
def test_filtered_child_collection_is_scoped_to_the_resolved_parent(res, world, style, kind, query):
    """django-filter passes its collection as the ``object_list`` keyword; it is scoped like the plain list, and
    the table (which reads ``self.object_list``) renders the same rows."""
    family = res.fbook[style, kind]
    response = _superclient(f"ar_fl_{style}_{kind}").get(_url(family.vs, "list", **_kw(res.pub, world.penguin)) + query)
    assert response.status_code == 200
    expected = [] if query == "?title=Foreign" else [world.book]
    assert list(response.context["object_list"]) == expected
    if kind == "table":
        assert [row.record for row in response.context["table"].rows] == expected


@pytest.mark.django_db
def test_m2m_membership_for_default_and_filter_omitting_child_querysets(res, world):
    client = _superclient("ar_m2m")
    for vs in (res.genre, res.cgenre):
        member = client.get(_url(vs, "detail", **_kw(res.pub, world.penguin), pk=world.genre.pk))
        assert member.status_code == 200, vs.name
        stranger = client.get(_url(vs, "detail", **_kw(res.pub, world.penguin), pk=world.stranger.pk))
        assert stranger.status_code == 404, vs.name
        listed = client.get(_url(vs, "list", **_kw(res.pub, world.penguin)))
        assert list(listed.context["object_list"]) == [world.genre], vs.name


@pytest.mark.django_db
def test_guardian_child_object_from_a_filter_omitting_queryset_is_404(res, world):
    client = _superclient("ar_guardian")
    url = _url(res.gbook, "detail", **_kw(res.gpub, world.penguin), pk=world.foreign.pk)
    assert client.get(url).status_code == 404
    url = _url(res.gbook, "detail", **_kw(res.gpub, world.penguin), pk=world.book.pk)
    assert client.get(url).status_code == 200


# ── the structural parent: identity reuse for create, state and helpers ──────


def _state_parent(view):
    return view._cv_ancestor_state.parent


@pytest.mark.django_db
def test_fk_create_attaches_the_resolved_parent_identity(res, world, monkeypatch):
    seen = []
    original = res.BookCreate.cv_get_parent_object

    def spy(self):
        obj = original(self)
        seen.append((obj, _state_parent(self)))
        return obj

    monkeypatch.setattr(res.BookCreate, "cv_get_parent_object", spy)
    client = _client(_user("ar_fk_create", (Publisher, "change")))
    with CaptureQueriesContext(connection) as captured:
        response = client.post(_url(res.book, "create", **_kw(res.pub, world.penguin)), {"title": "Created"})
    assert response.status_code == 302
    assert Book.objects.get(title="Created").publisher_id == world.penguin.pk
    assert seen and all(obj is resolved for obj, resolved in seen)
    assert len(_publisher_reads(captured)) == 1


@pytest.mark.django_db
def test_m2m_create_uses_the_resolved_parent_and_keeps_through_defaults(res, world, monkeypatch):
    calls = []

    def through_defaults(self, instance, parent_instance, m2m):
        calls.append((instance, parent_instance, _state_parent(self)))
        return {}

    monkeypatch.setattr(res.GenreCreate, "cv_parent_many_to_many_through_defaults", through_defaults)
    client = _client(_user("ar_m2m_create", (Publisher, "change")))
    response = client.post(_url(res.genre, "create", **_kw(res.pub, world.penguin)), {"name": "Essays"})
    assert response.status_code == 302
    created = Genre.objects.get(name="Essays")
    assert list(created.publishers.all()) == [world.penguin]
    ((instance, parent, resolved),) = calls
    assert instance == created and parent is resolved and parent.pk == world.penguin.pk
    # a mismatched M2M parent never reaches the form or the attachment
    calls.clear()
    response = client.post(
        _url(res.genre, "create", **_kw(res.pub, Publisher(pk=world.penguin.pk + 1000))), {"name": "X"}
    )
    assert response.status_code == 404 and calls == [] and not Genre.objects.filter(name="X").exists()


@pytest.mark.django_db
def test_unprotected_immediate_parent_stays_the_structural_parent(res, world, monkeypatch):
    """Publisher (protected) -> Book (provider none) -> BookNote: the Publisher supplies the nearest gate, the
    Book is still the parent for attachment and the parent-state hook."""
    states = []

    @classmethod
    def state_spy(cls, user, obj=None):
        states.append(obj)
        return True

    monkeypatch.setattr(res.OpenNoteCreate, "cv_action_enabled", state_spy)
    kwargs = {**_kw(res.pub, world.penguin), **_kw(res.open_book, world.book)}
    viewer = _client(_user("ar_open_viewer", (Publisher, "view"), (BookNote, "add")))
    assert viewer.post(_url(res.open_note, "create", **kwargs), {"note": "denied"}).status_code == 403
    assert states == []  # the Publisher gate denies before the local state hook
    editor = _client(_user("ar_open_editor", (Publisher, "change"), (BookNote, "add")))
    response = editor.post(_url(res.open_note, "create", **kwargs), {"note": "structural"})
    assert response.status_code == 302
    assert BookNote.objects.get(note="structural").book_id == world.book.pk
    assert states and all(isinstance(obj, Book) and obj.pk == world.book.pk for obj in states)


def _guarded_view(view_class, user, **kwargs):
    request = RequestFactory().get("/")
    request.user = user
    view = view_class()
    view.setup(request, **kwargs)
    assert view._cv_ancestor_guard() is None
    return view


@pytest.mark.django_db
def test_rendering_a_higher_create_reuses_the_resolved_ancestor(res, world, monkeypatch):
    """A Book create control rendered on a BookNote page targets the Publisher two levels up: it receives the
    Publisher the note request already resolved, without another lookup."""
    states = []

    @classmethod
    def state_spy(cls, user, obj=None):
        states.append(obj)
        return True

    monkeypatch.setattr(res.BookCreate, "cv_action_enabled", state_spy)
    user = User.objects.create_superuser(username="ar_render", password="pw")
    note_list = _guarded_view(res.NoteList, user, **_kw(res.pub, world.penguin), **_kw(res.book, world.book))
    resolved_publisher = note_list._cv_ancestor_state.objects[1]
    with CaptureQueriesContext(connection) as captured:
        assert res.BookCreate._cv_action_enabled_for_rendering(user, None, note_list) is True
    assert states == [resolved_publisher] and states[0] is resolved_publisher
    assert captured.captured_queries == []


@pytest.mark.django_db
def test_rendering_outside_a_guarded_request_stays_bounded(res, world, monkeypatch):
    """Without a resolved request chain the helper keeps its single immediate lookup (existing behavior)."""
    states = []

    @classmethod
    def state_spy(cls, user, obj=None):
        states.append(obj)
        return True

    monkeypatch.setattr(res.BookCreate, "cv_action_enabled", state_spy)
    user = User.objects.create_superuser(username="ar_render_bounded", password="pw")
    request = RequestFactory().get("/")
    request.user = user
    note_list = res.NoteList()
    note_list.setup(request, **_kw(res.pub, world.penguin), **_kw(res.book, world.book))
    with CaptureQueriesContext(connection) as captured:
        assert res.BookCreate._cv_action_enabled_for_rendering(user, None, note_list) is True
    assert states == [world.penguin] and len(_publisher_reads(captured)) == 1


@pytest.mark.django_db
def test_resolved_chain_is_request_local(res, world, monkeypatch):
    seen = []
    original = ancestors._authorize_ancestors

    def spy(view):
        result = original(view)
        seen.append(view)
        return result

    monkeypatch.setattr(ancestors, "_authorize_ancestors", spy)
    client = _superclient("ar_local")
    assert client.get(_url(res.book, "list", **_kw(res.pub, world.penguin))).status_code == 200
    assert client.get(_url(res.book, "list", **_kw(res.pub, world.other))).status_code == 200
    first, second = seen
    assert first is not second
    assert _state_parent(first).pk == world.penguin.pk and _state_parent(second).pk == world.other.pk
    # nothing is stored on the view class or the ViewSets
    assert getattr(res.BookList, "_cv_ancestor_state", None) is None
    assert all(getattr(vs, "_cv_ancestor_state", None) is None for vs in (res.pub, res.book))
    # a revoked grant is evaluated again on the next request
    user = _user("ar_local_revoked", (Publisher, "view"))
    actor = _client(user)
    assert actor.get(_url(res.book, "list", **_kw(res.pub, world.penguin))).status_code == 200
    user.user_permissions.clear()
    assert Client().get(_url(res.book, "list", **_kw(res.pub, world.penguin))).status_code == 302
    assert actor.get(_url(res.book, "list", **_kw(res.pub, world.penguin))).status_code == 403
