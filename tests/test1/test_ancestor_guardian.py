"""
Phase 06.18 plan 03 — Guardian ancestors through the shared ancestor engine.

A ``GuardianViewSet`` used as an ancestor is a strict object-permission gate (its class default provider is
``"guardian"``): the required permission comes from that ancestor's own permission map (Guardian's configured
content-type semantics), satisfied by a direct or group object grant on the resolved ancestor object. Only the
ancestor's own ``AncestorPolicy.accept_global_perms`` adds the model permission as an alternative. The endpoint
view's ``cv_guardian_accept_global_perms`` keeps its local meaning and never relaxes ancestry; a plain or core
child cannot bypass a Guardian ancestor; local child gates still apply after ancestry succeeds.

Requests go through real URLs with database-backed grants. Every fixture builds fresh, uniquely named
ViewSets behind a temporary ROOT_URLCONF and restores the registry and caches (``isolated_routes``).
"""

from __future__ import annotations

import re
from types import SimpleNamespace

import pytest
from django.contrib.auth.models import Group, PermissionsMixin
from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django.test import Client, override_settings
from django.test.utils import CaptureQueriesContext
from guardian.conf import settings as guardian_settings
from guardian.core import ObjectPermissionChecker
from guardian.shortcuts import assign_perm

from crud_views.lib.viewset import AncestorPolicy, ParentViewSet, ViewSet
from tests.test1.app.models import Book, Publisher, PublisherProxy
from tests.test1.test_ancestor_authorization import _client, _url, _user, isolated_routes

ALLOW_INACTIVE = "django.contrib.auth.backends.AllowAllUsersModelBackend"
GUARDIAN_BACKENDS = [ALLOW_INACTIVE, "guardian.backends.ObjectPermissionBackend"]
PROXY_CT = "tests.test1.test_ancestor_guardian.proxy_content_type"


def proxy_content_type(obj):
    """A configured Guardian content-type hook: proxy models keep their own content type."""
    return ContentType.objects.get_for_model(obj, for_concrete_model=False)


# ── routes ───────────────────────────────────────────────────────────────────

PARENTS = ("guardian", "fallback", "core", "proxy")


@pytest.fixture
def routes():
    """For every parent kind — strict Guardian, Guardian with ancestor fallback, core and a Guardian proxy-model
    parent — a nested Guardian Book ViewSet (list, list with the local global-permission flag, detail, create)
    and a nested plain core Book ViewSet (list only, no endpoint-local gate)."""
    from crud_views.lib.views import CreateViewParentMixin, ListView
    from crud_views_guardian.lib.views import (
        GuardianCreateViewPermissionRequired,
        GuardianDetailViewPermissionRequired,
        GuardianListViewPermissionRequired,
    )
    from crud_views_guardian.lib.viewset import GuardianViewSet

    def build(sfx):
        parents = {
            "guardian": GuardianViewSet(model=Publisher, name=f"agpub{sfx}"),
            "fallback": GuardianViewSet(
                model=Publisher, name=f"agpubfb{sfx}", ancestor_policy=AncestorPolicy(accept_global_perms=True)
            ),
            "core": ViewSet(model=Publisher, name=f"agcpub{sfx}"),
            "proxy": GuardianViewSet(model=PublisherProxy, name=f"agproxy{sfx}"),
        }
        ns = SimpleNamespace(parents=parents, guardian={}, plain={}, views={})
        for kind, parent in parents.items():
            edge = ParentViewSet(name=parent.name, attribute="publisher")
            gbook = GuardianViewSet(model=Book, name=f"agb{kind}{sfx}", parent=edge)
            pbook = ViewSet(
                model=Book, name=f"agp{kind}{sfx}", parent=ParentViewSet(name=parent.name, attribute="publisher")
            )
            common = {"cv_viewset": gbook, "cv_context_actions": []}
            ns.views[kind] = SimpleNamespace(
                List=type("List", (GuardianListViewPermissionRequired,), {**common, "cv_list_actions": []}),
                GlobalList=type(
                    "GlobalList",
                    (GuardianListViewPermissionRequired,),
                    {
                        **common,
                        "cv_list_actions": [],
                        "cv_key": "global_list",
                        "cv_path": "global",
                        "cv_guardian_accept_global_perms": True,
                    },
                ),
                Detail=type("Detail", (GuardianDetailViewPermissionRequired,), dict(common)),
                Create=type(
                    "Create",
                    (CreateViewParentMixin, GuardianCreateViewPermissionRequired),
                    {**common, "fields": ["title"]},
                ),
                PlainList=type(
                    "PlainList", (ListView,), {"cv_viewset": pbook, "cv_list_actions": [], "cv_context_actions": []}
                ),
            )
            ns.guardian[kind] = gbook
            ns.plain[kind] = pbook
        routed = [*parents.values(), *ns.guardian.values(), *ns.plain.values()]
        return ns, routed

    with isolated_routes(build) as ns:
        yield ns


@pytest.fixture
def world(db):
    penguin = Publisher.objects.create(name="Penguin")
    other = Publisher.objects.create(name="Other")
    granted = Book.objects.create(title="Granted", publisher=penguin)
    ungranted = Book.objects.create(title="Ungranted", publisher=penguin)
    return SimpleNamespace(penguin=penguin, other=other, granted=granted, ungranted=ungranted)


def _kwargs(routes, kind, publisher):
    return {f"{routes.parents[kind].name}_pk": publisher.pk}


def _guardian_url(routes, kind, key, publisher, **extra):
    return _url(routes.guardian[kind], key, **_kwargs(routes, kind, publisher), **extra)


def _plain_url(routes, kind, publisher):
    return _url(routes.plain[kind], "list", **_kwargs(routes, kind, publisher))


def _object_grant(user_or_group, routes, kind, action, obj):
    assign_perm(routes.parents[kind].permissions[action], user_or_group, obj)


@pytest.fixture
def events(monkeypatch):
    """Ordered framework events: ViewSet queryset calls, Guardian object checks and model permission checks."""
    recorded: list[tuple[str, str]] = []
    original_queryset = ViewSet.get_queryset
    original_checker = ObjectPermissionChecker.has_perm
    original_has_perm = PermissionsMixin.has_perm

    def queryset_spy(self, view):
        recorded.append(("queryset", self.name))
        return original_queryset(self, view)

    def checker_spy(self, perm, obj):
        recorded.append(("object_perm", perm))
        return original_checker(self, perm, obj)

    def has_perm_spy(self, perm, obj=None):
        recorded.append(("model_perm", perm))
        return original_has_perm(self, perm, obj)

    monkeypatch.setattr(ViewSet, "get_queryset", queryset_spy)
    monkeypatch.setattr(ObjectPermissionChecker, "has_perm", checker_spy)
    monkeypatch.setattr(PermissionsMixin, "has_perm", has_perm_spy)
    return recorded


def _publisher_reads(captured) -> list[str]:
    return [q["sql"] for q in captured.captured_queries if re.search(r'FROM "app_publisher"', q["sql"])]


# ── independent gates ────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_plain_child_cannot_bypass_strict_guardian_parent(routes, world):
    # every model grant, no object grant on the Guardian parent: the plain child has no local gate to pass,
    # and the ancestor gate still denies
    user = _user("ag_plain_model", (Publisher, "view"), (Publisher, "change"), (Book, "view"))
    assert _client(user).get(_plain_url(routes, "guardian", world.penguin)).status_code == 403
    _object_grant(user, routes, "guardian", "view", world.penguin)
    response = _client(user).get(_plain_url(routes, "guardian", world.penguin))
    assert response.status_code == 200
    assert set(response.context["object_list"]) == {world.granted, world.ungranted}


@pytest.mark.django_db
def test_object_grant_on_another_parent_does_not_satisfy_the_gate(routes, world):
    user = _user("ag_other_parent")
    _object_grant(user, routes, "guardian", "view", world.other)
    assert _client(user).get(_plain_url(routes, "guardian", world.penguin)).status_code == 403


@pytest.mark.django_db
def test_global_child_grant_and_local_flag_do_not_substitute_parent_grant(routes, world):
    # the Book view's local cv_guardian_accept_global_perms and every model grant on Book and Publisher do not
    # relax the strict Guardian Publisher ancestor
    user = _user("ag_global_child", (Book, "view"), (Publisher, "view"))
    client = _client(user)
    assert client.get(_guardian_url(routes, "guardian", "global_list", world.penguin)).status_code == 403
    assert client.get(_guardian_url(routes, "guardian", "list", world.penguin)).status_code == 403
    _object_grant(user, routes, "guardian", "view", world.penguin)
    # ancestry passes; the local flag keeps its local meaning (model Book view lists every row) …
    response = client.get(_guardian_url(routes, "guardian", "global_list", world.penguin))
    assert response.status_code == 200
    assert set(response.context["object_list"]) == {world.granted, world.ungranted}
    # … and the strict local list filter stays strict
    response = client.get(_guardian_url(routes, "guardian", "list", world.penguin))
    assert response.status_code == 200
    assert list(response.context["object_list"]) == []


@pytest.mark.django_db
def test_local_child_denial_remains_after_ancestor_success(routes, world):
    user = _user("ag_local_denied")
    _object_grant(user, routes, "guardian", "view", world.penguin)
    client = _client(user)
    detail = _guardian_url(routes, "guardian", "detail", world.penguin, pk=world.ungranted.pk)
    assert client.get(detail).status_code == 403
    assign_perm(routes.guardian["guardian"].permissions["view"], user, world.granted)
    granted = _guardian_url(routes, "guardian", "detail", world.penguin, pk=world.granted.pk)
    assert client.get(granted).status_code == 200
    response = client.get(_guardian_url(routes, "guardian", "list", world.penguin))
    assert list(response.context["object_list"]) == [world.granted]


@pytest.mark.django_db
def test_local_object_grant_without_parent_grant_is_denied(routes, world):
    user = _user("ag_child_only")
    assign_perm(routes.guardian["guardian"].permissions["view"], user, world.granted)
    detail = _guardian_url(routes, "guardian", "detail", world.penguin, pk=world.granted.pk)
    assert _client(user).get(detail).status_code == 403


# ── provider truth table ─────────────────────────────────────────────────────


@pytest.mark.django_db
@pytest.mark.parametrize("fallback", [False, True], ids=["fallback-off", "fallback-on"])
@pytest.mark.parametrize("model_grant", [False, True], ids=["no-model", "model"])
@pytest.mark.parametrize("object_grant", [False, True], ids=["no-object", "object"])
def test_fallback_truth_table(routes, world, object_grant, model_grant, fallback):
    kind = "fallback" if fallback else "guardian"
    user = _user(f"ag_tt_{int(object_grant)}{int(model_grant)}{int(fallback)}", *([(Publisher, "view")] * model_grant))
    if object_grant:
        _object_grant(user, routes, kind, "view", world.penguin)
    expected = 200 if object_grant or (model_grant and fallback) else 403
    assert _client(user).get(_plain_url(routes, kind, world.penguin)).status_code == expected


@pytest.mark.django_db
def test_fallback_uses_the_required_permission_only(routes, world):
    # the Write pair needs change on the nearest ancestor: a model view grant is no fallback for it
    user = _user("ag_fallback_view_only", (Publisher, "view"))
    create = _guardian_url(routes, "fallback", "create", world.penguin)
    assert _client(user).get(create).status_code == 403
    editor = _user("ag_fallback_change", (Publisher, "change"))
    assert _client(editor).get(create).status_code == 200


@pytest.mark.django_db
def test_group_object_grant_satisfies_the_gate(routes, world):
    user = _user("ag_group_member")
    group = Group.objects.create(name="ag_readers")
    user.groups.add(group)
    _object_grant(group, routes, "guardian", "view", world.penguin)
    assert _client(user).get(_plain_url(routes, "guardian", world.penguin)).status_code == 200


@pytest.mark.django_db
def test_active_superuser_satisfies_strict_guardian_ancestor(routes, world):
    user = _user("ag_super", superuser=True)
    assert _client(user).get(_plain_url(routes, "guardian", world.penguin)).status_code == 200
    response = _client(user).get(_guardian_url(routes, "guardian", "list", world.penguin))
    assert response.status_code == 200


@pytest.mark.django_db
@pytest.mark.parametrize("superuser", [False, True], ids=["user", "superuser"])
@pytest.mark.parametrize("child", ["plain", "guardian"])
def test_inactive_actor_is_denied_before_any_ancestor_work(routes, world, events, superuser, child):
    user = _user(f"ag_inactive_{child}_{int(superuser)}", (Publisher, "view"), superuser=superuser)
    _object_grant(user, routes, "fallback", "view", world.penguin)
    user.is_active = False
    user.save()
    url = (
        _plain_url(routes, "fallback", world.penguin)
        if child == "plain"
        else _guardian_url(routes, "fallback", "list", world.penguin)
    )
    with override_settings(AUTHENTICATION_BACKENDS=GUARDIAN_BACKENDS):
        client = Client()
        client.force_login(user)
        events.clear()
        response = client.get(url)
    assert response.status_code == 403
    assert events == []  # no ancestor lookup, no object or model permission evaluation


@pytest.mark.django_db
@pytest.mark.parametrize(("behavior", "status"), [("redirect", 302), ("403", 403), ("404", 404)])
def test_guardian_child_anonymous_behavior_is_preserved_before_ancestor_lookup(
    routes, world, events, monkeypatch, behavior, status
):
    monkeypatch.setattr(routes.views["guardian"].List, "cv_guardian_anonymous_behavior", behavior)
    events.clear()
    response = Client().get(_guardian_url(routes, "guardian", "list", world.penguin))
    assert response.status_code == status
    if status == 302:
        assert response["Location"].startswith("/accounts/login/?next=")
    assert events == []


@pytest.mark.django_db
def test_plain_child_anonymous_gets_login_redirect_before_lookup(routes, world, events):
    events.clear()
    response = Client().get(_plain_url(routes, "guardian", world.penguin))
    assert response.status_code == 302
    assert events == []


# ── configured content types ─────────────────────────────────────────────────


@pytest.fixture
def proxy_content_types(monkeypatch):
    monkeypatch.setattr(guardian_settings, "GET_CONTENT_TYPE", PROXY_CT)
    ContentType.objects.clear_cache()
    yield
    ContentType.objects.clear_cache()


@pytest.mark.django_db
def test_configured_content_type_drives_the_ancestor_permission(proxy_content_types, routes, world):
    proxy_vs = routes.parents["proxy"]
    assert proxy_vs.permissions["view"] == "app.view_publisherproxy"
    proxy = PublisherProxy.objects.get(pk=world.penguin.pk)
    concrete = _user("ag_concrete_grant")
    assign_perm("app.view_publisher", concrete, world.penguin)  # the concrete model's grant is another permission
    assert _client(concrete).get(_plain_url(routes, "proxy", world.penguin)).status_code == 403
    configured = _user("ag_proxy_grant")
    assign_perm(proxy_vs.permissions["view"], configured, proxy)
    assert _client(configured).get(_plain_url(routes, "proxy", world.penguin)).status_code == 200


# ── core parent versus Guardian parent (migration) ───────────────────────────


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("parent", "grant", "status"),
    [
        ("core", "object", 403),
        ("core", "model", 200),
        ("guardian", "object", 200),
        ("guardian", "model", 403),
    ],
)
def test_guardian_child_parent_gate_follows_the_parent_provider(routes, world, parent, grant, status):
    user = _user(f"ag_mixed_{parent}_{grant}", *([(Publisher, "view")] if grant == "model" else []))
    if grant == "object":
        assign_perm("app.view_publisher", user, world.penguin)
    assign_perm(routes.guardian[parent].permissions["view"], user, world.granted)  # local object gate passes
    client = _client(user)
    assert client.get(_guardian_url(routes, parent, "list", world.penguin)).status_code == status
    detail = _guardian_url(routes, parent, "detail", world.penguin, pk=world.granted.pk)
    assert client.get(detail).status_code == status


# ── single traversal, nested create and strict helper ────────────────────────


@pytest.mark.django_db
@pytest.mark.parametrize("key", ["list", "create"])
def test_guardian_child_resolves_the_parent_once(routes, world, key):
    user = _user(f"ag_once_{key}")
    _object_grant(user, routes, "guardian", "view", world.penguin)
    _object_grant(user, routes, "guardian", "change", world.penguin)
    client = _client(user)
    with CaptureQueriesContext(connection) as captured:
        response = client.get(_guardian_url(routes, "guardian", key, world.penguin))
    assert response.status_code == 200
    assert len(_publisher_reads(captured)) == 1, _publisher_reads(captured)


@pytest.mark.django_db
def test_guardian_ancestor_is_checked_through_the_shared_engine_order(routes, world, events):
    user = _user("ag_order")
    _object_grant(user, routes, "guardian", "view", world.penguin)
    events.clear()
    assert _client(user).get(_guardian_url(routes, "guardian", "list", world.penguin)).status_code == 200
    parent = ("queryset", routes.parents["guardian"].name)
    gate = ("object_perm", "app.view_publisher")
    child = ("queryset", routes.guardian["guardian"].name)
    assert events.index(parent) < events.index(gate) < events.index(child)
    assert events.count(parent) == 1
    assert ("model_perm", "app.view_publisher") not in events  # strict: no model fallback evaluated


@pytest.mark.django_db
def test_nested_guardian_create_needs_parent_change_and_no_child_add(routes, world):
    viewer = _user("ag_create_viewer")
    _object_grant(viewer, routes, "guardian", "view", world.penguin)
    create = _guardian_url(routes, "guardian", "create", world.penguin)
    assert _client(viewer).get(create).status_code == 403
    editor = _user("ag_create_editor")  # no Book add permission of any kind
    _object_grant(editor, routes, "guardian", "change", world.penguin)
    client = _client(editor)
    assert client.get(create).status_code == 200
    response = client.post(create, {"title": "Created"})
    assert response.status_code == 302, response.content[:300]
    assert Book.objects.get(title="Created").publisher_id == world.penguin.pk


@pytest.mark.django_db
@pytest.mark.parametrize("enabled", [True, False])
def test_nested_guardian_create_state_receives_the_resolved_parent(routes, world, monkeypatch, enabled):
    seen = []
    resolved = []
    from crud_views.lib import ancestors

    original = ancestors._resolve_ancestor

    def resolve_spy(view, edge, ancestor, outer):
        obj = original(view, edge, ancestor, outer)
        resolved.append(obj)
        return obj

    def state(cls, user, obj=None):
        seen.append(obj)
        return enabled

    monkeypatch.setattr(ancestors, "_resolve_ancestor", resolve_spy)
    monkeypatch.setattr(routes.views["guardian"].Create, "cv_action_enabled", classmethod(state))
    user = _user(f"ag_create_state_{int(enabled)}")
    _object_grant(user, routes, "guardian", "change", world.penguin)
    response = _client(user).get(_guardian_url(routes, "guardian", "create", world.penguin))
    assert response.status_code == (200 if enabled else 403)
    assert len(resolved) == 1
    assert seen and seen[0] is resolved[0]  # the state hook sees the guard's own parent object


@pytest.mark.django_db
def test_ancestor_fallback_does_not_widen_the_strict_helper(routes, world):
    user = _user("ag_helper_model", (Publisher, "view"))
    assert list(routes.parents["fallback"].get_objects_for_user(user, "view")) == []
    assert routes.parents["fallback"].ancestor_policy.accept_global_perms is True


@pytest.mark.django_db
def test_ancestor_checker_is_scoped_to_the_request(routes, world):
    # a grant revoked between requests takes effect on the next request (no cross-request checker reuse)
    user = _user("ag_revoke")
    _object_grant(user, routes, "guardian", "view", world.penguin)
    client = _client(user)
    assert client.get(_plain_url(routes, "guardian", world.penguin)).status_code == 200
    from guardian.shortcuts import remove_perm

    remove_perm(routes.parents["guardian"].permissions["view"], user, world.penguin)
    assert client.get(_plain_url(routes, "guardian", world.penguin)).status_code == 403


def test_guardian_viewset_class_default_provider_is_guardian():
    from crud_views_guardian.lib.viewset import GuardianViewSet

    assert GuardianViewSet._ancestor_provider == "guardian"
    assert ViewSet._ancestor_provider == "model"


@pytest.mark.django_db
def test_explicit_model_provider_on_guardian_ancestor_uses_model_permissions(world):
    from crud_views.lib.views import ListView
    from crud_views_guardian.lib.viewset import GuardianViewSet

    def build(sfx):
        parent = GuardianViewSet(model=Publisher, name=f"agmp{sfx}", ancestor_policy=AncestorPolicy(provider="model"))
        child = ViewSet(model=Book, name=f"agmc{sfx}", parent=ParentViewSet(name=parent.name, attribute="publisher"))
        type("PlainList", (ListView,), {"cv_viewset": child, "cv_list_actions": [], "cv_context_actions": []})
        return SimpleNamespace(parent=parent, child=child), [parent, child]

    with isolated_routes(build) as ns:
        url = _url(ns.child, "list", **{f"{ns.parent.name}_pk": world.penguin.pk})
        object_only = _user("ag_mp_object")
        assign_perm("app.view_publisher", object_only, world.penguin)
        assert _client(object_only).get(url).status_code == 403
        model_only = _user("ag_mp_model", (Publisher, "view"))
        assert _client(model_only).get(url).status_code == 200
