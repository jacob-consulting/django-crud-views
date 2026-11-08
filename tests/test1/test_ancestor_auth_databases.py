"""
Phase 06.18 plan 07 — the reached default-database boundary of nested authorization records (ANCE-04, ANCE-06).

Wave one supports only ``default`` for the authorization records a nested request's permission checks read: the
permission vocabulary (ContentType, Permission), the actor and its group/permission through tables, and Guardian's
generic and direct object grants. Each check is validated where it is *reached*, before its vocabulary (cold or
already cached) and before any backend shortcut (active superuser, model fallback):

* an ancestor gate of the shared engine, only for selected levels (a higher level that nearest-only mode does not
  select is not touched);
* the endpoint's own local gates after ancestry: Guardian object gates and list filters, core permission-required
  checks (including the all-none early actor admission) and nested manage pages (group gate, permission holders).

Plain endpoints with no permission check do no auth work, and top-level ViewSets keep their routed behaviour.
Rows and actors collide on purpose: ``default`` and ``shard`` hold the same primary keys (and the same actor
password hash, so a session can load either copy), so a wrong-copy grant is visible instead of silently "working".
Nothing reroutes or retries on ``default``.

The router is module-local (the same shape as ``tests.test1.test_ancestor_databases``): ``routes.read[Model]``
maps a model to an alias; unmapped models get no answer, which is Django's default routing. Fixtures build fresh,
uniquely named ViewSets behind a temporary ROOT_URLCONF and restore registry, URL and ContentType caches afterwards
(``isolated_routes``; the project URLconf is imported first).
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured
from django.db import router
from django.test import RequestFactory, override_settings
from django.urls import resolve
from guardian.models import GroupObjectPermission, UserObjectPermission
from guardian.shortcuts import assign_perm

from crud_views.lib import ancestor_db
from crud_views.lib.view import CrudView
from crud_views.lib.viewset import AncestorPolicy, ParentViewSet, ViewSet
from tests.test1.app.models import (
    Book,
    BookNote,
    Publisher,
    Shelf,
    ShelfGroupObjectPermission,
    ShelfItem,
    ShelfUserObjectPermission,
)
from tests.test1.test_ancestor_actors import ANONYMOUS_READER
from tests.test1.test_ancestor_authorization import _client, _url, isolated_routes
from tests.test1.test_ancestor_databases import _sql, captured
from tests.test1.test_ancestor_resolution import _register_project_viewsets

pytestmark = pytest.mark.django_db(transaction=True, databases=["default", "shard"])
REFUSED = r"nested ViewSets support only the 'default' database"
# loads inactive actors from the session (Django's ModelBackend would make them anonymous) and denies them
ALLOW_INACTIVE = "django.contrib.auth.backends.AllowAllUsersModelBackend"

# the auth records a permission check reads, by name
TABLES = {
    "user": User,
    "group": Group,
    "permission": Permission,
    "contenttype": ContentType,
    "user_groups": User.groups.through,
    "user_permissions": User.user_permissions.through,
    "group_permissions": Group.permissions.through,
    "user_grant": UserObjectPermission,
    "group_grant": GroupObjectPermission,
    "direct_user_grant": ShelfUserObjectPermission,
    "direct_group_grant": ShelfGroupObjectPermission,
}
CORE = ["user", "group", "permission", "contenttype", "user_groups", "user_permissions", "group_permissions"]
GENERIC = ["user_grant", "group_grant"]
DIRECT = ["direct_user_grant", "direct_group_grant"]
AUTH_SQL_TABLES = (
    "auth_permission",
    "auth_group",
    "auth_user_groups",
    "auth_user_user_permissions",
    "auth_group_permissions",
    "django_content_type",
    "guardian_userobjectpermission",
    "guardian_groupobjectpermission",
    "app_shelfuserobjectpermission",
    "app_shelfgroupobjectpermission",
)
# ancestor kinds: core model permissions, strict Guardian, Guardian with ancestor fallback, Guardian direct grants
KINDS = ("model", "guardian", "fallback", "direct")


def _kind_tables(kind):
    return CORE + (GENERIC if kind != "model" else []) + (DIRECT if kind == "direct" else [])


def _auth_sql(capture) -> list[str]:
    return [sql for sql in _sql(capture) if any(f'"{table}"' in sql for table in AUTH_SQL_TABLES)]


def _foreign_sql(capture) -> list[str]:
    """Shard SQL other than loading the session's (colliding) actor copy."""
    return [sql for sql in _sql(capture) if '"auth_user"' not in sql or '"auth_user_' in sql]


def _assert_refused_without_auth_reads(sql):
    assert _auth_sql(sql.default) == []
    assert _auth_sql(sql.shard) == []
    assert _foreign_sql(sql.shard) == []


# ── routing, rows and actors ─────────────────────────────────────────────────


@pytest.fixture
def routes(monkeypatch):
    """Module-local router; every consulted (operation, model) is recorded in ``calls``."""
    table = SimpleNamespace(read={}, write={}, calls=[])

    class Router:
        def db_for_read(self, model, **hints):
            table.calls.append(("read", model))
            return table.read.get(model)

        def db_for_write(self, model, **hints):
            table.calls.append(("write", model))
            return table.write.get(model)

    monkeypatch.setattr(router, "routers", [Router()])
    ContentType.objects.clear_cache()
    yield table
    ContentType.objects.clear_cache()


@pytest.fixture
def world():
    rows = {}
    for alias in ("default", "shard"):
        publisher = Publisher.objects.using(alias).create(pk=41, name=f"{alias} publisher")
        book = Book.objects.using(alias).create(pk=71, publisher_id=41, title=f"{alias} book")
        BookNote.objects.using(alias).create(pk=91, book_id=71, note=f"{alias} note")
        shelf = Shelf.objects.using(alias).create(pk=51, name=f"{alias} shelf")
        ShelfItem.objects.using(alias).create(pk=61, shelf_id=51, name=f"{alias} item")
        rows[alias] = SimpleNamespace(publisher=publisher, book=book, shelf=shelf)
    return rows["default"]


def _actor(username, *, superuser=False, active=True):
    """An actor on default with a colliding copy (same pk and password hash) on shard."""
    create = User.objects.create_superuser if superuser else User.objects.create_user
    user = create(username=username, password="pw")
    if not active:
        user.is_active = False
        user.save()
    User.objects.using("shard").create(
        pk=user.pk,
        username=username,
        password=user.password,
        is_superuser=user.is_superuser,
        is_staff=user.is_staff,
        is_active=active,
    )
    return user


def _model_perm(user, model, action, using="default"):
    ct = ContentType.objects.db_manager(using).get_for_model(model)
    permission = Permission.objects.using(using).get(content_type=ct, codename=f"{action}_{ct.model}")
    User.objects.using(using).get(pk=user.pk).user_permissions.add(permission)


def _grant(user, kind, world, action="view"):
    """The grant that satisfies the ancestor gate of ``kind`` on default."""
    if kind in ("model", "fallback"):
        _model_perm(user, Publisher, action)
    elif kind == "guardian":
        assign_perm(f"app.{action}_publisher", user, world.publisher)
    else:
        assign_perm(f"app.{action}_shelf", user, world.shelf)


def _shard_object_grant(user, model, pk, action="view"):
    """A colliding generic Guardian grant on shard (same actor pk, same object pk)."""
    ct = ContentType.objects.db_manager("shard").get_for_model(model)
    permission = Permission.objects.using("shard").get(content_type=ct, codename=f"{action}_{ct.model}")
    UserObjectPermission.objects.using("shard").create(
        user_id=user.pk, permission=permission, content_type=ct, object_pk=str(pk)
    )


def _call(url, user):
    """Dispatch ``url`` directly with ``user`` as the request actor (e.g. an actor loaded from shard)."""
    request = RequestFactory().get(url)
    request.user = user
    match = resolve(url)
    return match.func(request, *match.args, **match.kwargs)


# ── dynamic ViewSets ─────────────────────────────────────────────────────────


@pytest.fixture
def adb():
    from crud_views.lib.views import (
        DetailView,
        DetailViewPermissionRequired,
        ListView,
        ListViewPermissionRequired,
    )
    from crud_views_guardian.lib.views import (
        GuardianDetailViewPermissionRequired,
        GuardianListViewPermissionRequired,
    )
    from crud_views_guardian.lib.viewset import GuardianViewSet

    def view(base, vs, **attrs):
        return type(base.__name__, (base,), {"cv_viewset": vs, "cv_context_actions": [], **attrs})

    def lst(vs, base=ListView, **attrs):
        return view(base, vs, cv_list_actions=[], **attrs)

    def child(name, parent, model=Book, attribute="publisher", **kwargs):
        return (GuardianViewSet if kwargs.pop("guardian", False) else ViewSet)(
            model=model, name=name, parent=ParentViewSet(name=parent.name, attribute=attribute), **kwargs
        )

    def build(sfx):
        ns = SimpleNamespace(anc={}, child={}, notes={})

        # ── Task 1: one ancestor per provider kind, each with a plain child (no local permission check) ──
        ns.anc["model"] = ViewSet(model=Publisher, name=f"aamodel{sfx}")
        ns.anc["guardian"] = GuardianViewSet(model=Publisher, name=f"aaguard{sfx}")
        ns.anc["fallback"] = GuardianViewSet(
            model=Publisher, name=f"aafall{sfx}", ancestor_policy=AncestorPolicy(accept_global_perms=True)
        )
        ns.anc["direct"] = GuardianViewSet(model=Shelf, name=f"aadirect{sfx}")
        for kind, ancestor in ns.anc.items():
            model, attribute = (ShelfItem, "shelf") if kind == "direct" else (Book, "publisher")
            vs = child(f"aac{kind}{sfx}", ancestor, model=model, attribute=attribute)
            ns.child[kind] = SimpleNamespace(vs=vs, Detail=view(DetailView, vs), List=lst(vs))

        # Publisher (Guardian, generic grants) -> Book (core, model permissions) -> BookNote: nearest-only gates
        # only Book, full cascade gates both
        ns.gchain = GuardianViewSet(model=Publisher, name=f"aagchain{sfx}")
        ns.cbook = child(f"aacbook{sfx}", ns.gchain)
        lst(ns.cbook)
        for cascade in (False, True):
            vs = child(
                f"aanote{int(cascade)}{sfx}",
                ns.cbook,
                model=BookNote,
                attribute="book",
                ancestor_policy=AncestorPolicy(cascade=cascade),
            )
            ns.notes[cascade] = SimpleNamespace(vs=vs, Detail=view(DetailView, vs), List=lst(vs))
        # Publisher (core) -> Book (Guardian) -> BookNote, full cascade: an outer denial hides the deeper gate
        ns.cchain = ViewSet(model=Publisher, name=f"aacchain{sfx}")
        ns.gbook = child(f"aagbook{sfx}", ns.cchain, guardian=True)
        lst(ns.gbook)
        ns.inner = child(
            f"aainner{sfx}", ns.gbook, model=BookNote, attribute="book", ancestor_policy=AncestorPolicy(cascade=True)
        )
        ns.InnerDetail = view(DetailView, ns.inner)

        # ── Tasks 2 and 3: local gates beneath an all-none parent (no ancestor gate is evaluated) ──
        ns.none = ViewSet(model=Publisher, name=f"aanone{sfx}", ancestor_policy=AncestorPolicy(provider="none"))
        lst(ns.none)
        ns.gloc = child(f"aagloc{sfx}", ns.none, guardian=True)
        ns.GList = lst(ns.gloc, GuardianListViewPermissionRequired)
        ns.GGlobalList = lst(
            ns.gloc,
            GuardianListViewPermissionRequired,
            cv_key="global_list",
            cv_path="global",
            cv_guardian_accept_global_perms=True,
        )
        ns.GDetail = view(GuardianDetailViewPermissionRequired, ns.gloc)
        ns.GGlobalDetail = view(
            GuardianDetailViewPermissionRequired,
            ns.gloc,
            cv_key="global_detail",
            cv_path="global-detail",
            cv_guardian_accept_global_perms=True,
        )
        ns.cloc = child(f"aacloc{sfx}", ns.none)
        ns.CList, ns.CDetail = lst(ns.cloc, ListViewPermissionRequired), view(DetailViewPermissionRequired, ns.cloc)
        ns.ploc = child(f"aaploc{sfx}", ns.none)
        ns.PList, ns.PDetail = lst(ns.ploc), view(DetailView, ns.ploc)
        # protected core parent -> core permission-required child: ancestor gate, then the local gate
        ns.ppub = ViewSet(model=Publisher, name=f"aappub{sfx}")
        lst(ns.ppub)
        ns.pcbook = child(f"aapcbook{sfx}", ns.ppub)
        ns.PCList, ns.PCDetail = lst(ns.pcbook), view(DetailViewPermissionRequired, ns.pcbook)

        # ── top-level controls ──
        ns.gtop = GuardianViewSet(model=Book, name=f"aagtop{sfx}")
        ns.GTList, ns.GTDetail = (
            lst(ns.gtop, GuardianListViewPermissionRequired),
            view(GuardianDetailViewPermissionRequired, ns.gtop),
        )
        ns.ctop = ViewSet(model=Book, name=f"aactop{sfx}")
        ns.CTList, ns.CTDetail = lst(ns.ctop, ListViewPermissionRequired), view(DetailViewPermissionRequired, ns.ctop)

        routed = [
            *ns.anc.values(),
            *(c.vs for c in ns.child.values()),
            ns.gchain,
            ns.cbook,
            *(n.vs for n in ns.notes.values()),
            ns.cchain,
            ns.gbook,
            ns.inner,
            ns.none,
            ns.gloc,
            ns.cloc,
            ns.ploc,
            ns.ppub,
            ns.pcbook,
            ns.gtop,
            ns.ctop,
        ]
        return ns, routed

    _register_project_viewsets()
    with isolated_routes(build) as ns:
        yield ns


def _child_url(adb, kind, key, world):
    ancestor, entry = adb.anc[kind], adb.child[kind]
    parent = world.shelf if kind == "direct" else world.publisher
    kwargs = {f"{ancestor.name}_pk": parent.pk}
    if key == "detail":
        kwargs["pk"] = 61 if kind == "direct" else 71
    return _url(entry.vs, key, **kwargs)


def _note_url(vs, chain_root, chain_book):
    return _url(vs, "detail", **{f"{chain_root.name}_pk": 41, f"{chain_book.name}_pk": 71, "pk": 91})


def _local_url(adb, vs, key, pk=True):
    kwargs = {f"{adb.none.name}_pk": 41}
    if pk:
        kwargs["pk"] = 71
    return _url(vs, key, **kwargs)


@pytest.fixture
def events(monkeypatch):
    """Ordered framework events: auth-route checks (``("auth", model, provider)``, recorded where the boundary
    enumerates the checked tables), permission-map reads (by ViewSet),
    ancestor provider calls, child object lookups, action-state checks and manage holder queries."""
    from crud_views.lib.views.manage import ManageView

    recorded: list[tuple] = []
    original_tables = getattr(ancestor_db, "_auth_tables", None)
    original_permissions = ViewSet.permissions
    original_provider = ViewSet._ancestor_has_permission
    original_get_object = CrudView.get_object
    original_enabled = CrudView.cv_action_enabled.__func__
    original_holders = ManageView.get_permission_holders

    def tables(model, provider):
        recorded.append(("auth", model.__name__, provider))
        return original_tables(model, provider)

    def permissions(self):
        recorded.append(("vocabulary", self.name))
        return original_permissions.fget(self)

    def provider(self, user, permission, obj, *, view):
        recorded.append(("provider", self.name))
        return original_provider(self, user, permission, obj, view=view)

    def get_object(self, queryset=None):
        recorded.append(("child", self.cv_viewset.name))
        return original_get_object(self, queryset)

    def enabled(cls, user, obj=None):
        recorded.append(("state", cls.cv_viewset.name))
        return original_enabled(cls, user, obj)

    def holders(self):
        recorded.append(("holders", self.cv_viewset.name))
        return original_holders(self)

    if original_tables is not None:
        monkeypatch.setattr(ancestor_db, "_auth_tables", tables)
    monkeypatch.setattr(ViewSet, "permissions", property(permissions))
    monkeypatch.setattr(ViewSet, "_ancestor_has_permission", provider)
    monkeypatch.setattr(CrudView, "get_object", get_object)
    monkeypatch.setattr(CrudView, "cv_action_enabled", classmethod(enabled))
    monkeypatch.setattr(ManageView, "get_permission_holders", holders)
    return recorded


def _auth_events(events) -> list[tuple]:
    return [event for event in events if event[0] == "auth"]


# ── Task 1: ancestor gates ───────────────────────────────────────────────────


GATE_CASES = [(kind, table) for kind in KINDS for table in _kind_tables(kind)]


@pytest.mark.parametrize("actor", ["superuser", "granted"])
@pytest.mark.parametrize("vocabulary", ["cold", "warm"])
@pytest.mark.parametrize(("kind", "table"), GATE_CASES)
def test_ancestor_gate_refuses_shard_auth_records(adb, world, routes, kind, table, vocabulary, actor):
    """A selected ancestor gate validates its auth records before its vocabulary and before any shortcut (active
    superuser, Guardian checker, ancestor model fallback); a cached vocabulary is not invalidated."""
    user = _actor(f"aa_{actor}", superuser=actor == "superuser")
    if actor == "granted":
        _grant(user, kind, world)
    client = _client(user)
    ancestor = adb.anc[kind]
    if vocabulary == "warm":
        warm = ancestor.permissions
        assert warm
    else:
        ancestor._default_permissions = None
        ContentType.objects.clear_cache()
    routes.read[TABLES[table]] = "shard"
    with captured() as sql, pytest.raises(ImproperlyConfigured, match=REFUSED):
        client.get(_child_url(adb, kind, "detail", world))
    _assert_refused_without_auth_reads(sql)
    if vocabulary == "warm":
        assert ancestor._default_permissions is warm


@pytest.mark.parametrize("explicit", [False, True])
@pytest.mark.parametrize("kind", KINDS)
def test_ancestor_gates_on_default_succeed(adb, world, routes, kind, explicit):
    """Default and explicit-default auth routes keep the gate's real outcome: superuser and granted actors pass,
    an ungranted actor is denied."""
    if explicit:
        for table in _kind_tables(kind):
            routes.read[TABLES[table]] = "default"
    superuser, granted, stranger = (
        _actor("aa_super", superuser=True),
        _actor("aa_granted"),
        _actor("aa_stranger"),
    )
    _grant(granted, kind, world)
    url = _child_url(adb, kind, "detail", world)
    with captured() as sql:
        assert _client(superuser).get(url).status_code == 200
        assert _client(granted).get(url).status_code == 200
        assert _client(stranger).get(url).status_code == 403
    assert _sql(sql.shard) == []


@pytest.mark.parametrize("boundary", ["enabled", "disabled"])
@pytest.mark.parametrize("kind", ["model", "guardian"])
def test_colliding_shard_grants_are_never_consulted(adb, world, routes, monkeypatch, kind, boundary):
    """Mutation check: the actor holds no grant on default, its colliding shard copy does. With the boundary
    disabled a shard Permission route exposes the wrong copy; enabled, the gate refuses and never retries."""
    user = _actor("aa_collide")
    if kind == "model":
        _model_perm(user, Publisher, "view", using="shard")
    else:
        _shard_object_grant(user, Publisher, 41)
    if boundary == "disabled":
        monkeypatch.setattr(ancestor_db, "_auth_tables", lambda model, provider: [], raising=False)
    client = _client(user)
    url = _child_url(adb, kind, "detail", world)
    assert client.get(url).status_code == 403  # default routing: no grant on default
    routes.read[Permission] = "shard"
    if boundary == "disabled":
        assert client.get(url).status_code == 200  # the wrong (shard) copy authorized the request
        return
    with captured() as sql, pytest.raises(ImproperlyConfigured, match=REFUSED):
        client.get(url)
    _assert_refused_without_auth_reads(sql)


@pytest.mark.parametrize("kind", ["model", "guardian"])
def test_actor_bound_to_shard_is_refused_at_the_gate(adb, world, routes, kind):
    """The actor's own database is part of the auth records: a shard-loaded actor never authorizes a gate."""
    shard_actor = User.objects.using("shard").get(pk=_actor("aa_bound", superuser=True).pk)
    with captured() as sql, pytest.raises(ImproperlyConfigured, match=REFUSED):
        _call(_child_url(adb, kind, "detail", world), shard_actor)
    _assert_refused_without_auth_reads(sql)


def test_nearest_only_never_touches_the_unselected_higher_gate(adb, world, routes, events):
    """Nearest-only: only the nearest gate (core Book) reads auth records; the higher Guardian gate gets no route
    check, map or provider call, so its shard grant route is never reached."""
    routes.read[UserObjectPermission] = routes.read[GroupObjectPermission] = "shard"
    client = _client(_actor("aa_near", superuser=True))
    events.clear()
    response = client.get(_note_url(adb.notes[False].vs, adb.gchain, adb.cbook))
    assert response.status_code == 200
    assert _auth_events(events) == [("auth", "Book", "model")]
    assert ("vocabulary", adb.gchain.name) not in events and ("provider", adb.gchain.name) not in events
    assert events.index(("auth", "Book", "model")) < events.index(("vocabulary", adb.cbook.name))


def test_full_cascade_reaches_the_higher_gate_first(adb, world, routes, events):
    routes.read[UserObjectPermission] = routes.read[GroupObjectPermission] = "shard"
    client = _client(_actor("aa_full", superuser=True))
    events.clear()
    with pytest.raises(ImproperlyConfigured, match=REFUSED):
        client.get(_note_url(adb.notes[True].vs, adb.gchain, adb.cbook))
    assert _auth_events(events) == [("auth", "Publisher", "guardian")]
    assert ("vocabulary", adb.gchain.name) not in events and ("vocabulary", adb.cbook.name) not in events


def test_outer_denial_hides_a_deeper_invalid_auth_route(adb, world, routes, events):
    """Full cascade, outermost first: a denied core Publisher gate stops before the deeper Guardian Book gate,
    whose shard grant route is reached only once the outer gate passes."""
    routes.read[UserObjectPermission] = routes.read[GroupObjectPermission] = "shard"
    stranger, reader = _actor("aa_outer_no"), _actor("aa_outer_yes")
    _model_perm(reader, Publisher, "view")
    url = _note_url(adb.InnerDetail.cv_viewset, adb.cchain, adb.gbook)
    events.clear()
    assert _client(stranger).get(url).status_code == 403
    assert _auth_events(events) == [("auth", "Publisher", "model")]
    with pytest.raises(ImproperlyConfigured, match=REFUSED):
        _client(reader).get(url)


def test_anonymous_and_missing_ancestors_do_no_auth_route_work(adb, world, routes, events):
    routes.read[Permission] = routes.read[ContentType] = "shard"
    events.clear()
    assert _client(None).get(_child_url(adb, "model", "detail", world)).status_code == 302
    missing = _url(adb.child["model"].vs, "detail", **{f"{adb.anc['model'].name}_pk": 999, "pk": 71})
    assert _client(_actor("aa_missing", superuser=True)).get(missing).status_code == 404
    assert _auth_events(events) == []


@pytest.mark.parametrize("kind", ["model", "guardian", "direct"])
def test_immediate_parent_helper_refuses_shard_auth_records(adb, world, routes, kind):
    from crud_views.lib.ancestors import _immediate_parent_access

    user = _actor("aa_helper", superuser=True)
    parent = world.shelf if kind == "direct" else world.publisher
    view_class = adb.child[kind].List
    assert _immediate_parent_access(view_class, user, parent) is True
    routes.read[TABLES["direct_user_grant" if kind == "direct" else "permission"]] = "shard"
    with pytest.raises(ImproperlyConfigured, match=REFUSED):
        _immediate_parent_access(view_class, user, parent)


# ── Task 2: local Guardian gates and nested manage after ancestry ────────────

LOCAL_GUARDIAN = {
    "detail": ("GDetail", "detail", True),
    "global_detail": ("GGlobalDetail", "global_detail", True),
    "list": ("GList", "list", False),
    "global_list": ("GGlobalList", "global_list", False),
}
LOCAL_TABLES = ["permission", "contenttype", "user_groups", "user_permissions", "user_grant", "group_grant"]


def _guardian_local_url(adb, name):
    _, key, pk = LOCAL_GUARDIAN[name]
    return _local_url(adb, adb.gloc, key, pk=pk)


@pytest.mark.parametrize("actor", ["superuser", "granted"])
@pytest.mark.parametrize("table", LOCAL_TABLES)
@pytest.mark.parametrize("name", list(LOCAL_GUARDIAN))
def test_all_none_local_guardian_gates_refuse_shard_auth_records(adb, world, routes, events, name, table, actor):
    """All-none ancestry evaluates no ancestor gate, but the endpoint's own Guardian object gate or list filter
    still validates its auth records before the checker, the superuser shortcut or the local model fallback."""
    user = _actor(f"aa_l_{actor}", superuser=actor == "superuser")
    if actor == "granted":
        assign_perm("app.view_book", user, world.book)
        _model_perm(user, Book, "view")
    client = _client(user)
    assert adb.gloc.permissions  # warm vocabulary: the route check still runs
    routes.read[TABLES[table]] = "shard"
    events.clear()
    with captured() as sql, pytest.raises(ImproperlyConfigured, match=REFUSED):
        client.get(_guardian_local_url(adb, name))
    _assert_refused_without_auth_reads(sql)
    assert ("provider", adb.none.name) not in events
    assert _auth_events(events) == [("auth", "Book", "guardian")]


def test_all_none_local_guardian_gates_on_default(adb, world, routes):
    granted, stranger = _actor("aa_lg_yes"), _actor("aa_lg_no")
    assign_perm("app.view_book", granted, world.book)
    globally = _actor("aa_lg_global")
    _model_perm(globally, Book, "view")
    with captured() as sql:
        assert _client(granted).get(_guardian_local_url(adb, "detail")).status_code == 200
        assert _client(stranger).get(_guardian_local_url(adb, "detail")).status_code == 403
        assert _client(globally).get(_guardian_local_url(adb, "detail")).status_code == 403
        assert _client(globally).get(_guardian_local_url(adb, "global_detail")).status_code == 200
        rows = _client(granted).get(_guardian_local_url(adb, "list")).context["object_list"]
        assert [book.title for book in rows] == ["default book"]
        assert list(_client(stranger).get(_guardian_local_url(adb, "list")).context["object_list"]) == []
    assert _sql(sql.shard) == []


def test_local_guardian_gate_refuses_an_actor_bound_to_shard(adb, world, routes):
    shard_actor = User.objects.using("shard").get(pk=_actor("aa_lg_bound", superuser=True).pk)
    for name in ("detail", "list"):
        with captured() as sql, pytest.raises(ImproperlyConfigured, match=REFUSED):
            _call(_guardian_local_url(adb, name), shard_actor)
        _assert_refused_without_auth_reads(sql)


def test_local_guardian_wrong_copy_is_never_consulted(adb, world, routes):
    """A colliding shard grant on the child row: refused, never consulted (and never retried on default)."""
    user = _actor("aa_lg_collide")
    _shard_object_grant(user, Book, 71)
    client = _client(user)
    assert client.get(_guardian_local_url(adb, "detail")).status_code == 403
    routes.read[Permission] = "shard"
    with captured() as sql, pytest.raises(ImproperlyConfigured, match=REFUSED):
        client.get(_guardian_local_url(adb, "detail"))
    _assert_refused_without_auth_reads(sql)


def test_guardian_object_access_helper_refuses_nested_shard_auth_records(adb, world, routes):
    user = _actor("aa_lg_helper")
    assign_perm("app.view_book", user, world.book)
    assert adb.GDetail.cv_has_access(user, world.book) is True
    assert adb.GTDetail.cv_has_access(user, world.book) is True
    routes.read[UserObjectPermission] = "shard"
    with pytest.raises(ImproperlyConfigured, match=REFUSED):
        adb.GDetail.cv_has_access(user, world.book)
    adb.GTDetail.cv_has_access(user, world.book)  # top-level: routed as before, no boundary


def _manage_url(adb, vs):
    return _local_url(adb, vs, "manage", pk=False)


def _manage_mode(monkeypatch, mode):
    from crud_views.lib.settings import crud_views_settings

    monkeypatch.setattr(crud_views_settings, "manage_views_enabled", mode)


def _manage_member(username):
    from crud_views.lib.settings import crud_views_settings

    user = _actor(username)
    user.groups.add(Group.objects.get_or_create(name=crud_views_settings.manage_group)[0])
    return user


@pytest.mark.parametrize("table", ["group", "user_groups"])
def test_nested_group_manage_gate_refuses_shard_auth_records(adb, world, routes, events, monkeypatch, table):
    """The nested manage group gate validates its group route before the membership query; the holder
    diagnostics are never reached."""
    _manage_mode(monkeypatch, "no")
    client = _client(_manage_member("aa_mg"))
    assert client.get(_manage_url(adb, adb.cloc)).status_code == 200
    routes.read[TABLES[table]] = "shard"
    events.clear()
    with captured() as sql, pytest.raises(ImproperlyConfigured, match=REFUSED):
        client.get(_manage_url(adb, adb.cloc))
    _assert_refused_without_auth_reads(sql)
    assert ("holders", adb.cloc.name) not in events


def test_nested_group_manage_anonymous_does_no_auth_route_work(adb, world, routes, events, monkeypatch):
    _manage_mode(monkeypatch, "no")
    routes.read[Group] = routes.read[Permission] = "shard"
    events.clear()
    assert _client(None).get(_manage_url(adb, adb.cloc)).status_code == 302
    assert _auth_events(events) == []


@pytest.mark.parametrize("vs", ["cloc", "gloc"])
def test_public_nested_manage_admits_without_auth_work_then_guards_its_context(adb, world, routes, events, vs):
    """Public manage settings admit without any auth work; the page's own permission rows and holder queries
    are reached auth consumers and refuse a shard route before ``get_permission_holders`` runs."""
    viewset = getattr(adb, vs)
    client = _client(_actor("aa_pm"))
    events.clear()
    assert client.get(_manage_url(adb, viewset)).status_code == 200
    auth_at = [index for index, event in enumerate(events) if event[0] == "auth"]
    assert auth_at and ("holders", viewset.name) in events[auth_at[0] :]
    routes.read[Permission] = "shard"
    events.clear()
    with captured() as sql, pytest.raises(ImproperlyConfigured, match=REFUSED):
        client.get(_manage_url(adb, viewset))
    _assert_refused_without_auth_reads(sql)
    assert ("holders", viewset.name) not in events


def test_guardian_manage_holders_refuse_a_shard_grant_route(adb, world, routes, events):
    """The Guardian holder diagnostics validate the grant tables before their first query, also when called
    directly."""
    client = _client(_actor("aa_gm", superuser=True))
    routes.read[GroupObjectPermission] = "shard"
    events.clear()
    with captured() as sql, pytest.raises(ImproperlyConfigured, match=REFUSED):
        client.get(_manage_url(adb, adb.gloc))
    # the page's own permission rows read (default-routed) Django auth records first; no grant table is read
    grants = ('"guardian_groupobjectpermission"', '"guardian_userobjectpermission"')
    assert [q for q in _sql(sql.default) + _sql(sql.shard) if any(table in q for table in grants)] == []
    assert _foreign_sql(sql.shard) == []
    # refused in the Guardian holder query, before the core holders it extends
    assert _auth_events(events)[-1] == ("auth", "Book", "guardian") and ("holders", adb.gloc.name) not in events
    view = adb.gloc.get_view_class("manage")()
    view.setup(RequestFactory().get(_manage_url(adb, adb.gloc)), **{f"{adb.none.name}_pk": 41})
    view.request.user = User.objects.get(username="aa_gm")
    with pytest.raises(ImproperlyConfigured, match=REFUSED):
        view.get_permission_holders()


def test_top_level_guardian_and_manage_keep_their_routing(adb, world, routes, monkeypatch):
    """Top-level ViewSets: Guardian list/detail gates, the strict ViewSet helper and the manage page keep their
    routed behaviour (no default-database boundary)."""
    user = _actor("aa_top", superuser=True)
    client = _client(user)
    routes.read[Permission] = routes.read[UserObjectPermission] = routes.read[GroupObjectPermission] = "shard"
    assert client.get(_url(adb.gtop, "list")).status_code == 200
    assert client.get(_url(adb.gtop, "detail", pk=71)).status_code == 200
    assert client.get(_url(adb.gtop, "manage")).status_code == 200
    adb.gtop.get_objects_for_user(user, "view").count()
    _manage_mode(monkeypatch, "no")
    routes.read[Group] = "shard"
    assert client.get(_url(adb.ctop, "manage")).status_code == 403  # the shard copy is no manage member


# ── Task 3: core early and local permission checks ───────────────────────────


@pytest.mark.parametrize("key", ["detail", "list"])
@pytest.mark.parametrize("actor", ["anonymous", "inactive"])
def test_all_none_early_core_admission_refuses_shard_auth_records(adb, world, routes, events, actor, key):
    """All-none ancestry: the core early admission of anonymous/inactive actors asks the model permission; its
    auth records are validated first, before the vocabulary and with no child or state lookup."""
    user = None if actor == "anonymous" else _actor("aa_ce_inactive", active=False)
    url = _local_url(adb, adb.cloc, key, pk=key == "detail")
    with override_settings(AUTHENTICATION_BACKENDS=[ALLOW_INACTIVE, ANONYMOUS_READER]):
        client = _client(user)  # logged in through the overridden backend, so the session loads the inactive actor
        expected = 200 if actor == "anonymous" else 403
        assert client.get(url).status_code == expected
        routes.read[Permission] = "shard"
        events.clear()
        with captured() as sql, pytest.raises(ImproperlyConfigured, match=REFUSED):
            client.get(url)
    _assert_refused_without_auth_reads(sql)
    assert _auth_events(events) == [("auth", "Book", "model")]
    assert [event for event in events if event[0] in ("child", "state", "vocabulary")] == []


@pytest.mark.parametrize("vocabulary", ["cold", "warm"])
@pytest.mark.parametrize("table", CORE)
@pytest.mark.parametrize("key", ["detail", "list"])
def test_local_core_gate_refuses_shard_auth_records_before_child_and_state(
    adb, world, routes, events, key, table, vocabulary
):
    """After all-none ancestry, the core local permission check validates its auth records before the
    permission map (``permission_required``), the superuser shortcut, the child lookup and action state."""
    client = _client(_actor("aa_cl", superuser=True))
    url = _local_url(adb, adb.cloc, key, pk=key == "detail")
    assert client.get(url).status_code == 200
    if vocabulary == "warm":
        warm = adb.cloc.permissions
    else:
        adb.cloc._default_permissions = None
        ContentType.objects.clear_cache()
    routes.read[TABLES[table]] = "shard"
    events.clear()
    with captured() as sql, pytest.raises(ImproperlyConfigured, match=REFUSED):
        client.get(url)
    _assert_refused_without_auth_reads(sql)
    assert [event for event in events if event[0] in ("child", "state", "vocabulary")] == []
    if vocabulary == "warm":
        assert adb.cloc._default_permissions is warm


def test_local_core_gate_on_default_keeps_its_outcome(adb, world, routes):
    reader, stranger = _actor("aa_cd_yes"), _actor("aa_cd_no")
    _model_perm(reader, Book, "view")
    url = _local_url(adb, adb.cloc, "detail")
    with captured() as sql:
        assert _client(reader).get(url).status_code == 200
        assert _client(stranger).get(url).status_code == 403
    assert _sql(sql.shard) == []


def test_local_core_gate_refuses_an_actor_bound_to_shard(adb, world, routes, events):
    shard_actor = User.objects.using("shard").get(pk=_actor("aa_cb", superuser=True).pk)
    events.clear()
    with captured() as sql, pytest.raises(ImproperlyConfigured, match=REFUSED):
        _call(_local_url(adb, adb.cloc, "detail"), shard_actor)
    _assert_refused_without_auth_reads(sql)
    assert [event for event in events if event[0] in ("child", "state")] == []


def test_protected_core_child_checks_the_ancestor_then_the_local_records(adb, world, routes, events):
    """Ancestor gate first (Publisher), then the local gate (Book), both before the child lookup; a local denial
    after ancestor success keeps its 403."""
    reader, parent_only = _actor("aa_pc_yes"), _actor("aa_pc_parent")
    for user in (reader, parent_only):
        _model_perm(user, Publisher, "view")
    _model_perm(reader, Book, "view")
    url = _url(adb.pcbook, "detail", **{f"{adb.ppub.name}_pk": 41, "pk": 71})
    events.clear()
    assert _client(reader).get(url).status_code == 200
    order = [event for event in events if event[0] in ("auth", "child")]
    assert order[:3] == [("auth", "Publisher", "model"), ("auth", "Book", "model"), ("child", adb.pcbook.name)]
    assert _client(parent_only).get(url).status_code == 403
    routes.read[Permission] = "shard"
    events.clear()
    with pytest.raises(ImproperlyConfigured, match=REFUSED):
        _client(reader).get(url)
    assert _auth_events(events) == [("auth", "Publisher", "model")]


def test_plain_nested_endpoints_do_no_auth_work(adb, world, routes, events):
    """A nested endpoint without a permission check acquires no auth consumer: shard auth routes do not matter."""
    for table in TABLES.values():
        if table is not User:
            routes.read[table] = "shard"
    events.clear()
    with captured() as sql:
        assert _client(None).get(_local_url(adb, adb.ploc, "detail")).status_code == 200
        assert _client(None).get(_local_url(adb, adb.ploc, "list", pk=False)).status_code == 200
    assert _auth_events(events) == []
    assert _sql(sql.shard) == []


def test_core_access_helper_refuses_nested_shard_auth_records(adb, world, routes):
    user = _actor("aa_ch")
    _model_perm(user, Book, "view")
    assert adb.CDetail.cv_has_access(user) is True
    routes.read[Permission] = "shard"
    with pytest.raises(ImproperlyConfigured, match=REFUSED):
        adb.CDetail.cv_has_access(User.objects.get(pk=user.pk))
    adb.CTDetail.cv_has_access(User.objects.get(pk=user.pk))  # top-level: routed as before


def test_top_level_core_permission_views_keep_their_routing(adb, world, routes):
    client = _client(_actor("aa_ct", superuser=True))
    routes.read[Permission] = routes.read[ContentType] = "shard"
    assert client.get(_url(adb.ctop, "detail", pk=71)).status_code == 200
    assert client.get(_url(adb.ctop, "list")).status_code == 200
