"""
Phase 06.18 plan 03 — bounded immediate-parent helpers.

Rendering and access helpers that already check a resolved immediate structural parent (Guardian child
collection links, contextual create buttons, ``cv_create_has_access`` / ``cv_has_access`` of nested Guardian
creates and cancel availability) use ``crud_views.lib.ancestors._immediate_parent_access``:

* the immediate structural parent's own provider and fallback, with the target operation's *nearest* key;
* never a farther ancestor, never an ancestor lookup or queryset call (no full-chain rendering work);
* an immediate parent with provider ``"none"`` skips only that gate — actor, state and custom checks remain;
* unavailable context (no parent, ambiguous child-only M2M input) stays unavailable;
* invalid configuration (a key missing from the parent's permission map) raises;
* the request-resolved parent identity is reused when the rendering view supplies it; integer and UUID keys
  are passed through unchanged, and declarations are not mutated by repeated calls.
"""

from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ImproperlyConfigured
from django.db import connection
from django.test import RequestFactory
from django.test.utils import CaptureQueriesContext
from guardian.shortcuts import assign_perm

from crud_views.lib import ancestors
from crud_views.lib.viewset import AncestorPermissions, AncestorPolicy, ParentViewSet, ViewSet
from tests.test1.app.models import Author, Book, BookNote, Genre, Publisher, UUIDFragmentRow
from tests.test1.test_ancestor_authorization import _client, _url, _user, isolated_routes


@pytest.fixture
def helpers():
    """Guardian Publisher → Guardian Book → Guardian BookNote, a Guardian Book under a core Publisher, an M2M
    Guardian Genre, a Guardian Book with a custom Write pair, Book with provider ``none`` between Publisher and
    BookNote, and a UUID Guardian Author → Guardian UUIDFragmentRow chain."""
    from crud_views.lib.views import CreateViewParentMixin
    from crud_views_guardian.lib.views import (
        GuardianCreateViewPermissionRequired,
        GuardianDetailViewPermissionRequired,
        GuardianListViewPermissionRequired,
    )
    from crud_views_guardian.lib.viewset import GuardianViewSet

    def family(vs, fields):
        common = {"cv_viewset": vs, "cv_context_actions": []}
        return SimpleNamespace(
            vs=vs,
            List=type("List", (GuardianListViewPermissionRequired,), {**common, "cv_list_actions": []}),
            Detail=type("Detail", (GuardianDetailViewPermissionRequired,), dict(common)),
            Create=type(
                "Create", (CreateViewParentMixin, GuardianCreateViewPermissionRequired), {**common, "fields": fields}
            ),
        )

    def build(sfx):
        pub = GuardianViewSet(model=Publisher, name=f"ahpub{sfx}")
        cpub = ViewSet(model=Publisher, name=f"ahcpub{sfx}")
        book = GuardianViewSet(
            model=Book, name=f"ahbook{sfx}", parent=ParentViewSet(name=pub.name, attribute="publisher")
        )
        note = GuardianViewSet(
            model=BookNote, name=f"ahnote{sfx}", parent=ParentViewSet(name=book.name, attribute="book")
        )
        core_book = GuardianViewSet(
            model=Book, name=f"ahcbook{sfx}", parent=ParentViewSet(name=cpub.name, attribute="publisher")
        )
        genre = GuardianViewSet(
            model=Genre,
            name=f"ahgenre{sfx}",
            parent=ParentViewSet(name=pub.name, attribute="publishers", many_to_many_through_attribute="genres"),
        )
        odd = GuardianViewSet(
            model=Book,
            name=f"ahodd{sfx}",
            parent=ParentViewSet(name=pub.name, attribute="publisher"),
            ancestor_policy=AncestorPolicy(write=AncestorPermissions(nearest="approve", higher="view")),
        )
        open_book = GuardianViewSet(
            model=Book,
            name=f"ahopen{sfx}",
            parent=ParentViewSet(name=pub.name, attribute="publisher"),
            ancestor_policy=AncestorPolicy(provider="none"),
        )
        open_note = GuardianViewSet(
            model=BookNote, name=f"ahonote{sfx}", parent=ParentViewSet(name=open_book.name, attribute="book")
        )
        author = GuardianViewSet(model=Author, name=f"ahauthor{sfx}")
        row = GuardianViewSet(
            model=UUIDFragmentRow, name=f"ahrow{sfx}", parent=ParentViewSet(name=author.name, attribute="author")
        )
        ns = SimpleNamespace(
            pub=family(pub, ["name"]),
            cpub=cpub,
            book=family(book, ["title"]),
            note=family(note, ["note"]),
            core_book=family(core_book, ["title"]),
            genre=family(genre, ["name"]),
            odd=family(odd, ["title"]),
            open_book=family(open_book, ["title"]),
            open_note=family(open_note, ["note"]),
            author=family(author, ["first_name", "last_name"]),
            row=family(row, ["text"]),
        )
        routed = [pub, cpub, book, note, core_book, genre, odd, open_book, open_note, author, row]
        return ns, routed

    with isolated_routes(build) as ns:
        yield ns


@pytest.fixture
def data(db):
    penguin = Publisher.objects.create(name="Penguin")
    other = Publisher.objects.create(name="Other")
    book = Book.objects.create(title="Hitchhiker", publisher=penguin)
    genre = Genre.objects.create(name="Fiction")
    genre.publishers.add(penguin, other)
    author = Author.objects.create(first_name="Douglas", last_name="Adams")
    return SimpleNamespace(penguin=penguin, other=other, book=book, genre=genre, author=author)


def _grant(user, family, action, obj):
    assign_perm(family.vs.permissions[action], user, obj)


@pytest.fixture
def provider_calls(monkeypatch):
    """Every ancestor provider call: (ViewSet name, permission, object)."""
    from crud_views_guardian.lib.viewset import GuardianViewSet

    calls: list[tuple[str, str, object]] = []
    originals = {cls: cls._ancestor_has_permission for cls in (ViewSet, GuardianViewSet)}

    def spy_for(cls):
        def spy(self, user, permission, obj, *, view):
            calls.append((self.name, permission, obj))
            return originals[cls](self, user, permission, obj, view=view)

        return spy

    for cls in originals:
        monkeypatch.setattr(cls, "_ancestor_has_permission", spy_for(cls))
    return calls


@pytest.fixture
def lookups(monkeypatch):
    calls: list[str] = []
    original = ViewSet.get_queryset

    def spy(self, view):
        calls.append(self.name)
        return original(self, view)

    monkeypatch.setattr(ViewSet, "get_queryset", spy)
    return calls


def _bound(view_class, user, **kwargs):
    """A view instance set up for one GET request (as Django's as_view() would before dispatch)."""
    request = RequestFactory().get("/")
    request.user = user
    view = view_class()
    view.setup(request, **kwargs)
    return view


# ── provider and nearest key of the immediate parent ─────────────────────────


@pytest.mark.django_db
def test_immediate_parent_uses_the_target_operation_nearest_key(helpers, data):
    viewer = _user("ah_viewer")
    _grant(viewer, helpers.pub, "view", data.penguin)
    editor = _user("ah_editor")
    _grant(editor, helpers.pub, "change", data.penguin)
    # Read (list): nearest view; Write (create): nearest change
    assert ancestors._immediate_parent_access(helpers.book.List, viewer, data.penguin) is True
    assert ancestors._immediate_parent_access(helpers.book.Create, viewer, data.penguin) is False
    assert ancestors._immediate_parent_access(helpers.book.Create, editor, data.penguin) is True
    assert ancestors._immediate_parent_access(helpers.book.List, editor, data.penguin) is False
    # another parent row is not covered by the grant
    assert ancestors._immediate_parent_access(helpers.book.Create, editor, data.other) is False


@pytest.mark.django_db
def test_create_helpers_follow_the_immediate_parent_policy(helpers, data):
    viewer = _user("ah_create_viewer")
    _grant(viewer, helpers.pub, "view", data.penguin)
    editor = _user("ah_create_editor")
    _grant(editor, helpers.pub, "change", data.penguin)
    create = helpers.book.Create
    for helper in (
        lambda user, obj: create.cv_has_access(user, obj),
        lambda user, obj: create.cv_create_has_access(user, None, obj),
    ):
        assert helper(editor, data.penguin) is True
        assert helper(viewer, data.penguin) is False
        # a single-FK own-child input resolves its parent
        assert helper(editor, data.book) is True
        assert helper(viewer, data.book) is False
        # no context stays unavailable
        assert helper(editor, None) is False


@pytest.mark.django_db
def test_child_collection_link_uses_the_target_read_requirement(helpers, data):
    viewer = _user("ah_link_viewer")
    _grant(viewer, helpers.pub, "view", data.penguin)
    editor = _user("ah_link_editor")
    _grant(editor, helpers.pub, "change", data.penguin)
    assert helpers.book.List._cv_child_link_has_access(viewer, data.penguin) is True
    assert helpers.book.List._cv_child_link_has_access(editor, data.penguin) is False
    assert helpers.book.List._cv_child_link_has_access(viewer, data.other) is False


@pytest.mark.django_db
def test_core_immediate_parent_uses_model_permissions(helpers, data):
    object_only = _user("ah_core_object")
    assign_perm("app.change_publisher", object_only, data.penguin)
    model_only = _user("ah_core_model", (Publisher, "change"))
    assert helpers.core_book.Create.cv_has_access(object_only, data.penguin) is False
    assert helpers.core_book.Create.cv_has_access(model_only, data.penguin) is True


@pytest.mark.django_db
def test_ambiguous_m2m_child_input_stays_unavailable(helpers, data, provider_calls):
    editor = _user("ah_m2m_editor")
    _grant(editor, helpers.pub, "change", data.penguin)
    create = helpers.genre.Create
    assert create.cv_has_access(editor, data.genre) is False  # a Genre names no single parent
    assert create.cv_create_has_access(editor, None, data.genre) is False
    assert provider_calls == []  # nothing is guessed, no permission is evaluated
    assert create.cv_has_access(editor, data.penguin) is True  # an explicit parent works


@pytest.mark.django_db
def test_invalid_nearest_key_surfaces_as_configuration_error(helpers, data):
    editor = _user("ah_invalid_key")
    with pytest.raises(ImproperlyConfigured, match="approve"):
        ancestors._immediate_parent_access(helpers.odd.Create, editor, data.penguin)
    with pytest.raises(ImproperlyConfigured, match="approve"):
        helpers.odd.Create.cv_has_access(editor, data.penguin)


# ── provider none and farther ancestors ──────────────────────────────────────


@pytest.mark.django_db
def test_none_immediate_parent_skips_only_its_gate(helpers, data, provider_calls, lookups):
    nobody = _user("ah_none_nobody")  # no grant on Publisher or Book
    create = helpers.open_note.Create
    with CaptureQueriesContext(connection) as captured:
        assert ancestors._immediate_parent_access(create, nobody, data.book) is True
        assert create.cv_has_access(nobody, data.book) is True
        assert create.cv_create_has_access(nobody, None, data.book) is True
    # the farther protected Publisher is never evaluated for rendering, nothing is looked up
    assert provider_calls == []
    assert lookups == []
    assert captured.captured_queries == []
    # the request itself selects Publisher (nearest protected ancestor) and denies
    url = _url(
        helpers.open_note.vs,
        "create",
        **{f"{helpers.pub.vs.name}_pk": data.penguin.pk, f"{helpers.open_book.vs.name}_pk": data.book.pk},
    )
    assert _client(nobody).get(url).status_code == 403


@pytest.mark.django_db
def test_none_immediate_parent_retains_actor_and_state_checks(helpers, data, monkeypatch):
    create = helpers.open_note.Create
    inactive = _user("ah_none_inactive")
    inactive.is_active = False
    assert create.cv_has_access(inactive, data.book) is False
    assert create.cv_create_has_access(inactive, None, data.book) is False
    seen = []

    def state(cls, user, obj=None):
        seen.append(obj)
        return False

    monkeypatch.setattr(create, "cv_action_enabled", classmethod(state))
    active = _user("ah_none_active")
    assert create._cv_action_enabled_for_context(active, data.book) is False
    assert seen == [data.book]  # the custom hook still receives the structural parent


@pytest.mark.django_db
def test_helper_never_evaluates_a_farther_ancestor(helpers, data, provider_calls, lookups):
    editor = _user("ah_deep_editor")
    _grant(editor, helpers.book, "change", data.book)  # only the immediate Book parent
    assert ancestors._immediate_parent_access(helpers.note.Create, editor, data.book) is True
    assert [(name, perm) for name, perm, _ in provider_calls] == [(helpers.book.vs.name, "app.change_book")]
    assert lookups == []


# ── identity and declarations ────────────────────────────────────────────────


@pytest.mark.django_db
def test_rendering_view_reuses_the_request_resolved_parent(helpers, data, provider_calls):
    editor = _user("ah_identity")
    _grant(editor, helpers.pub, "view", data.penguin)
    _grant(editor, helpers.pub, "change", data.penguin)
    view = _bound(helpers.book.List, editor, **{f"{helpers.pub.vs.name}_pk": data.penguin.pk})
    assert view._cv_ancestor_guard() is None
    resolved = view.cv_get_parent_object()
    provider_calls.clear()
    equal_copy = Publisher.objects.get(pk=data.penguin.pk)
    assert equal_copy is not resolved
    assert helpers.book.Create.cv_create_has_access(editor, view, equal_copy) is True
    assert provider_calls[-1][2] is resolved  # the request-resolved identity, not the equal copy
    # a different row is never replaced by the resolved parent
    assert helpers.book.Create.cv_create_has_access(editor, view, data.other) is False
    assert provider_calls[-1][2] is data.other


@pytest.mark.django_db
def test_uuid_parent_identity_and_declarations_survive_repeated_calls(helpers, data, provider_calls):
    editor = _user("ah_uuid_editor")
    _grant(editor, helpers.author, "change", data.author)
    create = helpers.row.Create
    before = (
        create.cv_viewset.ancestor_policy.model_dump(),
        create.cv_viewset.parent.model_dump(),
        dict(create.cv_viewset.permissions),
    )
    pk = data.author.pk
    for _ in range(3):
        assert ancestors._immediate_parent_access(create, editor, data.author) is True
        assert create.cv_has_access(editor, data.author) is True
    assert all(obj is data.author for _, _, obj in provider_calls)
    assert isinstance(data.author.pk, uuid.UUID) and data.author.pk == pk
    after = (
        create.cv_viewset.ancestor_policy.model_dump(),
        create.cv_viewset.parent.model_dump(),
        dict(create.cv_viewset.permissions),
    )
    assert after == before


@pytest.mark.django_db
def test_anonymous_and_inactive_actors_get_no_create_access(helpers, data):
    create = helpers.book.Create
    assert create.cv_has_access(AnonymousUser(), data.penguin) is False
    inactive = _user("ah_inactive", superuser=True)
    inactive.is_active = False
    assert create.cv_has_access(inactive, data.penguin) is False
    assert helpers.book.List._cv_child_link_has_access(inactive, data.penguin) is False


# ── request helpers: list-page create button and cancel availability ─────────


@pytest.mark.django_db
@pytest.mark.parametrize("grant", ["view", "view+change"])
def test_list_page_create_button_uses_the_resolved_parent(helpers, data, monkeypatch, grant):
    user = _user(f"ah_button_{grant.replace('+', '_')}")
    for action in grant.split("+"):
        _grant(user, helpers.pub, action, data.penguin)
    monkeypatch.setattr(helpers.book.List, "cv_context_actions", ["create"])
    url = _url(helpers.book.vs, "list", **{f"{helpers.pub.vs.name}_pk": data.penguin.pk})
    create_url = _url(helpers.book.vs, "create", **{f"{helpers.pub.vs.name}_pk": data.penguin.pk})
    with CaptureQueriesContext(connection) as captured:
        response = _client(user).get(url)
    assert response.status_code == 200
    assert (create_url in response.content.decode()) is (grant == "view+change")
    publisher_reads = [q for q in captured.captured_queries if 'FROM "app_publisher"' in q["sql"]]
    assert len(publisher_reads) == 1  # the button reuses the guard's parent


@pytest.mark.django_db
def test_cancel_availability_uses_the_immediate_parent_policy(helpers, data):
    viewer = _user("ah_cancel_viewer")
    _grant(viewer, helpers.pub, "view", data.penguin)
    editor = _user("ah_cancel_editor")
    _grant(editor, helpers.pub, "view", data.penguin)
    _grant(editor, helpers.pub, "change", data.penguin)
    kwargs = {f"{helpers.pub.vs.name}_pk": data.penguin.pk}
    for user, list_ok, create_ok in ((viewer, True, False), (editor, True, True)):
        view = _bound(helpers.book.List, user, **kwargs)
        assert view._cv_ancestor_guard() is None
        assert helpers.book.List._cv_cancel_target_available(user, None, view) is list_ok
        assert helpers.book.Create._cv_cancel_target_available(user, None, view) is create_ok


@pytest.mark.django_db
def test_cancel_availability_of_none_parent_retains_state(helpers, data, monkeypatch):
    nobody = _user("ah_cancel_none")
    _grant(nobody, helpers.pub, "view", data.penguin)  # reaches the open Book list (nearest protected: Publisher)
    kwargs = {f"{helpers.pub.vs.name}_pk": data.penguin.pk, f"{helpers.open_book.vs.name}_pk": data.book.pk}
    view = _bound(helpers.open_note.List, nobody, **kwargs)
    assert view._cv_ancestor_guard() is None
    create = helpers.open_note.Create
    assert create._cv_cancel_target_available(nobody, None, view) is True
    monkeypatch.setattr(create, "cv_action_enabled", classmethod(lambda cls, user, obj=None: False))
    assert create._cv_cancel_target_available(nobody, None, view) is False
