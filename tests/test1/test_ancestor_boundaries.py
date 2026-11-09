"""
Phase 06.18 plan 10 Task 1 — the URL-path mutation boundary and fresh-request authorization (ANCE-05, ANCE-08).

Passing ancestry authorizes the declared URL path only (D-19, D-21, D-52). Writes through that path keep their
normal semantics:

* a shared M2M child edited through parent A changes the shared row for B too, and B is never checked;
* an ordinary delete through A deletes the shared row (it is not turned into unlinking it from A);
* a valid form with an editable parent FK can move the child from A to B: A's path authorizes it, B gets no
  automatic destination gate, and the framework pins nothing. An application that wants to forbid moves
  excludes the field from its form (an application choice, shown as an allowed control).

Grants are evaluated on every request (D-20, D-22): a direct or group Guardian grant and a model grant revoked
between two requests deny the second one before any downstream work. Resolved objects and the Guardian checker
live on the view instance of one request; nothing authorizes another request, not even one that runs while the
first is still in flight. Django's per-user-instance permission cache is caller-held state: the framework does
not invalidate it, and a fresh request never reuses it.

Ancestors are Guardian ViewSets (strict object grants, so path A and path B are distinguishable), at one ancestor
(Publisher) and three ancestors (Publisher → Book → BookNote), in both cascade modes. Leaf views are core
permission-required views whose model grants (the local gates) pass. Every fixture builds fresh ViewSets behind a
temporary ROOT_URLCONF and restores registry and caches; the three-ancestor leaf is a test-scoped model.
"""

from __future__ import annotations

from contextlib import contextmanager
from types import SimpleNamespace

import pytest
from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType
from django.db import connection, models
from django.test import Client
from django.test.utils import isolate_apps
from guardian.shortcuts import assign_perm, remove_perm

import tests.test1.project.urls  # noqa: F401 - registers the shared app ViewSets before any registry snapshot
from crud_views.lib import ancestors
from crud_views.lib.viewset import AncestorPolicy, ParentViewSet, ViewSet
from tests.test1 import test_ancestor_authorization as _auth
from tests.test1.app.models import Book, BookNote, Genre, Publisher
from tests.test1.test_ancestor_authorization import _client, _url, isolated_routes

events = _auth.events  # ordered ViewSet queryset / has_perm spy of plan 01

# one ancestor uses the shared app models; three ancestors add a test-scoped table (schema edits need a
# transactional database)
DEPTHS = (
    pytest.param(1, id="depth1", marks=pytest.mark.django_db),
    pytest.param(3, id="depth3", marks=pytest.mark.django_db(transaction=True)),
)
DEPTH3 = DEPTHS[1:]
MODES = {"full": True, "nearest": False}

# ── test-scoped three-ancestor leaf ──────────────────────────────────────────


@contextmanager
def _boundary_leaf_model():
    """A leaf below Publisher → Book → BookNote with an editable FK (``note``) and a shared M2M
    (``shared_notes``) to BookNote. Hidden reverse accessors keep the real BookNote class unchanged."""
    with isolate_apps("tests.test1.app") as isolated:

        class BoundaryLeaf(models.Model):
            note = models.ForeignKey(BookNote, on_delete=models.CASCADE, related_name="+")
            shared_notes = models.ManyToManyField(BookNote, related_name="+")
            text = models.CharField(max_length=100)

            class Meta:
                app_label = "app"
                ordering = ["text"]

        # BookNote lives in the project registry: complete the relations that wait for it in the isolated one
        # (the M2M and its auto-created through model are otherwise left half-initialized)
        isolated.do_pending_operations(BookNote)
        with connection.schema_editor() as editor:
            editor.create_model(BoundaryLeaf)
        try:
            ct = ContentType.objects.get_for_model(BoundaryLeaf)
            for action in ("add", "change", "delete", "view"):
                Permission.objects.get_or_create(
                    content_type=ct, codename=f"{action}_{ct.model}", defaults={"name": f"Can {action} leaf"}
                )
            yield BoundaryLeaf
        finally:
            with connection.schema_editor() as editor:
                editor.delete_model(BoundaryLeaf)
            ContentType.objects.clear_cache()


@pytest.fixture
def leaf_model(depth):
    """None at one ancestor (Book/Genre are the leaves); the test-scoped leaf at three ancestors."""
    if depth == 1:
        yield None
        return
    with _boundary_leaf_model() as model:
        yield model


# ── routes and data ──────────────────────────────────────────────────────────


def _leaf_spec(depth, leaf_model):
    if depth == 1:
        return SimpleNamespace(
            fk_model=Book, fk_attr="publisher", fk_text="title", mm_model=Genre, mm_attr="publishers",
            mm_text="name", mm_through="genres",
        )  # fmt: skip
    return SimpleNamespace(
        fk_model=leaf_model, fk_attr="note", fk_text="text", mm_model=leaf_model, mm_attr="shared_notes",
        mm_text="text", mm_through=None,
    )  # fmt: skip


def _build_routes(depth, leaf_model):
    from crud_views.lib.views import (
        DeleteViewPermissionRequired,
        DetailViewPermissionRequired,
        ListViewPermissionRequired,
        UpdateViewPermissionRequired,
    )
    from crud_views_guardian.lib.viewset import GuardianViewSet

    spec = _leaf_spec(depth, leaf_model)

    def build(sfx):
        ancestor_models = [Publisher] if depth == 1 else [Publisher, Book, BookNote]
        fk_names = ["publisher", "book"]
        chain, parent = [], None
        for index, model in enumerate(ancestor_models):
            kwargs = {"model": model, "name": f"bd{index}{sfx}"}
            if parent is not None:
                kwargs["parent"] = ParentViewSet(name=parent.name, attribute=fk_names[index - 1])
            parent = GuardianViewSet(**kwargs)
            chain.append(parent)
        nearest = chain[-1]
        fk_vs = ViewSet(
            model=spec.fk_model, name=f"bdfk{sfx}", parent=ParentViewSet(name=nearest.name, attribute=spec.fk_attr)
        )
        mm_vs = ViewSet(
            model=spec.mm_model,
            name=f"bdmm{sfx}",
            parent=ParentViewSet(
                name=nearest.name, attribute=spec.mm_attr, many_to_many_through_attribute=spec.mm_through
            ),
        )

        def views(vs, fields):
            common = {"cv_viewset": vs, "cv_context_actions": [], "__module__": __name__}
            type("List", (ListViewPermissionRequired,), {**common, "cv_list_actions": []})
            type("Detail", (DetailViewPermissionRequired,), dict(common))
            type("Update", (UpdateViewPermissionRequired,), {**common, "fields": fields})
            type("Delete", (DeleteViewPermissionRequired,), dict(common))

        views(fk_vs, [spec.fk_text, spec.fk_attr])  # the parent FK is an ordinary editable form field
        views(mm_vs, [spec.mm_text])
        # application-owned restriction: an editor of the same ViewSet whose form excludes the parent field
        type(
            "Rename",
            (UpdateViewPermissionRequired,),
            {**{"cv_viewset": fk_vs, "cv_context_actions": [], "__module__": __name__}, "cv_key": "rename",
             "cv_path": "rename", "fields": [spec.fk_text]},
        )  # fmt: skip
        ns = SimpleNamespace(chain=chain, nearest=nearest, fk_vs=fk_vs, mm_vs=mm_vs, spec=spec, depth=depth)
        return ns, [*chain, fk_vs, mm_vs]

    return build


@pytest.fixture
def routes(depth, leaf_model):
    with isolated_routes(_build_routes(depth, leaf_model)) as ns:
        yield ns


def _path(depth, tag):
    publisher = Publisher.objects.create(name=f"pub-{tag}")
    if depth == 1:
        return [publisher]
    book = Book.objects.create(title=f"book-{tag}", publisher=publisher)
    return [publisher, book, BookNote.objects.create(book=book, note=f"note-{tag}")]


@pytest.fixture
def world(routes):
    """Two disjoint URL paths A and B; a child of A that may move, and a child shared by A and B."""
    depth, spec = routes.depth, routes.spec
    a, b = _path(depth, "a"), _path(depth, "b")
    if depth == 1:
        moving = Book.objects.create(title="moving", publisher=a[-1])
        shared = Genre.objects.create(name="shared")
    else:
        moving = spec.fk_model.objects.create(text="moving", note=a[-1])
        shared = spec.mm_model.objects.create(text="shared", note=a[-1])
    getattr(shared, spec.mm_attr).add(a[-1], b[-1])
    return SimpleNamespace(a=a, b=b, moving=moving, shared=shared)


def _kwargs(routes, path):
    return {f"{vs.name}_pk": obj.pk for vs, obj in zip(routes.chain, path, strict=True)}


def _leaf_url(routes, vs, key, path, **extra):
    return _url(vs, key, **_kwargs(routes, path), **extra)


def _apply_mode(routes, mode):
    for vs in (routes.fk_vs, routes.mm_vs):
        vs.ancestor_policy = AncestorPolicy(cascade=MODES[mode])


def _grant_path(user_or_group, routes, path, *, levels):
    """Object view+change on the selected ancestors of ``path`` (indexes into the chain)."""
    for index in levels:
        for action in ("view", "change"):
            assign_perm(routes.chain[index].permissions[action], user_or_group, path[index])


def _all_levels(routes):
    return range(len(routes.chain))


def _mode_levels(routes, mode):
    """The ancestors a request in ``mode`` gates: all of them (full) or only the nearest (nearest-only)."""
    return _all_levels(routes) if mode == "full" else [len(routes.chain) - 1]


def _local_grants(user, routes):
    for model in {routes.spec.fk_model, routes.spec.mm_model}:
        ct = ContentType.objects.get_for_model(model)
        for action in ("view", "change", "delete"):
            user.user_permissions.add(Permission.objects.get(content_type=ct, codename=f"{action}_{ct.model}"))


def _editor(routes, world, mode, name="bd_editor"):
    """Actor with exactly the grants ``mode`` needs on path A (none on path B) plus the local leaf gates."""
    user = User.objects.create_user(username=name, password="pw")
    _grant_path(user, routes, world.a, levels=_mode_levels(routes, mode))
    _local_grants(user, routes)
    return user


def _reader_of_b(routes, world):
    user = User.objects.create_user(username="bd_reader_b", password="pw")
    _grant_path(user, routes, world.b, levels=_all_levels(routes))
    _local_grants(user, routes)
    return user


# ── ancestor spies ───────────────────────────────────────────────────────────


@pytest.fixture
def ancestry(monkeypatch):
    """Every ancestor the guard resolved, every provider gate it evaluated and every child membership check, as
    ``(viewset name, object pk)`` — the objects the request actually traversed."""
    from crud_views_guardian.lib.viewset import GuardianViewSet

    recorded = SimpleNamespace(resolved=[], gated=[], membership=[])
    original_resolve = ancestors._resolve_ancestor
    original_member = ancestors._validate_child_parent
    original_gate = GuardianViewSet._ancestor_has_permission

    def resolve_spy(view, edge, ancestor, outer):
        obj = original_resolve(view, edge, ancestor, outer)
        recorded.resolved.append((ancestor.name, obj.pk))
        return obj

    def gate_spy(self, user, permission, obj, *, view):
        recorded.gated.append((self.name, obj.pk))
        return original_gate(self, user, permission, obj, view=view)

    def member_spy(view, obj):
        edge = ancestors._child_edge(view)
        if edge is not None:
            recorded.membership.append((obj.pk, edge[1].pk))
        return original_member(view, obj)

    monkeypatch.setattr(ancestors, "_resolve_ancestor", resolve_spy)
    monkeypatch.setattr(ancestors, "_validate_child_parent", member_spy)
    monkeypatch.setattr(GuardianViewSet, "_ancestor_has_permission", gate_spy)
    return recorded


def _path_pairs(routes, path, levels=None):
    levels = _all_levels(routes) if levels is None else levels
    return [(routes.chain[index].name, path[index].pk) for index in levels]


def _assert_only_path_a(routes, world, ancestry, mode):
    """The request traversed path A only: every A ancestor resolved once (both modes), the mode's gates
    evaluated once each, membership checked against A's nearest parent — and nothing of path B."""
    assert sorted(ancestry.resolved) == sorted(_path_pairs(routes, world.a))
    assert sorted(ancestry.gated) == sorted(_path_pairs(routes, world.a, _mode_levels(routes, mode)))
    assert {parent for _, parent in ancestry.membership} <= {world.a[-1].pk}
    b_pairs = set(_path_pairs(routes, world.b))
    assert b_pairs.isdisjoint(ancestry.resolved) and b_pairs.isdisjoint(ancestry.gated)


def _memberships(model, attr, pk):
    """Rows of the M2M through table for child ``pk`` (read directly: the test-scoped leaf's reverse query name
    is not known to the project registry's BookNote)."""
    field = model._meta.get_field(attr)
    return field.remote_field.through.objects.filter(**{field.m2m_field_name(): pk})


def _members(obj, attr):
    field = type(obj)._meta.get_field(attr)
    return set(_memberships(type(obj), attr, obj.pk).values_list(f"{field.m2m_reverse_field_name()}_id", flat=True))


# ── mutation boundary ────────────────────────────────────────────────────────


@pytest.mark.parametrize("mode", list(MODES))
@pytest.mark.parametrize("depth", DEPTHS)
def test_shared_m2m_edit_through_a_changes_the_row_for_b_without_authorizing_b(routes, world, ancestry, mode):
    _apply_mode(routes, mode)
    spec = routes.spec
    response = _client(_editor(routes, world, mode)).post(
        _leaf_url(routes, routes.mm_vs, "update", world.a, pk=world.shared.pk), {spec.mm_text: "edited"}
    )
    assert response.status_code == 302, response.content[:500]
    _assert_only_path_a(routes, world, ancestry, mode)
    shared = spec.mm_model.objects.get(pk=world.shared.pk)
    assert getattr(shared, spec.mm_text) == "edited"
    assert _members(shared, spec.mm_attr) == {world.a[-1].pk, world.b[-1].pk}  # memberships untouched

    # the same row, reached through B by an actor authorized for B, shows the edit
    detail = _client(_reader_of_b(routes, world)).get(
        _leaf_url(routes, routes.mm_vs, "detail", world.b, pk=world.shared.pk)
    )
    assert detail.status_code == 200
    assert getattr(detail.context["object"], spec.mm_text) == "edited"


@pytest.mark.parametrize("mode", list(MODES))
@pytest.mark.parametrize("depth", DEPTHS)
def test_editor_of_a_is_not_authorized_for_b(routes, world, ancestry, mode):
    """Control: editing the shared row through A did not need B — and does not grant B either."""
    _apply_mode(routes, mode)
    response = _client(_editor(routes, world, mode)).post(
        _leaf_url(routes, routes.mm_vs, "update", world.b, pk=world.shared.pk), {routes.spec.mm_text: "via b"}
    )
    assert response.status_code == 403
    assert getattr(routes.spec.mm_model.objects.get(pk=world.shared.pk), routes.spec.mm_text) == "shared"


@pytest.mark.parametrize("mode", list(MODES))
@pytest.mark.parametrize("depth", DEPTHS)
def test_ordinary_delete_through_a_deletes_the_shared_row(routes, world, ancestry, mode):
    _apply_mode(routes, mode)
    spec = routes.spec
    assert _memberships(spec.mm_model, spec.mm_attr, world.shared.pk).count() == 2
    response = _client(_editor(routes, world, mode)).post(
        _leaf_url(routes, routes.mm_vs, "delete", world.a, pk=world.shared.pk)
    )
    assert response.status_code == 302, response.content[:500]
    _assert_only_path_a(routes, world, ancestry, mode)
    # deleted, not unlinked from A: the row and B's membership are gone with it
    assert not spec.mm_model.objects.filter(pk=world.shared.pk).exists()
    assert _memberships(spec.mm_model, spec.mm_attr, world.shared.pk).count() == 0
    assert all(type(obj).objects.filter(pk=obj.pk).exists() for obj in [*world.a, *world.b])  # parents remain


@pytest.mark.parametrize("mode", list(MODES))
@pytest.mark.parametrize("depth", DEPTHS)
def test_editable_parent_fk_move_from_a_to_b_has_no_destination_gate(routes, world, ancestry, mode):
    _apply_mode(routes, mode)
    spec = routes.spec
    editor = _editor(routes, world, mode)  # no grant at all on path B
    client = _client(editor)
    response = client.post(
        _leaf_url(routes, routes.fk_vs, "update", world.a, pk=world.moving.pk),
        {spec.fk_text: "moved", spec.fk_attr: world.b[-1].pk},
    )
    assert response.status_code == 302, response.content[:500]
    _assert_only_path_a(routes, world, ancestry, mode)
    moved = spec.fk_model.objects.get(pk=world.moving.pk)
    assert getattr(moved, f"{spec.fk_attr}_id") == world.b[-1].pk
    assert getattr(moved, spec.fk_text) == "moved"

    # the move authorized nothing for B, and A's path no longer reaches the moved row
    assert client.get(_leaf_url(routes, routes.fk_vs, "detail", world.b, pk=world.moving.pk)).status_code == 403
    assert client.get(_leaf_url(routes, routes.fk_vs, "detail", world.a, pk=world.moving.pk)).status_code == 404


@pytest.mark.parametrize("mode", list(MODES))
@pytest.mark.parametrize("depth", DEPTHS)
def test_move_still_needs_the_original_path_authorization(routes, world, ancestry, mode):
    """Control: the move is a write through A, so A's nearest change gate applies (view alone is denied)."""
    _apply_mode(routes, mode)
    spec = routes.spec
    user = User.objects.create_user(username="bd_viewer", password="pw")
    for index in _all_levels(routes):
        assign_perm(routes.chain[index].permissions["view"], user, world.a[index])
    _local_grants(user, routes)
    response = _client(user).post(
        _leaf_url(routes, routes.fk_vs, "update", world.a, pk=world.moving.pk),
        {spec.fk_text: "moved", spec.fk_attr: world.b[-1].pk},
    )
    assert response.status_code == 403
    assert getattr(spec.fk_model.objects.get(pk=world.moving.pk), f"{spec.fk_attr}_id") == world.a[-1].pk


@pytest.mark.parametrize("mode", list(MODES))
@pytest.mark.parametrize("depth", DEPTHS)
def test_application_owned_form_exclusion_keeps_the_child_under_a(routes, world, ancestry, mode):
    """Allowed control: an application forbids moves by leaving the parent field out of its form. The framework
    adds no pinning of its own — the submitted parent value is simply not a form field here."""
    _apply_mode(routes, mode)
    spec = routes.spec
    response = _client(_editor(routes, world, mode)).post(
        _leaf_url(routes, routes.fk_vs, "rename", world.a, pk=world.moving.pk),
        {spec.fk_text: "renamed", spec.fk_attr: world.b[-1].pk},
    )
    assert response.status_code == 302, response.content[:500]
    _assert_only_path_a(routes, world, ancestry, mode)
    kept = spec.fk_model.objects.get(pk=world.moving.pk)
    assert getattr(kept, f"{spec.fk_attr}_id") == world.a[-1].pk
    assert getattr(kept, spec.fk_text) == "renamed"


# ── fresh-request revocation ─────────────────────────────────────────────────


def _queryset_calls(events, vs) -> int:
    return sum(1 for event in events if event == ("queryset", vs.name))


def _revoke(routes, world, holder, index, action):
    remove_perm(routes.chain[index].permissions[action], holder, world.a[index])


@pytest.mark.parametrize("kind", ["direct", "group"])
@pytest.mark.parametrize("mode", list(MODES))
@pytest.mark.parametrize("depth", DEPTHS)
def test_revoked_nearest_guardian_grant_denies_the_next_request_before_downstream_work(
    routes, world, events, mode, kind
):
    _apply_mode(routes, mode)
    spec = routes.spec
    user = User.objects.create_user(username="bd_revoked", password="pw")
    holder = user
    if kind == "group":
        holder = Group.objects.create(name="bd_editors")
        user.groups.add(holder)
    _grant_path(holder, routes, world.a, levels=_mode_levels(routes, mode))
    _local_grants(user, routes)
    client = _client(user)
    url = _leaf_url(routes, routes.mm_vs, "update", world.a, pk=world.shared.pk)

    assert client.post(url, {spec.mm_text: "first"}).status_code == 302
    _revoke(routes, world, holder, len(routes.chain) - 1, "change")
    events.clear()
    assert client.post(url, {spec.mm_text: "second"}).status_code == 403
    assert getattr(spec.mm_model.objects.get(pk=world.shared.pk), spec.mm_text) == "first"
    assert _queryset_calls(events, routes.mm_vs) == 0  # denied before the child lookup, form and write


@pytest.mark.parametrize("mode", list(MODES))
@pytest.mark.parametrize("depth", DEPTH3)
def test_revoked_higher_grant_denies_full_cascade_only(routes, world, mode):
    """Revoking the outermost ancestor's grant denies the next full-cascade request; nearest-only never
    evaluated it, so its next request still succeeds."""
    _apply_mode(routes, mode)
    spec = routes.spec
    user = User.objects.create_user(username="bd_higher", password="pw")
    _grant_path(user, routes, world.a, levels=_all_levels(routes))
    _local_grants(user, routes)
    client = _client(user)
    url = _leaf_url(routes, routes.mm_vs, "update", world.a, pk=world.shared.pk)
    assert client.post(url, {spec.mm_text: "first"}).status_code == 302
    _revoke(routes, world, user, 0, "view")
    expected = 403 if mode == "full" else 302
    assert client.post(url, {spec.mm_text: "second"}).status_code == expected


@pytest.fixture
def core_chain():
    """Core (model provider) Publisher → plain Book list, for model-grant revocation."""
    from crud_views.lib.views import ListView

    def build(sfx):
        pub_vs = ViewSet(model=Publisher, name=f"bdcpub{sfx}")
        book_vs = ViewSet(
            model=Book, name=f"bdcbook{sfx}", parent=ParentViewSet(name=pub_vs.name, attribute="publisher")
        )
        type("List", (ListView,), {"cv_viewset": book_vs, "cv_list_actions": [], "cv_context_actions": []})
        return SimpleNamespace(pub_vs=pub_vs, book_vs=book_vs), [pub_vs, book_vs]

    with isolated_routes(build) as ns:
        yield ns


@pytest.mark.django_db
def test_revoked_model_grant_denies_the_next_request_without_touching_caller_held_caches(core_chain, events):
    publisher = Publisher.objects.create(name="pub-core")
    Book.objects.create(title="child", publisher=publisher)
    user = User.objects.create_user(username="bd_model", password="pw")
    permission = Permission.objects.get(content_type__app_label="app", codename="view_publisher")
    user.user_permissions.add(permission)
    client = _client(user)
    url = _url(core_chain.book_vs, "list", **{f"{core_chain.pub_vs.name}_pk": publisher.pk})
    assert client.get(url).status_code == 200

    held = User.objects.get(pk=user.pk)  # a caller-held actor instance with a primed permission cache
    assert held.has_perm("app.view_publisher")
    user.user_permissions.remove(permission)
    events.clear()

    assert client.get(url).status_code == 403  # the next request loads a fresh actor and re-evaluates
    assert _queryset_calls(events, core_chain.book_vs) == 0
    # Django's per-instance permission cache is the caller's: the framework neither reads nor invalidates it
    assert held.has_perm("app.view_publisher")
    assert not User.objects.get(pk=user.pk).has_perm("app.view_publisher")


# ── request-local state ──────────────────────────────────────────────────────


@pytest.fixture
def guarded_views(monkeypatch):
    """The view instance of every request that passed through the ancestor guard."""
    seen = []
    original = ancestors._authorize_ancestors

    def spy(view):
        seen.append(view)
        return original(view)

    monkeypatch.setattr(ancestors, "_authorize_ancestors", spy)
    return seen


@pytest.mark.parametrize("mode", list(MODES))
@pytest.mark.parametrize("depth", DEPTHS)
def test_resolved_objects_and_checker_belong_to_one_request(routes, world, guarded_views, mode):
    _apply_mode(routes, mode)
    client = _client(_editor(routes, world, mode))
    url = _leaf_url(routes, routes.mm_vs, "detail", world.a, pk=world.shared.pk)
    assert client.get(url).status_code == 200
    assert client.get(url).status_code == 200
    first, second = guarded_views
    assert first is not second
    assert first._cv_ancestor_state is not second._cv_ancestor_state
    assert first._cv_ancestor_state.objects[0] is not second._cv_ancestor_state.objects[0]  # re-resolved
    assert first._cv_guardian_ancestor_checker[1] is not second._cv_guardian_ancestor_checker[1]
    # nothing about access is kept on the ViewSets or the view classes between requests
    for holder in [*routes.chain, routes.mm_vs, type(first)]:
        state = vars(holder)
        assert "_cv_ancestor_state" not in state and "_cv_guardian_ancestor_checker" not in state


@pytest.mark.parametrize("depth", DEPTH3)
def test_permission_vocabulary_cache_outlives_requests_but_access_does_not(routes, world, guarded_views):
    """The pre-existing permission-vocabulary cache (codename map per ViewSet) persists across requests: it
    names permissions, it does not record who holds them. Access is re-evaluated per request."""
    _apply_mode(routes, "full")
    user = User.objects.create_user(username="bd_vocab", password="pw")
    _grant_path(user, routes, world.a, levels=_all_levels(routes))
    _local_grants(user, routes)
    client = _client(user)
    url = _leaf_url(routes, routes.mm_vs, "detail", world.a, pk=world.shared.pk)
    assert client.get(url).status_code == 200
    vocabulary = [vs._default_permissions for vs in routes.chain]
    assert all(vocabulary)
    remove_perm(routes.chain[0].permissions["view"], user, world.a[0])
    assert client.get(url).status_code == 403
    assert [vs._default_permissions for vs in routes.chain] == vocabulary  # same vocabulary, new decision


@pytest.mark.parametrize("mode", list(MODES))
@pytest.mark.parametrize("depth", DEPTHS)
def test_in_flight_request_state_never_authorizes_another_request(routes, world, monkeypatch, mode):
    """ANCE-08 concurrency probe: while one authorized request is inside its ancestor gate, a second request
    runs to completion — for an actor without grants, and for the same actor on path B. Both are denied; the
    first request then completes normally."""
    from crud_views_guardian.lib.viewset import GuardianViewSet

    _apply_mode(routes, mode)
    granted = _client(_editor(routes, world, mode))
    stranger = _client(User.objects.create_user(username="bd_stranger", password="pw"))
    url_a = _leaf_url(routes, routes.mm_vs, "detail", world.a, pk=world.shared.pk)
    url_b = _leaf_url(routes, routes.mm_vs, "detail", world.b, pk=world.shared.pk)
    nested = []
    original_gate = GuardianViewSet._ancestor_has_permission

    def gate_with_interleaved_request(self, user, permission, obj, *, view):
        allowed = original_gate(self, user, permission, obj, view=view)
        if not nested:
            nested.append(None)  # once, while the outer request holds resolved ancestors and a primed checker
            nested[0] = (stranger.get(url_a).status_code, granted.get(url_b).status_code)
        return allowed

    monkeypatch.setattr(GuardianViewSet, "_ancestor_has_permission", gate_with_interleaved_request)
    assert granted.get(url_a).status_code == 200
    assert nested == [(403, 403)]


@pytest.mark.django_db
def test_interleaved_actors_on_one_viewset_are_decided_independently(core_chain):
    publisher = Publisher.objects.create(name="pub-interleave")
    reader = User.objects.create_user(username="bd_reader", password="pw")
    reader.user_permissions.add(Permission.objects.get(content_type__app_label="app", codename="view_publisher"))
    url = _url(core_chain.book_vs, "list", **{f"{core_chain.pub_vs.name}_pk": publisher.pk})
    reader_client = _client(reader)
    stranger_client = _client(User.objects.create_user(username="bd_nobody", password="pw"))
    assert [c.get(url).status_code for c in (reader_client, stranger_client, reader_client, Client())] == [
        200,
        403,
        200,
        302,  # anonymous: login redirect
    ]
