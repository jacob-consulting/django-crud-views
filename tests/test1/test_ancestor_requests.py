"""Core request enforcement of ancestor authorization: selected gates, operation pairs, actor order and manage.

Every test drives real ``Client`` requests against isolated traced chains (``tests.test1.ancestor_cases``) and asserts
exact statuses plus the exact sequence of named events: ``<level>_queryset`` / ``<level>_gate`` for each ancestor
ViewSet, ``child`` for the endpoint's own queryset, and ``local_permission``, ``state``, ``form``, ``save`` and
``on_commit`` for endpoint-local work.
"""

import pytest
from django.contrib.auth.models import Group, Permission, User
from django.core.exceptions import ImproperlyConfigured
from django.test import Client, override_settings

from crud_views.lib.settings import crud_views_settings
from crud_views.lib.viewset import AncestorPermissions, AncestorPolicy, ViewSet
from tests.test1.ancestor_cases import (
    CHECKED,
    EVENTS,
    FixedTemplateMixin,
    ancestor_scope,
    traced_chain,
)
from tests.test1.app.models import AncestorAttachment, Book, BookNote, Publisher

LOGIN = "/accounts/login/"
INACTIVE_BACKENDS = [
    "django.contrib.auth.backends.AllowAllUsersModelBackend",
    "guardian.backends.ObjectPermissionBackend",
]
ANONYMOUS_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "tests.test1.test_ancestor_requests.AnonymousNoteViewBackend",
]
MANAGE_GROUP = "anc_manage_admins"

# Publisher (outer) → Book (inner) → BookNote (endpoint)
TWO = ((Publisher, None, "outer"), (Book, "publisher", "inner"), (BookNote, "book", "child"))
# Publisher (outer) → Book (endpoint)
ONE = ((Publisher, None, "outer"), (Book, "publisher", "child"))
# Publisher (top) → Book (mid) → BookNote (near) → AncestorAttachment (endpoint)
THREE = (
    (Publisher, None, "top"),
    (Book, "publisher", "mid"),
    (BookNote, "book", "near"),
    (AncestorAttachment, "note", "child"),
)


class AnonymousNoteViewBackend:
    """An authentication backend that grants anonymous actors the BookNote view permission."""

    def authenticate(self, request, **credentials):
        return None

    def has_perm(self, user_obj, perm, obj=None):
        return user_obj.is_anonymous and perm == "app.view_booknote"


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


# ── endpoint views ────────────────────────────────────────────────────────────


class LocalTrace:
    """Endpoint-local events of a permission-required view: its local gate and its action state."""

    def has_permission(self):
        EVENTS.append("local_permission")
        return super().has_permission()

    @classmethod
    def cv_action_enabled(cls, user, obj=None):
        EVENTS.append("state")
        return True


class FormTrace:
    """Endpoint-local form, write and commit events."""

    def get_form(self, form_class=None):
        EVENTS.append("form")
        return super().get_form(form_class)

    def cv_form_valid(self, context):
        EVENTS.append("save")
        super().cv_form_valid(context)

    def cv_on_commit(self, context):
        EVENTS.append("on_commit")


def define(scope, viewset, base, key=None, **attrs):
    """Register a fixed-template view of ``base`` (a class or tuple of classes) on ``viewset``."""
    bases = base if isinstance(base, tuple) else (base,)
    if key is not None:
        attrs.update(cv_key=key, cv_path=key)
    name = f"{bases[-1].__name__}{key or ''}{scope.sfx}"
    return type(name, (FixedTemplateMixin, *bases), {"cv_viewset": viewset, "__module__": __name__, **attrs})


def crud_views(scope, viewset, fields):
    """Plain list/detail/create/update/delete views on ``viewset``."""
    from crud_views.lib.views import CreateView, CreateViewParentMixin, DeleteView, DetailView, ListView, UpdateView

    define(scope, viewset, ListView)
    define(scope, viewset, DetailView)
    create = (FormTrace, CreateViewParentMixin, CreateView) if viewset.has_parent else (FormTrace, CreateView)
    define(scope, viewset, create, fields=fields)
    define(scope, viewset, (FormTrace, UpdateView), fields=fields)
    define(scope, viewset, (FormTrace, DeleteView))


# ── data and actors ───────────────────────────────────────────────────────────


def make_user(username="actor", perms=(), groups=(), **extra):
    user = User.objects.create_user(username=username, password="password", **extra)
    for codename in perms:
        user.user_permissions.add(Permission.objects.get(codename=codename, content_type__app_label="app"))
    for name in groups:
        user.groups.add(Group.objects.get_or_create(name=name)[0])
    return user


def client_for(user=None) -> Client:
    client = Client()
    if user is not None:
        client.force_login(user)
    return client


def data():
    publisher = Publisher.objects.create(name="Publisher")
    book = Book.objects.create(title="Book", publisher=publisher)
    note = BookNote.objects.create(book=book, note="Note")
    attachment = AncestorAttachment.objects.create(note=note, text="Attachment")
    other = Publisher.objects.create(name="Other")
    other_book = Book.objects.create(title="Other Book", publisher=other)
    return publisher, book, note, attachment, other_book


def checked_traces():
    return [trace for trace, _permission in CHECKED]


def checked_permissions():
    return [permission for _trace, permission in CHECKED]


# ── independent gates ─────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_core_ancestor_gate_is_independent_of_plain_or_local_child(scope, events):
    from crud_views.lib.views import DetailView, DetailViewPermissionRequired

    routes = traced_chain(scope, ONE)
    child = routes.endpoint
    define(scope, child, DetailView)
    define(scope, child, (LocalTrace, DetailViewPermissionRequired), key="pdetail")
    scope.mount([child])
    publisher, book, *_ = data()

    def get(user, key):
        events.clear()
        return client_for(user).get(routes.url(key, [publisher], obj=book))

    # parent denied: neither a plain child nor a local child grant passes
    child_only = make_user("child-only", ["view_book"])
    assert get(child_only, "detail").status_code == 403
    assert events == ["outer_queryset", "outer_gate"]
    assert get(child_only, "pdetail").status_code == 403
    assert events == ["outer_queryset", "outer_gate"]

    # parent allowed: the plain child has no local gate, the local gate still denies
    parent_only = make_user("parent-only", ["view_publisher"])
    assert get(parent_only, "detail").status_code == 200
    assert events == ["outer_queryset", "outer_gate", "child"]
    assert get(parent_only, "pdetail").status_code == 403
    assert events == ["outer_queryset", "outer_gate", "local_permission"]

    both = make_user("both", ["view_publisher", "view_book"])
    assert get(both, "pdetail").status_code == 200
    assert events == ["outer_queryset", "outer_gate", "local_permission", "child", "state", "child"]


# ── depth and protected positions ─────────────────────────────────────────────

DEPTH_CASES = {
    # id: (global cascade, endpoint cascade, providers top/mid/near, ancestor cascades mid/near, checked levels)
    "global-full": (True, None, (None, None, None), (None, None), ["top", "mid", "near"]),
    "viewset-nearest": (True, False, (None, None, None), (None, None), ["near"]),
    "global-nearest": (False, None, (None, None, None), (None, None), ["near"]),
    "viewset-full": (False, True, (None, None, None), (None, None), ["top", "mid", "near"]),
    "explicit-model": (True, None, ("model", "model", "model"), (None, None), ["top", "mid", "near"]),
    "ancestor-cascade-cannot-stop": (True, None, (None, None, None), (False, False), ["top", "mid", "near"]),
    "none-middle-full": (True, None, (None, "none", None), (None, None), ["top", "near"]),
    "none-middle-nearest": (True, False, (None, "none", None), (None, None), ["near"]),
    "none-nearest-nearest": (True, False, (None, None, "none"), (None, None), ["mid"]),
    "none-nearest-full": (True, None, (None, None, "none"), (None, None), ["top", "mid"]),
    "all-none": (True, None, ("none", "none", "none"), (None, None), []),
}


def depth_policies(endpoint_cascade, providers, ancestor_cascades):
    policies = {0: AncestorPolicy(provider=providers[0])}
    for index in (1, 2):
        policies[index] = AncestorPolicy(provider=providers[index], cascade=ancestor_cascades[index - 1])
    policies[3] = AncestorPolicy(cascade=endpoint_cascade)
    return policies


@pytest.mark.django_db
@pytest.mark.parametrize("case", DEPTH_CASES)
def test_depth_and_protected_positions(scope, events, monkeypatch, case):
    from crud_views.lib.views import DetailView

    global_cascade, endpoint_cascade, providers, ancestor_cascades, expected_levels = DEPTH_CASES[case]
    monkeypatch.setattr(crud_views_settings, "ancestor_permission_cascade", global_cascade)
    routes = traced_chain(scope, THREE, policies=depth_policies(endpoint_cascade, providers, ancestor_cascades))
    define(scope, routes.endpoint, DetailView)
    scope.mount([routes.endpoint])
    publisher, book, note, attachment, _ = data()
    user = make_user("reader", ["view_publisher", "view_book", "view_booknote"])

    response = client_for(user).get(routes.url("detail", [publisher, book, note], obj=attachment))

    assert response.status_code == 200
    assert checked_traces() == expected_levels
    expected_events = []
    for level in ("top", "mid", "near"):
        expected_events.append(f"{level}_queryset")
        if level in expected_levels:
            expected_events.append(f"{level}_gate")
    assert events == [*expected_events, "child"]
    model_names = {"top": "publisher", "mid": "book", "near": "booknote"}
    assert checked_permissions() == [f"app.view_{model_names[level]}" for level in expected_levels]


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("providers", "perms", "denied_level"),
    [
        ((None, None, None), ["view_publisher", "view_book"], "near"),
        ((None, None, "none"), ["view_publisher", "view_booknote"], "mid"),
    ],
    ids=["nearest", "none-nearest"],
)
def test_denied_nearest_never_tries_a_farther_ancestor(scope, events, providers, perms, denied_level):
    from crud_views.lib.views import DetailView

    routes = traced_chain(scope, THREE, policies=depth_policies(False, providers, (None, None)))
    define(scope, routes.endpoint, DetailView)
    scope.mount([routes.endpoint])
    publisher, book, note, attachment, _ = data()
    user = make_user("partial", perms)

    response = client_for(user).get(routes.url("detail", [publisher, book, note], obj=attachment))

    assert response.status_code == 403
    assert checked_traces() == [denied_level]
    assert "child" not in events


# ── operation pairs ───────────────────────────────────────────────────────────

READ = ["app.view_publisher", "app.view_book"]
WRITE = ["app.view_publisher", "app.change_book"]


@pytest.mark.django_db
def test_read_write_and_complete_pair_override(scope, events, django_capture_on_commit_callbacks):
    routes = traced_chain(scope, TWO)
    crud_views(scope, routes.endpoint, ["note"])
    scope.mount([routes.endpoint])
    publisher, book, note, *_ = data()
    parents = [publisher, book]
    client = client_for(make_user("writer", ["view_publisher", "view_book", "change_book"]))

    def check(method, key, expected_status, expected_permissions, obj=None, payload=None):
        events.clear()
        CHECKED.clear()
        url = routes.url(key, parents, obj=obj)
        with django_capture_on_commit_callbacks(execute=True):
            response = client.post(url, payload or {}) if method == "post" else client.get(url)
        assert response.status_code == expected_status, (method, key)
        assert checked_permissions() == expected_permissions, (method, key)

    check("get", "list", 200, READ)
    check("get", "detail", 200, READ, obj=note)
    check("get", "create", 200, WRITE)
    assert events == ["outer_queryset", "outer_gate", "inner_queryset", "inner_gate", "form"]
    check("post", "create", 302, WRITE, payload={"note": "Created"})
    assert events == ["outer_queryset", "outer_gate", "inner_queryset", "inner_gate", "form", "save", "on_commit"]
    created = BookNote.objects.get(note="Created")
    assert created.book == book
    check("get", "update", 200, WRITE, obj=note)
    check("post", "update", 302, WRITE, obj=note, payload={"note": "Updated"})
    check("get", "delete", 200, WRITE, obj=created)
    check("post", "delete", 302, WRITE, obj=created)
    assert not BookNote.objects.filter(pk=created.pk).exists()

    # parent delete alone does not permit a child delete: the Write pair needs parent change
    deleter = client_for(make_user("deleter", ["view_publisher", "view_book", "delete_book"]))
    for method in ("get", "post"):
        events.clear()
        url = routes.url("delete", parents, obj=note)
        response = deleter.post(url) if method == "post" else deleter.get(url)
        assert response.status_code == 403
        assert events == ["outer_queryset", "outer_gate", "inner_queryset", "inner_gate"]
    assert BookNote.objects.filter(pk=note.pk).exists()


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("pair", "allowed_perms", "denied_perms", "expected"),
    [
        (("change", "change"), ["change_publisher", "change_book"], ["view_publisher", "change_book"], "change"),
        (("view", "view"), ["view_publisher", "view_book"], ["view_publisher"], "view"),
    ],
    ids=["change-change", "view-view"],
)
def test_complete_write_pair_replaces_the_default(scope, events, pair, allowed_perms, denied_perms, expected):
    from crud_views.lib.views import ListView, UpdateView

    write = AncestorPermissions(nearest=pair[0], higher=pair[1])
    routes = traced_chain(scope, TWO, policies={2: AncestorPolicy(write=write)})
    define(scope, routes.endpoint, ListView)
    define(scope, routes.endpoint, UpdateView, fields=["note"])
    scope.mount([routes.endpoint])
    publisher, book, note, *_ = data()
    url = routes.url("update", [publisher, book], obj=note)

    assert client_for(make_user("allowed", allowed_perms)).get(url).status_code == 200
    assert checked_permissions() == [f"app.{expected}_publisher", f"app.{expected}_book"]
    assert client_for(make_user("denied", denied_perms)).get(url).status_code == 403


@pytest.mark.django_db
def test_each_ancestor_resolves_its_own_permission_map(scope, events):
    from crud_views.lib.views import DetailView

    actions = {
        "detail": AncestorPermissions(nearest="change", higher="delete"),
        "approve": AncestorPermissions(nearest="approve", higher="view"),
    }
    routes = traced_chain(scope, TWO, policies={2: AncestorPolicy(actions=actions)})
    define(scope, routes.endpoint, DetailView)
    define(scope, routes.endpoint, DetailView, key="approve")
    scope.mount([routes.endpoint])
    publisher, book, note, *_ = data()

    user = make_user("mapped", ["delete_publisher", "change_book"])
    response = client_for(user).get(routes.url("detail", [publisher, book], obj=note))
    assert response.status_code == 200
    assert CHECKED == [("outer", "app.delete_publisher"), ("inner", "app.change_book")]

    # a selected key missing from the reached ancestor's map is a configuration error, never a weaker check
    CHECKED.clear()
    url = routes.url("approve", [publisher, book], obj=note)
    with pytest.raises(ImproperlyConfigured, match="'approve'") as error:
        client_for(make_user("approver", ["view_publisher"])).get(url)
    assert routes.viewsets[1].name in str(error.value)
    assert CHECKED == [("outer", "app.view_publisher")]

    # an outer denial is reached first: the deeper missing key is never resolved
    events.clear()
    CHECKED.clear()
    assert client_for(make_user("outsider")).get(url).status_code == 403
    assert events == ["outer_queryset", "outer_gate"]


@pytest.mark.django_db
def test_unregistered_action_key_fails_the_request_before_lookup(scope, events):
    """The runtime guard of E321: a completed registry with a stale ``actions`` key rejects every request."""
    from crud_views.lib.views import DetailView

    actions = {"approve": AncestorPermissions(nearest="change", higher="view")}
    routes = traced_chain(scope, TWO, policies={2: AncestorPolicy(actions=actions)})
    define(scope, routes.endpoint, DetailView)  # "approve" is never registered
    scope.mount([routes.endpoint])
    publisher, book, note, *_ = data()

    url = routes.url("detail", [publisher, book], obj=note)
    with pytest.raises(ImproperlyConfigured, match=r"ancestor_policy.actions\['approve'\].*names no registered view"):
        client_for(make_user("reader", ["view_publisher", "view_book"])).get(url)
    assert events == [] and CHECKED == []


# ── interleaved order ─────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_outer_denial_prevents_deeper_queries_and_local_work(scope, events):
    from crud_views.lib.views import DetailViewPermissionRequired

    routes = traced_chain(scope, TWO)
    define(scope, routes.endpoint, (LocalTrace, DetailViewPermissionRequired))
    scope.mount([routes.endpoint])
    publisher, *_ = data()
    url = routes.url("detail", [publisher, Book(pk=999999)], obj=BookNote(pk=999999))

    response = client_for(make_user("outsider", ["view_book", "view_booknote"])).get(url)

    assert response.status_code == 403
    assert events == ["outer_queryset", "outer_gate"]


# ── actor order ───────────────────────────────────────────────────────────────


def all_none_routes(scope):
    from crud_views.lib.views import DetailView, DetailViewPermissionRequired

    policies = {0: AncestorPolicy(provider="none"), 1: AncestorPolicy(provider="none")}
    routes = traced_chain(scope, TWO, policies=policies)
    define(scope, routes.endpoint, (LocalTrace, DetailViewPermissionRequired))
    define(scope, routes.endpoint, DetailView, key="public")
    scope.mount([routes.endpoint])
    return routes


def ancestry_urls(routes, key, with_object=True):
    publisher, book, note, _attachment, other_book = data()
    obj = note if with_object else None
    return {
        "valid": routes.url(key, [publisher, book], obj=obj),
        "missing": routes.url(key, [publisher, Book(pk=999999)], obj=obj),
        "mismatched": routes.url(key, [publisher, other_book], obj=obj),
    }


@pytest.mark.django_db
def test_all_none_preserves_existing_actor_admission(scope, events):
    routes = all_none_routes(scope)
    urls = ancestry_urls(routes, "detail")

    for name, url in urls.items():
        events.clear()
        response = Client().get(url)
        assert response.status_code == 302, name
        assert response["Location"] == f"{LOGIN}?next={url}", name
        assert events == [], name

    inactive = make_user("inactive", ["view_booknote"], is_active=False)
    with override_settings(AUTHENTICATION_BACKENDS=INACTIVE_BACKENDS):
        client = client_for(inactive)
        for name, url in urls.items():
            events.clear()
            assert client.get(url).status_code == 403, name
            assert events == [], name


@pytest.mark.django_db
def test_all_none_adds_no_actor_restriction(scope, events):
    routes = all_none_routes(scope)
    urls = ancestry_urls(routes, "detail")
    with override_settings(AUTHENTICATION_BACKENDS=ANONYMOUS_BACKENDS):
        assert Client().get(urls["valid"]).status_code == 200
        assert Client().get(urls["missing"]).status_code == 404
        assert Client().get(urls["mismatched"]).status_code == 404

    public = {name: url.replace("/detail/", "/public/") for name, url in urls.items()}
    events.clear()
    assert Client().get(public["valid"]).status_code == 200
    assert events == ["outer_queryset", "inner_queryset", "child"]
    assert Client().get(public["missing"]).status_code == 404
    assert Client().get(public["mismatched"]).status_code == 404

    # public manage (CRUD_VIEWS_MANAGE_VIEWS_ENABLED="yes" in the test settings)
    manage = ancestry_urls(routes, "manage", with_object=False)
    assert Client().get(manage["valid"]).status_code == 200
    assert Client().get(manage["missing"]).status_code == 404


@pytest.mark.django_db
def test_protected_ancestry_rejects_anonymous_and_inactive_before_lookup(scope, events):
    from crud_views.lib.views import DetailView

    routes = traced_chain(scope, TWO)
    define(scope, routes.endpoint, DetailView)
    scope.mount([routes.endpoint])
    urls = ancestry_urls(routes, "detail")

    # a plain endpoint has no AccessMixin: the default login redirect
    for name, url in urls.items():
        events.clear()
        response = Client().get(url)
        assert response.status_code == 302, name
        assert response["Location"] == f"{LOGIN}?next={url}", name
        assert events == [], name

    superuser = make_user("inactive-root", is_active=False, is_superuser=True)
    with override_settings(AUTHENTICATION_BACKENDS=INACTIVE_BACKENDS):
        for name, url in urls.items():
            events.clear()
            assert client_for(superuser).get(url).status_code == 403, name
            assert events == [], name


@pytest.mark.django_db
def test_protected_ancestry_keeps_the_endpoint_denial_configuration(scope, events):
    from crud_views.lib.views import DetailViewPermissionRequired

    routes = traced_chain(scope, TWO)
    define(scope, routes.endpoint, DetailViewPermissionRequired, raise_exception=True)
    define(scope, routes.endpoint, DetailViewPermissionRequired, key="custom", login_url="/custom-login/")
    scope.mount([routes.endpoint])
    urls = ancestry_urls(routes, "detail")

    assert Client().get(urls["missing"]).status_code == 403
    custom = urls["missing"].replace("/detail/", "/custom/")
    response = Client().get(custom)
    assert response.status_code == 302
    assert response["Location"] == f"/custom-login/?next={custom}"
    assert events == []


# ── top-level ─────────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_top_level_does_no_ancestor_work(scope, events, monkeypatch):
    from crud_views.lib.view import ancestors

    def fail(*args, **kwargs):
        raise AssertionError("ancestor work on a top-level request")

    monkeypatch.setattr(ancestors, "authorize_ancestors", fail)
    monkeypatch.setattr(ancestors, "walk_ancestors", fail)
    monkeypatch.setattr(ViewSet, "_ancestor_has_permission", fail)
    routes = traced_chain(scope, ((Publisher, None, "child"),))
    crud_views(scope, routes.endpoint, ["name"])
    scope.mount([routes.endpoint])
    publisher = Publisher.objects.create(name="Top")
    client = client_for(make_user("top"))

    assert client.get(routes.url("list", [])).status_code == 200
    assert client.get(routes.url("detail", [], obj=publisher)).status_code == 200
    assert client.get(routes.url("create", [])).status_code == 200
    assert client.post(routes.url("create", []), {"name": "Created"}).status_code == 302
    assert client.get(routes.url("manage", [])).status_code == 200
    assert Client().get(routes.url("detail", [], obj=publisher)).status_code == 200
    assert not [event for event in events if event.endswith("_gate")]


# ── manage ────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_nested_core_manage_requires_both_gates(scope, events, monkeypatch):
    routes = traced_chain(scope, ONE)
    scope.mount([routes.endpoint])
    publisher, *_ = data()
    url = routes.url("manage", [publisher])
    missing = routes.url("manage", [Publisher(pk=999999)])

    # public manage cannot bypass ancestry
    monkeypatch.setattr(crud_views_settings, "manage_views_enabled", "yes")
    response = Client().get(url)
    assert (response.status_code, response["Location"], events) == (302, f"{LOGIN}?next={url}", [])
    assert client_for(make_user("public-outsider")).get(url).status_code == 403
    assert events == ["outer_queryset", "outer_gate"]
    assert client_for(make_user("public-reader", ["view_publisher"])).get(url).status_code == 200

    # debug-only manage cannot bypass ancestry either
    monkeypatch.setattr(crud_views_settings, "manage_views_enabled", "debug_only")
    with override_settings(DEBUG=True):
        assert client_for(make_user("debug-outsider")).get(url).status_code == 403
        assert client_for(make_user("debug-reader", ["view_publisher"])).get(url).status_code == 200

    # group manage: both the ancestor gate and the manage group are required
    monkeypatch.setattr(crud_views_settings, "manage_views_enabled", "no")
    monkeypatch.setattr(crud_views_settings, "manage_group", MANAGE_GROUP)
    events.clear()
    assert client_for(make_user("reader", ["view_publisher"])).get(url).status_code == 403
    assert events == ["outer_queryset", "outer_gate"]
    assert client_for(make_user("member", groups=[MANAGE_GROUP])).get(url).status_code == 403
    admin = client_for(make_user("admin", ["view_publisher"], groups=[MANAGE_GROUP]))
    assert admin.get(url).status_code == 200
    events.clear()
    assert admin.get(missing).status_code == 404
    assert events == ["outer_queryset"]


@pytest.mark.django_db
def test_nested_manage_nearest_only_and_all_none(scope, events, monkeypatch):
    monkeypatch.setattr(crud_views_settings, "manage_views_enabled", "no")
    monkeypatch.setattr(crud_views_settings, "manage_group", MANAGE_GROUP)
    nearest = traced_chain(scope, TWO, policies={2: AncestorPolicy(cascade=False)}, prefix="near")
    unprotected = traced_chain(
        scope, TWO, policies={0: AncestorPolicy(provider="none"), 1: AncestorPolicy(provider="none")}, prefix="none"
    )
    scope.mount([nearest.endpoint, unprotected.endpoint])
    publisher, book, *_ = data()
    admin = client_for(make_user("admin", ["view_book"], groups=[MANAGE_GROUP]))

    assert admin.get(nearest.url("manage", [publisher, book])).status_code == 200
    assert checked_traces() == ["inner"]

    url = unprotected.url("manage", [publisher, book])
    events.clear()
    response = Client().get(url)
    assert (response.status_code, response["Location"], events) == (302, f"{LOGIN}?next={url}", [])
    assert client_for(make_user("outsider")).get(url).status_code == 403
    assert admin.get(url).status_code == 200
    assert admin.get(unprotected.url("manage", [publisher, Book(pk=999999)])).status_code == 404
