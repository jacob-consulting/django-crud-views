"""The default-database boundary of nested requests, against the independent ``default`` and ``shard`` databases.

Nested ancestry, nested child data and the authorization records their gates read support only ``default``. Every
reached nondefault selection (a ``.using()`` on any effective queryset, a read or write router, an actor loaded from
another database, routed auth or Guardian grant tables) is a configuration error, never an ordinary denial or a
silent read of a colliding copy. Most worlds below exist on both databases with identical primary keys, so a stray
shard query would succeed or deny instead of raising. Top-level requests keep their existing routed behavior.
"""

import pytest
from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured
from django.db import router
from django.test import Client, RequestFactory
from django.urls import resolve
from guardian.models import GroupObjectPermission, UserObjectPermission
from guardian.shortcuts import assign_perm

from crud_views.lib.viewset import AncestorPermissions, AncestorPolicy
from tests.test1.ancestor_cases import CHECKED, EVENTS, TracedViewSet, ancestor_scope, traced_chain
from tests.test1.app.models import Book, BookNote, Publisher
from tests.test1.test_ancestor_guardian import TracedGuardianViewSet
from tests.test1.test_ancestor_requests import TWO, FormTrace, client_for, define, make_user

pytestmark = pytest.mark.django_db(transaction=True, databases=["default", "shard"])
MATCH = "'shard'"


@pytest.fixture(autouse=True)
def events():
    EVENTS.clear()
    CHECKED.clear()
    yield EVENTS
    EVENTS.clear()
    CHECKED.clear()


@pytest.fixture
def scope():
    with ancestor_scope() as scope:
        yield scope


# ── worlds ────────────────────────────────────────────────────────────────────


def mirror(*objs):
    """Copy rows to ``shard`` with identical primary keys (colliding identities)."""
    for obj in objs:
        fields = {field.attname: getattr(obj, field.attname) for field in obj._meta.concrete_fields}
        type(obj).objects.using("shard").create(**fields)


def world():
    """Publisher → Book → BookNote on ``default``, mirrored on ``shard``; returns the default instances."""
    publisher = Publisher.objects.create(name="default publisher")
    book = Book.objects.create(title="default book", publisher=publisher)
    note = BookNote.objects.create(book=book, note="default note")
    mirror(publisher, book, note)
    Publisher.objects.using("shard").filter(pk=publisher.pk).update(name="shard publisher")
    Book.objects.using("shard").filter(pk=book.pk).update(title="shard book")
    BookNote.objects.using("shard").filter(pk=note.pk).update(note="shard note")
    return publisher, book, note


def shard_actor(pk, perms=()):
    """An active actor on ``shard`` whose primary key collides with a default actor."""
    actor = User.objects.db_manager("shard").create_user(pk=pk, username=f"shard actor {pk}")
    for codename in perms:
        actor.user_permissions.add(
            Permission.objects.using("shard").get(codename=codename, content_type__app_label="app")
        )
    return actor


class ShardViewSet(TracedViewSet):
    def get_queryset(self, view):
        return super().get_queryset(view).using("shard")


class DefaultViewSet(TracedViewSet):
    def get_queryset(self, view):
        return super().get_queryset(view).using("default")


class ShardQueryset:
    """An endpoint queryset override selecting ``shard`` after the guarded base queryset."""

    def get_queryset(self):
        return super().get_queryset().using("shard")


class DefaultQueryset:
    def get_queryset(self):
        return super().get_queryset().using("default")


class WriteRouter:
    """Reads stay on ``default``; writes of the listed models go to ``shard``."""

    def __init__(self, *models):
        self.models = models

    def db_for_read(self, model, **hints):
        return None

    def db_for_write(self, model, **hints):
        return "shard" if model in self.models else None


def detail_chain(scope, viewset_classes=None, policies=None, base=None):
    from crud_views.lib.views import DetailView

    routes = traced_chain(scope, TWO, viewset_classes=viewset_classes, policies=policies)
    define(scope, routes.endpoint, base or DetailView)
    scope.mount([routes.endpoint])
    return routes


def no_note_written(note_text):
    return not any(BookNote.objects.using(alias).filter(note=note_text).exists() for alias in ("default", "shard"))


# ── default selection ─────────────────────────────────────────────────────────

SEEN: list = []


class CaptureObject:
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        SEEN.append((self, self.get_queryset(), obj))
        return obj


@pytest.mark.parametrize("explicit", [False, True], ids=["implicit", "using_default"])
def test_default_database_selection_is_preserved(scope, events, explicit):
    from crud_views.lib.views import DetailView, ListView

    SEEN.clear()
    classes = {0: DefaultViewSet, 1: DefaultViewSet, 2: DefaultViewSet} if explicit else None
    routes = traced_chain(scope, TWO, viewset_classes=classes)
    queryset_mixin = (DefaultQueryset,) if explicit else ()
    define(scope, routes.endpoint, (CaptureObject, *queryset_mixin, DetailView))
    define(scope, routes.endpoint, (*queryset_mixin, ListView))
    scope.mount([routes.endpoint])
    publisher, book, note = world()
    client = client_for(make_user("reader", ["view_publisher", "view_book"]))

    response = client.get(routes.url("detail", [publisher, book], obj=note))
    assert response.status_code == 200
    assert response.content.decode().split("|")[1] == str(note.pk)
    ((view, queryset, obj),) = SEEN
    # the explicit selection is kept (never stripped), the implicit one is never forced
    assert queryset._db == ("default" if explicit else None)
    assert (obj, obj._state.db, view.kwargs["pk"]) == (note, "default", str(note.pk))
    ancestors = view._cv_ancestor_objects
    assert [(o.pk, o._state.db) for o in ancestors.values()] == [(publisher.pk, "default"), (book.pk, "default")]
    assert view.cv_get_parent_object() is ancestors[routes.viewsets[1].name]
    assert view.cv_get_parent_object().title == "default book"

    response = client.get(routes.url("list", [publisher, book]))
    assert (response.status_code, response.content.decode().split("|")[0]) == (200, f"{note.pk};")


# ── reached nondefault ORM and authorization paths ───────────────────────────


def _request_detail(scope, client, **chain):
    routes = detail_chain(scope, **chain)
    publisher, book, note = world()
    client.get(routes.url("detail", [publisher, book], obj=note))


def _warm(client, url):
    """A successful request first: the permission vocabulary and content types are cached afterwards."""
    assert client.get(url).status_code == 200


def case_ancestor_using(scope, monkeypatch, database_routes):
    _request_detail(
        scope, client_for(make_user("r", ["view_publisher", "view_book"])), viewset_classes={0: ShardViewSet}
    )


def case_child_viewset_using(scope, monkeypatch, database_routes):
    _request_detail(
        scope, client_for(make_user("r", ["view_publisher", "view_book"])), viewset_classes={2: ShardViewSet}
    )


def case_ancestor_read_router(scope, monkeypatch, database_routes):
    routes = detail_chain(scope)
    publisher, book, note = world()
    client = client_for(make_user("r", ["view_publisher", "view_book"]))
    with database_routes("default", {Book: "shard"}):
        client.get(routes.url("detail", [publisher, book], obj=note))


def case_child_read_router(scope, monkeypatch, database_routes):
    routes = detail_chain(scope)
    publisher, book, note = world()
    client = client_for(make_user("r", ["view_publisher", "view_book"]))
    with database_routes("default", {BookNote: "shard"}):
        client.get(routes.url("detail", [publisher, book], obj=note))


def case_write_router(scope, monkeypatch, database_routes, atomic=True):
    from crud_views.lib.views import CreateView, CreateViewParentMixin

    routes = traced_chain(scope, TWO)
    define(scope, routes.endpoint, (FormTrace, CreateViewParentMixin, CreateView), fields=["note"], cv_atomic=atomic)
    scope.mount([routes.endpoint])
    publisher, book, _note = world()
    client = client_for(make_user("w", ["view_publisher", "change_book"]))
    monkeypatch.setattr(router, "routers", [WriteRouter(BookNote)])
    try:
        client.post(routes.url("create", [publisher, book]), {"note": "routed write"})
    finally:
        assert no_note_written("routed write")
        assert "on_commit" not in EVENTS


def case_write_router_without_atomic(scope, monkeypatch, database_routes):
    case_write_router(scope, monkeypatch, database_routes, atomic=False)


def _actor_request(scope, *, guardian):
    """The request actor was loaded from ``shard``; a colliding default actor holds every grant."""
    classes = {0: TracedGuardianViewSet} if guardian else None
    routes = detail_chain(scope, viewset_classes=classes)
    publisher, book, note = world()
    default_actor = make_user("default actor", ["view_publisher", "view_book"])
    assign_perm("app.view_publisher", default_actor, publisher)
    request = RequestFactory().get(routes.url("detail", [publisher, book], obj=note))
    request.user = shard_actor(default_actor.pk, ["view_publisher", "view_book"])
    match = resolve(request.path)
    match.func(request, **match.kwargs)


def case_actor_from_shard(scope, monkeypatch, database_routes):
    _actor_request(scope, guardian=False)


def case_guardian_actor_from_shard(scope, monkeypatch, database_routes):
    _actor_request(scope, guardian=True)


def _routed_auth(scope, database_routes, overrides, *, guardian=False):
    """Every grant exists on ``default`` (the warm-up passes); then the auth/grant tables of ``overrides`` route to
    ``shard``, which also holds an identical actor and the same tables."""
    classes = {0: TracedGuardianViewSet} if guardian else None
    routes = detail_chain(scope, viewset_classes=classes)
    publisher, book, note = world()
    group = Group.objects.create(name="readers")
    actor = make_user("routed", [] if guardian else ["view_book"])
    actor.groups.add(group)
    group.permissions.add(Permission.objects.get(codename="view_publisher"))
    if guardian:
        actor.user_permissions.add(Permission.objects.get(codename="view_book"))
        assign_perm("app.view_publisher", group, publisher)
    mirror(User.objects.get(pk=actor.pk))  # an identical shard actor: a routed session keeps authenticating
    client = client_for(actor)
    url = routes.url("detail", [publisher, book], obj=note)
    _warm(client, url)
    with database_routes("default", overrides):
        client.get(url)


def case_permission_route(scope, monkeypatch, database_routes):
    _routed_auth(scope, database_routes, {Permission: "shard"})


def case_content_type_route(scope, monkeypatch, database_routes):
    _routed_auth(scope, database_routes, {ContentType: "shard"})


def case_group_route(scope, monkeypatch, database_routes):
    _routed_auth(scope, database_routes, {Group: "shard"})


def case_user_route(scope, monkeypatch, database_routes):
    _routed_auth(scope, database_routes, {User: "shard"})


def case_guardian_user_grant_route(scope, monkeypatch, database_routes):
    _routed_auth(scope, database_routes, {UserObjectPermission: "shard"}, guardian=True)


def case_guardian_group_grant_route(scope, monkeypatch, database_routes):
    _routed_auth(scope, database_routes, {GroupObjectPermission: "shard"}, guardian=True)


def case_local_gate_permission_route(scope, monkeypatch, database_routes):
    """All-``none`` ancestry: the endpoint's local model-permission gate is the only auth read."""
    from crud_views.lib.views import DetailViewPermissionRequired

    none = AncestorPolicy(provider="none")
    routes = detail_chain(scope, policies={0: none, 1: none}, base=DetailViewPermissionRequired)
    publisher, book, note = world()
    actor = make_user("local", ["view_booknote"])
    mirror(User.objects.get(pk=actor.pk))
    client = client_for(actor)
    url = routes.url("detail", [publisher, book], obj=note)
    _warm(client, url)
    with database_routes("default", {Permission: "shard"}):
        client.get(url)


REACHED = [
    case_ancestor_using,
    case_child_viewset_using,
    case_ancestor_read_router,
    case_child_read_router,
    case_write_router,
    case_write_router_without_atomic,
    case_actor_from_shard,
    case_guardian_actor_from_shard,
    case_permission_route,
    case_content_type_route,
    case_group_route,
    case_user_route,
    case_guardian_user_grant_route,
    case_guardian_group_grant_route,
    case_local_gate_permission_route,
]


@pytest.mark.parametrize("case", REACHED, ids=[case.__name__.removeprefix("case_") for case in REACHED])
def test_reached_nondefault_orm_and_auth_paths_fail(scope, events, monkeypatch, database_routes, case):
    with pytest.raises(ImproperlyConfigured, match=MATCH):
        case(scope, monkeypatch, database_routes)


# ── reached order of database and permission-key errors ──────────────────────


def mixed_chain(scope, policies=None):
    """Publisher (model provider) → Book (Guardian provider) → BookNote."""
    return detail_chain(scope, viewset_classes={1: TracedGuardianViewSet}, policies=policies)


def test_database_and_permission_key_errors_obey_order(scope, events, database_routes):
    routes = mixed_chain(scope)
    publisher, book, note = world()
    url = routes.url("detail", [publisher, book], obj=note)
    grant_routes = {UserObjectPermission: "shard", GroupObjectPermission: "shard"}

    # an outer denial is reached first: the deeper routed Guardian grant tables are never validated or queried
    with database_routes("default", grant_routes):
        assert client_for(make_user("outsider")).get(url).status_code == 403
    assert events == ["outer_queryset", "outer_gate"]

    # outer passes: the deeper selected gate reaches its routed grant tables → configuration error
    events.clear()
    reader = client_for(make_user("reader", ["view_publisher"]))
    with database_routes("default", grant_routes), pytest.raises(ImproperlyConfigured, match=MATCH):
        reader.get(url)
    assert events == ["outer_queryset", "outer_gate", "inner_queryset"]


def test_deeper_missing_key_and_shard_ancestor_follow_an_outer_denial(scope, events):
    from crud_views.lib.views import DetailView

    actions = {"approve": AncestorPermissions(nearest="approve", higher="view")}
    routes = traced_chain(scope, TWO, viewset_classes={1: ShardViewSet}, policies={2: AncestorPolicy(actions=actions)})
    define(scope, routes.endpoint, DetailView)
    define(scope, routes.endpoint, DetailView, key="approve")
    scope.mount([routes.endpoint])
    publisher, book, note = world()
    for key in ("detail", "approve"):
        events.clear()
        assert (
            client_for(make_user(f"outsider {key}")).get(routes.url(key, [publisher, book], obj=note)).status_code
            == 403
        )
        assert events == ["outer_queryset", "outer_gate"]


def test_nearest_only_never_resolves_or_routes_an_unselected_higher_gate(scope, events, database_routes):
    actions = {"detail": AncestorPermissions(nearest="view", higher="no_such_key")}
    policies = {2: AncestorPolicy(cascade=False, actions=actions)}
    routes = detail_chain(scope, viewset_classes={0: TracedGuardianViewSet}, policies=policies)
    publisher, book, note = world()
    client = client_for(make_user("nearest", ["view_book"]))

    with database_routes("default", {UserObjectPermission: "shard", GroupObjectPermission: "shard"}):
        assert client.get(routes.url("detail", [publisher, book], obj=note)).status_code == 200
    assert CHECKED == [("inner", "app.view_book")]


# ── endpoint overrides cannot bypass the child guard ─────────────────────────


def _override_detail(scope, monkeypatch, database_routes):
    from crud_views.lib.views import DetailView

    _request_detail(
        scope, client_for(make_user("r", ["view_publisher", "view_book"])), base=(ShardQueryset, DetailView)
    )


def _override_list(scope, monkeypatch, database_routes):
    from crud_views.lib.views import ListView

    routes = traced_chain(scope, TWO)
    define(scope, routes.endpoint, (ShardQueryset, ListView))
    scope.mount([routes.endpoint])
    publisher, book, _note = world()
    client_for(make_user("r", ["view_publisher", "view_book"])).get(routes.url("list", [publisher, book]))


def _override_table_list(scope, monkeypatch, database_routes):
    from crud_views.lib.table import Table
    from crud_views.lib.views import ListView, ListViewTableMixin

    class NoteTable(Table):
        class Meta:
            model = BookNote
            fields = ["note"]

    routes = traced_chain(scope, TWO)
    define(scope, routes.endpoint, (ListViewTableMixin, ShardQueryset, ListView), table_class=NoteTable)
    scope.mount([routes.endpoint])
    publisher, book, _note = world()
    client_for(make_user("r", ["view_publisher", "view_book"])).get(routes.url("list", [publisher, book]))


class SuppliedShardObject:
    """Supplies its own queryset argument to ``get_object()``."""

    def get_object(self, queryset=None):
        return super().get_object(BookNote.objects.using("shard"))


def _supplied_get_object(scope, monkeypatch, database_routes):
    from crud_views.lib.views import DetailView

    _request_detail(
        scope, client_for(make_user("r", ["view_publisher", "view_book"])), base=(SuppliedShardObject, DetailView)
    )


def _guardian_child(scope, view_base, key, overrides, database_routes, *, attrs=None, obj=True):
    """Guardian endpoint under ``none`` ancestors: its own object/queryset gate is the only auth read."""
    from crud_views.lib.viewset import ParentViewSet
    from crud_views_guardian.lib.viewset import GuardianViewSet

    none = AncestorPolicy(provider="none")
    pub_vs = scope.viewset(GuardianViewSet, model=Publisher, name=scope.name("gpub"), ancestor_policy=none)
    book_vs = scope.viewset(
        GuardianViewSet,
        model=Book,
        name=scope.name("gbook"),
        parent=ParentViewSet(name=pub_vs.name, attribute="publisher"),
        ancestor_policy=none,
    )
    note_vs = scope.viewset(
        GuardianViewSet,
        model=BookNote,
        name=scope.name("gnote"),
        parent=ParentViewSet(name=book_vs.name, attribute="book"),
    )
    define(scope, note_vs, view_base, **(attrs or {}))
    scope.mount([note_vs])
    publisher, book, note = world()
    actor = make_user("guardian reader")
    note_vs.assign_perm("view", actor, note)
    shard_actor(actor.pk)
    from django.urls import reverse

    kwargs = {note_vs.parent.get_pk_name(): book.pk, book_vs.parent.get_pk_name(): publisher.pk}
    if obj:
        kwargs["pk"] = note.pk
    url = reverse(note_vs.get_router_name(key), kwargs=kwargs)
    client = client_for(actor)
    if overrides:
        _warm(client, url)
        with database_routes("default", overrides):
            client.get(url)
    else:
        client.get(url)


def _guardian_filtered_list(scope, monkeypatch, database_routes):
    from crud_views_guardian.lib.views import GuardianListViewPermissionRequired

    routes = {UserObjectPermission: "shard", GroupObjectPermission: "shard"}
    _guardian_child(scope, GuardianListViewPermissionRequired, "list", routes, database_routes, obj=False)


def _guardian_list_override(scope, monkeypatch, database_routes):
    from crud_views_guardian.lib.views import GuardianListViewPermissionRequired

    _guardian_child(
        scope, (ShardQueryset, GuardianListViewPermissionRequired), "list", None, database_routes, obj=False
    )


def _guardian_object_gate(scope, monkeypatch, database_routes):
    from crud_views_guardian.lib.views import GuardianDetailViewPermissionRequired

    routes = {UserObjectPermission: "shard", GroupObjectPermission: "shard"}
    _guardian_child(scope, GuardianDetailViewPermissionRequired, "detail", routes, database_routes)


def _form_write(scope, monkeypatch, view_bases, key, *, obj, payload, router_models=(), policies=None, **attrs):
    from crud_views.lib.views import ListView

    routes = traced_chain(scope, TWO, policies=policies)
    define(scope, routes.endpoint, ListView)
    define(scope, routes.endpoint, view_bases, **attrs)
    scope.mount([routes.endpoint])
    publisher, book, note = world()
    client = client_for(make_user("w", ["view_publisher", "change_book"]))
    if router_models:
        monkeypatch.setattr(router, "routers", [WriteRouter(*router_models)])
    url = routes.url(key, [publisher, book], obj=note if obj else None)
    try:
        client.post(url, payload)
    finally:
        assert "on_commit" not in EVENTS
        assert [n.note for n in BookNote.objects.all()] == ["default note"]
        assert [n.note for n in BookNote.objects.using("shard").all()] == ["shard note"]


class ShardWriteAlias:
    def cv_get_db_alias(self):
        return "shard"


def _write_alias_override(scope, monkeypatch, database_routes):
    from crud_views.lib.views import CreateView, CreateViewParentMixin

    bases = (ShardWriteAlias, FormTrace, CreateViewParentMixin, CreateView)
    _form_write(scope, monkeypatch, bases, "create", obj=False, payload={"note": "x"}, fields=["note"])


def _write_alias_override_without_atomic(scope, monkeypatch, database_routes):
    from crud_views.lib.views import UpdateView

    bases = (ShardWriteAlias, FormTrace, UpdateView)
    payload = {"note": "x"}
    _form_write(scope, monkeypatch, bases, "update", obj=True, payload=payload, fields=["note"], cv_atomic=False)


class DefaultWriteAlias:
    def cv_get_db_alias(self):
        return "default"


def _default_alias_override_with_shard_write_router(scope, monkeypatch, database_routes):
    from crud_views.lib.views import UpdateView

    bases = (DefaultWriteAlias, FormTrace, UpdateView)
    _form_write(
        scope, monkeypatch, bases, "update", obj=True, payload={"note": "x"}, router_models=(BookNote,), fields=["note"]
    )


def _update_write_router_without_atomic(scope, monkeypatch, database_routes):
    from crud_views.lib.views import UpdateView

    bases = (FormTrace, UpdateView)
    payload = {"note": "x"}
    _form_write(
        scope,
        monkeypatch,
        bases,
        "update",
        obj=True,
        payload=payload,
        router_models=(BookNote,),
        fields=["note"],
        cv_atomic=False,
    )


def _delete_write_router(scope, monkeypatch, database_routes):
    from crud_views.lib.views import DeleteView

    _form_write(scope, monkeypatch, (FormTrace, DeleteView), "delete", obj=True, payload={}, router_models=(BookNote,))


def _delete_write_router_without_atomic(scope, monkeypatch, database_routes):
    from crud_views.lib.views import DeleteView

    _form_write(
        scope,
        monkeypatch,
        (FormTrace, DeleteView),
        "delete",
        obj=True,
        payload={},
        router_models=(BookNote,),
        cv_atomic=False,
    )


def _action_write_router_without_atomic(scope, monkeypatch, database_routes):
    from crud_views.lib.views import ActionView

    class TouchAction(ActionView):
        cv_key = "touch"
        cv_path = "touch"

        def action(self, context):
            self.object.note = "x"
            self.object.save()
            return True

    _form_write(
        scope,
        monkeypatch,
        (FormTrace, TouchAction),
        "touch",
        obj=True,
        payload={},
        router_models=(BookNote,),
        policies={2: AncestorPolicy(actions={"touch": AncestorPermissions(nearest="change", higher="view")})},
        cv_atomic=False,
    )


OVERRIDES = [
    _override_detail,
    _override_list,
    _override_table_list,
    _supplied_get_object,
    _guardian_filtered_list,
    _guardian_list_override,
    _guardian_object_gate,
    _write_alias_override,
    _write_alias_override_without_atomic,
    _default_alias_override_with_shard_write_router,
    _update_write_router_without_atomic,
    _delete_write_router,
    _delete_write_router_without_atomic,
    _action_write_router_without_atomic,
]


@pytest.mark.parametrize("case", OVERRIDES, ids=[case.__name__.lstrip("_") for case in OVERRIDES])
def test_queryset_override_cannot_bypass_child_database_guard(scope, events, monkeypatch, database_routes, case):
    with pytest.raises(ImproperlyConfigured, match=MATCH):
        case(scope, monkeypatch, database_routes)


# ── top level unchanged ───────────────────────────────────────────────────────


@pytest.mark.parametrize("using", ["default", "shard"])
@pytest.mark.parametrize("atomic", [True, False])
def test_top_level_routed_behavior_is_unchanged(scope, events, database_routes, using, atomic):
    from crud_views.lib.views import (
        DeleteViewPermissionRequired,
        DetailViewPermissionRequired,
        ListViewPermissionRequired,
        UpdateViewPermissionRequired,
    )

    other = "default" if using == "shard" else "shard"
    publisher_vs = scope.viewset(TracedViewSet, model=Publisher, name=scope.name("toppub"), trace="child")
    define(scope, publisher_vs, ListViewPermissionRequired)
    define(scope, publisher_vs, DetailViewPermissionRequired)
    define(scope, publisher_vs, UpdateViewPermissionRequired, fields=["name"], cv_atomic=atomic)
    define(scope, publisher_vs, DeleteViewPermissionRequired, cv_atomic=atomic)
    scope.mount([publisher_vs])
    for alias in ("default", "shard"):
        Publisher.objects.using(alias).create(pk=41, name=f"{alias} publisher")
        Publisher.objects.using(alias).create(pk=42, name=f"{alias} second")
    with database_routes(using):
        actor = User.objects.db_manager(using).create_user(pk=51, username=f"{using} actor")
        for action in ("view", "change", "delete"):
            actor.user_permissions.add(
                Permission.objects.using(using).get(codename=f"{action}_publisher", content_type__app_label="app")
            )
        client = Client()
        client.force_login(actor)
        from django.urls import reverse

        def url(key, pk=None):
            return reverse(publisher_vs.get_router_name(key), kwargs={"pk": pk} if pk else {})

        response = client.get(url("list"))
        assert (response.status_code, response.content.decode().split("|")[0]) == (200, "41;42;")
        assert client.get(url("detail", 41)).status_code == 200
        assert client.post(url("update", 41), {"name": "renamed"}).status_code == 302
        assert client.post(url("delete", 42)).status_code == 302
    assert list(Publisher.objects.using(using).values_list("pk", "name")) == [(41, "renamed")]
    assert sorted(Publisher.objects.using(other).values_list("pk", "name")) == [
        (41, f"{other} publisher"),
        (42, f"{other} second"),
    ]


def test_top_level_actor_and_auth_routes_are_not_validated(scope, events, database_routes):
    """The nested auth-route validation never applies at the top level: the routed tables keep answering."""
    from crud_views.lib.views import DetailViewPermissionRequired

    publisher_vs = scope.viewset(TracedViewSet, model=Publisher, name=scope.name("authpub"), trace="child")
    define(scope, publisher_vs, DetailViewPermissionRequired)
    scope.mount([publisher_vs])
    publisher = Publisher.objects.create(name="default publisher")
    actor = make_user("top", ["view_publisher"])
    from django.urls import reverse

    url = reverse(publisher_vs.get_router_name("detail"), kwargs={"pk": publisher.pk})
    client = client_for(actor)
    _warm(client, url)
    shard_actor(actor.pk)
    with database_routes("default", {Permission: "shard"}):
        # the routed Permission table (empty grants on shard) denies as before; no configuration error
        assert client.get(url).status_code == 403
