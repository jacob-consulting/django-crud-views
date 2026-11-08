"""
Phase 06.18 plan 04 — early actor admission before any ancestor lookup.

The request order for a nested endpoint is: static validation → actor admission → interleaved ancestor
lookups/gates → the endpoint's remaining local work. This module proves the actor stage on real URLs:

* Protected ancestry (at least one selected ancestor gate): anonymous actors get the requested endpoint's
  anonymous response (login redirect by default, also for plain views; Guardian's configured 403/404 is kept),
  authenticated inactive actors — superusers included — get 403. Nothing is looked up first.
* All-none ancestry (every ancestor provider ``"none"``): the endpoint's own early admission decides, never an
  inferred login requirement. A core permission-required endpoint asks only its model permission (so a backend
  that grants anonymous actors still admits them); a plain endpoint admits everybody; Guardian keeps its
  explicit actor rules. An early denial is identical for a valid, missing and mismatched parent and performs no
  ancestor lookup; an admitted actor reaches relationship validation (404 on a missing or mismatched parent).
* The state-loading ``has_permission()`` of core permission-required views (child object, action state) is never
  used for actor admission: an active actor's local permission runs only after ancestry succeeded.
* The resolved ancestry is request/view-instance local: nothing carries between requests or actors.

Every fixture builds fresh, uniquely named ViewSets behind a temporary ROOT_URLCONF and restores the registry
and caches (``isolated_routes``).
"""

from __future__ import annotations

from types import SimpleNamespace
from urllib.parse import parse_qs

import pytest
from django.conf import settings
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import AnonymousUser, PermissionsMixin
from django.test import RequestFactory, override_settings
from guardian.shortcuts import assign_perm

from crud_views.lib.view import CrudViewPermissionRequiredMixin
from crud_views.lib.viewset import AncestorPolicy, ParentViewSet, ViewSet
from tests.test1.app.models import Book, Publisher
from tests.test1.test_ancestor_authorization import _client, _url, _user, isolated_routes

ALLOW_INACTIVE = "django.contrib.auth.backends.AllowAllUsersModelBackend"
MODEL_BACKEND = "django.contrib.auth.backends.ModelBackend"
GUARDIAN_BACKEND = "guardian.backends.ObjectPermissionBackend"
ANONYMOUS_READER = "tests.test1.test_ancestor_actors.AnonymousBookReaderBackend"


class AnonymousBookReaderBackend(BaseBackend):
    """A supported backend that admits anonymous actors to the Book model permission (view only)."""

    def has_perm(self, user_obj, perm, obj=None):
        return not user_obj.is_authenticated and perm == "app.view_book"


# ── routes ───────────────────────────────────────────────────────────────────

PARENT_KINDS = ("protected", "none")
CHILD_KINDS = ("plain", "core", "guardian", "gobject")


@pytest.fixture
def routes():
    """A protected core Publisher (model provider) and an unprotected one (provider "none"), each with four
    nested Book ViewSets: plain (ListView/DetailView, no local gate), core permission-required, the shipped
    Guardian composition (parent + object/queryset mixins) and a standalone Guardian object-permission
    composition (no parent mixin)."""
    from crud_views.lib.views import DetailView, DetailViewPermissionRequired, ListView, ListViewPermissionRequired
    from crud_views_guardian.lib.mixins import GuardianObjectPermissionMixin
    from crud_views_guardian.lib.views import (
        GuardianDetailViewPermissionRequired,
        GuardianListViewPermissionRequired,
    )
    from crud_views_guardian.lib.viewset import GuardianViewSet

    bases = {
        "plain": (ListView, DetailView, ViewSet),
        "core": (ListViewPermissionRequired, DetailViewPermissionRequired, ViewSet),
        "guardian": (GuardianListViewPermissionRequired, GuardianDetailViewPermissionRequired, GuardianViewSet),
        "gobject": (None, None, ViewSet),
    }

    def build(sfx):
        parents = {
            "protected": ViewSet(model=Publisher, name=f"aapub{sfx}"),
            "none": ViewSet(model=Publisher, name=f"aanone{sfx}", ancestor_policy=AncestorPolicy(provider="none")),
        }
        ns = SimpleNamespace(parents=parents, children={}, views={})
        for pkind, parent in parents.items():
            for ckind, (list_base, detail_base, vs_class) in bases.items():
                child = vs_class(
                    model=Book,
                    name=f"aa{ckind}{pkind}{sfx}",
                    parent=ParentViewSet(name=parent.name, attribute="publisher"),
                )
                common = {"cv_viewset": child, "cv_context_actions": []}
                if ckind == "gobject":
                    detail = type(
                        "GObjectDetail", (GuardianObjectPermissionMixin, DetailViewPermissionRequired), dict(common)
                    )
                    listing = None
                else:
                    listing = type("List", (list_base,), {**common, "cv_list_actions": []})
                    detail = type("Detail", (detail_base,), dict(common))
                ns.children[(pkind, ckind)] = child
                ns.views[(pkind, ckind)] = SimpleNamespace(List=listing, Detail=detail)
        return ns, [*parents.values(), *ns.children.values()]

    with isolated_routes(build) as ns:
        yield ns


@pytest.fixture
def world(db):
    penguin = Publisher.objects.create(name="Penguin")
    other = Publisher.objects.create(name="Other")
    book = Book.objects.create(title="Hitchhiker", publisher=penguin)
    foreign = Book.objects.create(title="Foreign", publisher=other)
    return SimpleNamespace(penguin=penguin, other=other, book=book, foreign=foreign)


def _detail_url(routes, pkind, ckind, publisher_pk, book_pk):
    child = routes.children[(pkind, ckind)]
    return _url(child, "detail", **{f"{routes.parents[pkind].name}_pk": publisher_pk, "pk": book_pk})


def _list_url(routes, pkind, ckind, publisher_pk):
    child = routes.children[(pkind, ckind)]
    return _url(child, "list", **{f"{routes.parents[pkind].name}_pk": publisher_pk})


def _three_targets(routes, pkind, ckind, world):
    """The same endpoint with a valid, a missing and a mismatched parent."""
    return {
        "valid": _detail_url(routes, pkind, ckind, world.penguin.pk, world.book.pk),
        "missing": _detail_url(routes, pkind, ckind, 987654, world.book.pk),
        "mismatched": _detail_url(routes, pkind, ckind, world.penguin.pk, world.foreign.pk),
    }


@pytest.fixture
def events(monkeypatch):
    """Ordered framework events: ViewSet querysets, model permission checks (authenticated and anonymous actors)
    and the state-loading local
    ``has_permission`` / ``cv_get_action_object`` of core permission-required views."""
    recorded: list[tuple[str, str]] = []
    original_queryset = ViewSet.get_queryset
    original_has_perm = PermissionsMixin.has_perm
    original_local = CrudViewPermissionRequiredMixin.has_permission
    original_anonymous = AnonymousUser.has_perm

    def queryset_spy(self, view):
        recorded.append(("queryset", self.name))
        return original_queryset(self, view)

    def has_perm_spy(self, perm, obj=None):
        recorded.append(("model_perm", perm))
        return original_has_perm(self, perm, obj)

    def anonymous_spy(self, perm, obj=None):
        recorded.append(("model_perm", perm))
        return original_anonymous(self, perm, obj)

    def local_spy(self):
        recorded.append(("local_has_permission", self.cv_viewset.name))
        return original_local(self)

    monkeypatch.setattr(ViewSet, "get_queryset", queryset_spy)
    monkeypatch.setattr(PermissionsMixin, "has_perm", has_perm_spy)
    monkeypatch.setattr(AnonymousUser, "has_perm", anonymous_spy)
    monkeypatch.setattr(CrudViewPermissionRequiredMixin, "has_permission", local_spy)
    return recorded


def _querysets(events) -> list:
    return [event for event in events if event[0] == "queryset"]


def _login_target(response) -> str:
    assert response.status_code == 302, response.status_code
    target, _, query = response["Location"].partition("?")
    assert target == settings.LOGIN_URL
    return query


# ── protected ancestry: anonymous actors ─────────────────────────────────────


@pytest.mark.django_db
@pytest.mark.parametrize("ckind", ["plain", "core"])
@pytest.mark.parametrize("target", ["valid", "missing", "mismatched"])
def test_protected_anonymous_gets_login_redirect_before_lookup(routes, world, events, ckind, target):
    url = _three_targets(routes, "protected", ckind, world)[target]
    response = _client(None).get(url)
    assert "next=" in _login_target(response)
    assert events == []


@pytest.mark.django_db
def test_protected_anonymous_plain_list_redirects_without_access_mixin(routes, world, events):
    response = _client(None).get(_list_url(routes, "protected", "plain", 987654))
    _login_target(response)
    assert events == []


@pytest.mark.django_db
def test_protected_ancestry_denies_anonymous_even_when_a_backend_admits_them(routes, world, events):
    # a backend that admits anonymous actors locally cannot waive the protected ancestor's actor rule
    with override_settings(AUTHENTICATION_BACKENDS=[MODEL_BACKEND, ANONYMOUS_READER]):
        response = _client(None).get(_three_targets(routes, "protected", "core", world)["valid"])
    _login_target(response)
    assert events == []


@pytest.mark.django_db
@pytest.mark.parametrize("ckind", ["guardian", "gobject"])
@pytest.mark.parametrize("behavior,status", [("redirect", 302), ("403", 403), ("404", 404)])
def test_protected_anonymous_keeps_configured_guardian_response(
    routes, world, events, monkeypatch, ckind, behavior, status
):
    monkeypatch.setattr(routes.views[("protected", ckind)].Detail, "cv_guardian_anonymous_behavior", behavior)
    for url in _three_targets(routes, "protected", ckind, world).values():
        response = _client(None).get(url)
        assert response.status_code == status
        if status == 302:
            _login_target(response)
    assert _querysets(events) == []


# ── protected ancestry: inactive actors ──────────────────────────────────────


@pytest.mark.django_db
@pytest.mark.parametrize("ckind", CHILD_KINDS)
@pytest.mark.parametrize("superuser", [False, True], ids=["user", "superuser"])
def test_protected_inactive_actor_is_403_before_lookup(routes, world, events, ckind, superuser):
    user = _user(f"aa_inactive_{ckind}_{int(superuser)}", (Publisher, "view"), (Book, "view"), superuser=superuser)
    assign_perm(routes.children[("protected", ckind)].permissions["view"], user, world.book)
    user.is_active = False
    user.save()
    with override_settings(AUTHENTICATION_BACKENDS=[ALLOW_INACTIVE, GUARDIAN_BACKEND]):
        client = _client(None)
        client.force_login(user, backend=ALLOW_INACTIVE)
        for url in _three_targets(routes, "protected", ckind, world).values():
            assert client.get(url).status_code == 403
    assert _querysets(events) == []
    assert ("local_has_permission", routes.children[("protected", ckind)].name) not in events


# ── all-none ancestry: early denial is identical for valid / missing / mismatched ──


@pytest.mark.django_db
def test_all_none_core_anonymous_denial_is_identical_without_lookup(routes, world, events):
    for target, url in _three_targets(routes, "none", "core", world).items():
        response = _client(None).get(url)
        assert parse_qs(_login_target(response)) == {"next": [url]}, target
    assert _querysets(events) == []
    # admission asked the endpoint's model permission only, never the state-loading local has_permission
    assert {event for event in events if event[0] == "local_has_permission"} == set()
    assert ("model_perm", "app.view_book") in events


@pytest.mark.django_db
@pytest.mark.parametrize("superuser", [False, True], ids=["user", "superuser"])
def test_all_none_core_inactive_denial_is_identical_without_lookup(routes, world, events, superuser):
    user = _user(f"aa_none_inactive_{int(superuser)}", (Book, "view"), superuser=superuser)
    user.is_active = False
    user.save()
    with override_settings(AUTHENTICATION_BACKENDS=[ALLOW_INACTIVE]):
        client = _client(None)
        client.force_login(user, backend=ALLOW_INACTIVE)
        for url in _three_targets(routes, "none", "core", world).values():
            assert client.get(url).status_code == 403
    assert _querysets(events) == []
    assert [event for event in events if event[0] == "local_has_permission"] == []


@pytest.mark.django_db
@pytest.mark.parametrize("behavior,status", [("redirect", 302), ("403", 403), ("404", 404)])
@pytest.mark.parametrize("ckind", ["guardian", "gobject"])
def test_all_none_guardian_keeps_its_explicit_actor_rules(routes, world, events, monkeypatch, ckind, behavior, status):
    monkeypatch.setattr(routes.views[("none", ckind)].Detail, "cv_guardian_anonymous_behavior", behavior)
    responses = [_client(None).get(url) for url in _three_targets(routes, "none", ckind, world).values()]
    assert [response.status_code for response in responses] == [status] * 3
    assert _querysets(events) == []


@pytest.mark.django_db
@pytest.mark.parametrize("ckind", ["guardian", "gobject"])
def test_all_none_guardian_inactive_superuser_is_403_without_lookup(routes, world, events, ckind):
    user = _user(f"aa_none_ginactive_{ckind}", superuser=True)
    user.is_active = False
    user.save()
    with override_settings(AUTHENTICATION_BACKENDS=[ALLOW_INACTIVE, GUARDIAN_BACKEND]):
        client = _client(None)
        client.force_login(user, backend=ALLOW_INACTIVE)
        for url in _three_targets(routes, "none", ckind, world).values():
            assert client.get(url).status_code == 403
    assert _querysets(events) == []


# ── all-none ancestry: admitted actors reach relationship validation ─────────


@pytest.mark.django_db
def test_all_none_plain_endpoint_stays_public(routes, world, events):
    targets = _three_targets(routes, "none", "plain", world)
    assert _client(None).get(targets["valid"]).status_code == 200
    assert _client(None).get(targets["missing"]).status_code == 404
    assert _client(None).get(targets["mismatched"]).status_code == 404
    assert ("queryset", routes.parents["none"].name) in events
    assert _client(None).get(_list_url(routes, "none", "plain", world.penguin.pk)).status_code == 200


@pytest.mark.django_db
def test_all_none_anonymous_granting_backend_admits_then_validates_ancestry_first(routes, world, events):
    targets = _three_targets(routes, "none", "core", world)
    parent, child = routes.parents["none"].name, routes.children[("none", "core")].name
    with override_settings(AUTHENTICATION_BACKENDS=[MODEL_BACKEND, ANONYMOUS_READER]):
        assert _client(None).get(targets["valid"]).status_code == 200
        events.clear()
        assert _client(None).get(targets["mismatched"]).status_code == 404
        # the ancestor is resolved (relationship validated) before the local gate and the child lookup
        assert events.index(("queryset", parent)) < events.index(("local_has_permission", child))
        assert events.index(("queryset", parent)) < events.index(("queryset", child))
        events.clear()
        assert _client(None).get(targets["missing"]).status_code == 404
    assert ("queryset", child) not in events
    assert ("local_has_permission", child) not in events


@pytest.mark.django_db
def test_all_none_active_actor_without_local_permission_reaches_relationships_first(routes, world, events):
    # an active actor is admitted; its missing model permission is a local gate that runs after ancestry
    user = _user("aa_none_active_no_perm")
    targets = _three_targets(routes, "none", "core", world)
    client = _client(user)
    assert client.get(targets["missing"]).status_code == 404
    assert client.get(targets["mismatched"]).status_code == 403  # parent exists; the child lookup never ran
    assert ("queryset", routes.children[("none", "core")].name) not in events


# ── active actors: local permission and state only after ancestry ────────────


@pytest.mark.django_db
def test_core_local_denial_runs_after_the_ancestor_gate(routes, world, events):
    parent, child = routes.parents["protected"].name, routes.children[("protected", "core")].name
    user = _user("aa_parent_only", (Publisher, "view"))
    response = _client(user).get(_three_targets(routes, "protected", "core", world)["valid"])
    assert response.status_code == 403
    gate = events.index(("model_perm", "app.view_publisher"))
    assert events.index(("queryset", parent)) < gate < events.index(("local_has_permission", child))
    assert ("queryset", child) not in events


@pytest.mark.django_db
def test_core_ancestor_denial_prevents_child_lookup_and_local_state(routes, world, events):
    child = routes.children[("protected", "core")].name
    user = _user("aa_child_only", (Book, "view"))
    response = _client(user).get(_three_targets(routes, "protected", "core", world)["valid"])
    assert response.status_code == 403
    assert ("queryset", child) not in events
    assert ("local_has_permission", child) not in events


@pytest.mark.django_db
def test_core_missing_parent_is_404_before_the_local_gate(routes, world, events):
    user = _user("aa_no_child_perm", (Publisher, "view"))
    response = _client(user).get(_three_targets(routes, "protected", "core", world)["missing"])
    assert response.status_code == 404
    assert ("local_has_permission", routes.children[("protected", "core")].name) not in events


@pytest.mark.django_db
def test_core_local_success_after_ancestry(routes, world, events):
    parent, child = routes.parents["protected"].name, routes.children[("protected", "core")].name
    user = _user("aa_both", (Publisher, "view"), (Book, "view"))
    response = _client(user).get(_three_targets(routes, "protected", "core", world)["valid"])
    assert response.status_code == 200
    assert response.context["object"] == world.book
    assert events.index(("queryset", parent)) < events.index(("local_has_permission", child))
    assert events.index(("local_has_permission", child)) < events.index(("queryset", child))
    # the mismatched child is a 404 from the scoped child lookup, after both gates passed
    assert _client(user).get(_three_targets(routes, "protected", "core", world)["mismatched"]).status_code == 404


# ── request-local state ──────────────────────────────────────────────────────


@pytest.mark.django_db
def test_ancestry_state_does_not_carry_between_requests_actors_or_instances(routes, world):
    reader = _user("aa_reader", (Publisher, "view"), (Book, "view"))
    stranger = _user("aa_stranger", (Book, "view"))
    view_class = routes.views[("protected", "core")].Detail
    url = _three_targets(routes, "protected", "core", world)["valid"]
    kwargs = {f"{routes.parents['protected'].name}_pk": world.penguin.pk, "pk": world.book.pk}
    factory = RequestFactory()

    instances = []

    def run(user):
        request = factory.get(url)
        request.user = user
        view = view_class(**{})
        view.setup(request, **kwargs)
        instances.append(view)
        try:
            return view.dispatch(request, **kwargs).status_code
        except Exception as exc:  # PermissionDenied surfaces from dispatch
            return type(exc).__name__

    assert run(reader) == 200
    assert run(stranger) == "PermissionDenied"
    assert run(AnonymousUser()) == 302
    assert run(reader) == 200
    assert instances[0]._cv_ancestor_state.parent == world.penguin
    assert getattr(instances[1], "_cv_ancestor_state", None) is None
    assert getattr(instances[2], "_cv_ancestor_state", None) is None
    assert instances[3]._cv_ancestor_state is not instances[0]._cv_ancestor_state
    assert not hasattr(view_class, "_cv_ancestor_state")
    # and through the client: a granted request does not open the next actor's request
    assert _client(reader).get(url).status_code == 200
    assert _client(stranger).get(url).status_code == 403


@pytest.mark.django_db
def test_backend_failure_during_admission_is_not_success(routes, world, monkeypatch):
    # a backend error while deciding all-none admission propagates; it never becomes an admitted request
    def broken(self, perm, obj=None):
        raise RuntimeError("backend down")

    monkeypatch.setattr(AnonymousUser, "has_perm", broken)
    client = _client(None)
    client.raise_request_exception = True
    with pytest.raises(RuntimeError, match="backend down"):
        client.get(_three_targets(routes, "none", "core", world)["valid"])


# ── manage: actual settings/group admission, independent local group gate ────


def _manage_url(routes, pkind, publisher_pk, ckind="plain"):
    return _url(routes.children[(pkind, ckind)], "manage", **{f"{routes.parents[pkind].name}_pk": publisher_pk})


@pytest.fixture
def manage_events(monkeypatch, events):
    from crud_views.lib.views.manage import ManageView

    original = ManageView.has_permission

    def gate_spy(self):
        events.append(("manage_gate", self.cv_viewset.name))
        return original(self)

    monkeypatch.setattr(ManageView, "has_permission", gate_spy)
    return events


def _manage_mode(monkeypatch, mode):
    from crud_views.lib.settings import crud_views_settings

    monkeypatch.setattr(crud_views_settings, "manage_views_enabled", mode)


def _manage_member(username, *perms):
    from django.contrib.auth.models import Group

    from crud_views.lib.settings import crud_views_settings

    user = _user(username, *perms)
    user.groups.add(Group.objects.get_or_create(name=crud_views_settings.manage_group)[0])
    return user


@pytest.mark.django_db
@pytest.mark.parametrize("ckind", ["plain", "guardian"])
def test_protected_public_manage_still_denies_anonymous_and_inactive(routes, world, manage_events, monkeypatch, ckind):
    _manage_mode(monkeypatch, "yes")
    for publisher_pk in (world.penguin.pk, 987654):
        _login_target(_client(None).get(_manage_url(routes, "protected", publisher_pk, ckind)))
    inactive = _user(f"aa_mg_inactive_{ckind}", superuser=True)
    inactive.is_active = False
    inactive.save()
    with override_settings(AUTHENTICATION_BACKENDS=[ALLOW_INACTIVE]):
        client = _client(None)
        client.force_login(inactive, backend=ALLOW_INACTIVE)
        assert client.get(_manage_url(routes, "protected", world.penguin.pk, ckind)).status_code == 403
    assert _querysets(manage_events) == []


@pytest.mark.django_db
def test_all_none_public_manage_stays_public(routes, world, manage_events, monkeypatch):
    _manage_mode(monkeypatch, "yes")
    assert _client(None).get(_manage_url(routes, "none", world.penguin.pk)).status_code == 200
    assert _client(None).get(_manage_url(routes, "none", 987654)).status_code == 404  # relationships still apply


@pytest.mark.django_db
def test_all_none_group_manage_denies_anonymous_identically_without_lookup(routes, world, manage_events, monkeypatch):
    _manage_mode(monkeypatch, "debug_only")  # DEBUG is off under pytest: the group gate applies
    for publisher_pk in (world.penguin.pk, 987654):
        _login_target(_client(None).get(_manage_url(routes, "none", publisher_pk)))
    assert _querysets(manage_events) == []


@pytest.mark.django_db
def test_all_none_group_manage_gate_runs_after_relationships(routes, world, manage_events, monkeypatch):
    _manage_mode(monkeypatch, "debug_only")
    stranger = _user("aa_mg_stranger")
    assert _client(stranger).get(_manage_url(routes, "none", 987654)).status_code == 404
    assert ("manage_gate", routes.children[("none", "plain")].name) not in manage_events
    assert _client(stranger).get(_manage_url(routes, "none", world.penguin.pk)).status_code == 403
    assert manage_events.index(("queryset", routes.parents["none"].name)) < manage_events.index(
        ("manage_gate", routes.children[("none", "plain")].name)
    )
    assert _client(_manage_member("aa_mg_member")).get(_manage_url(routes, "none", world.penguin.pk)).status_code == 200


@pytest.mark.django_db
def test_all_none_group_manage_keeps_admitting_an_inactive_member(routes, world, monkeypatch):
    # the existing manage gate never checked is_active; all-none ancestry adds no inactivity restriction
    _manage_mode(monkeypatch, "debug_only")
    member = _manage_member("aa_mg_inactive_member")
    member.is_active = False
    member.save()
    with override_settings(AUTHENTICATION_BACKENDS=[ALLOW_INACTIVE]):
        client = _client(None)
        client.force_login(member, backend=ALLOW_INACTIVE)
        assert client.get(_manage_url(routes, "none", world.penguin.pk)).status_code == 200


@pytest.mark.django_db
@pytest.mark.parametrize("ckind", ["plain", "guardian"])
def test_protected_manage_group_membership_does_not_bypass_ancestry(routes, world, manage_events, monkeypatch, ckind):
    _manage_mode(monkeypatch, "debug_only")
    member = _manage_member(f"aa_mg_noparent_{ckind}")
    assert _client(member).get(_manage_url(routes, "protected", world.penguin.pk, ckind)).status_code == 403
    assert [event for event in manage_events if event[0] == "manage_gate"] == []
    reader = _manage_member(f"aa_mg_reader_{ckind}", (Publisher, "view"))
    assert _client(reader).get(_manage_url(routes, "protected", world.penguin.pk, ckind)).status_code == 200
    # ancestry passes, the group gate still denies a non-member
    outsider = _user(f"aa_mg_outsider_{ckind}", (Publisher, "view"))
    assert _client(outsider).get(_manage_url(routes, "protected", world.penguin.pk, ckind)).status_code == 403


# ── static validation precedes actor admission ───────────────────────────────


@pytest.fixture
def undeclared_custom():
    """A nested custom ActionView without its exact ancestor_policy.actions entry, plain and permission-required."""
    from crud_views.lib.views import ActionView, ActionViewPermissionRequired

    def build(sfx):
        pub = ViewSet(model=Publisher, name=f"aaspub{sfx}")
        child = ViewSet(model=Book, name=f"aasbook{sfx}", parent=ParentViewSet(name=pub.name, attribute="publisher"))
        for key, base in (("act", ActionView), ("pact", ActionViewPermissionRequired)):
            type(f"Undeclared{key}", (base,), {"cv_viewset": child, "cv_key": key, "cv_path": key})
        return SimpleNamespace(pub=pub, child=child), [pub, child]

    with isolated_routes(build) as ns:
        yield ns


@pytest.mark.django_db
@pytest.mark.parametrize("key", ["act", "pact"])
def test_static_configuration_error_precedes_actor_admission(undeclared_custom, world, events, key):
    from django.core.exceptions import ImproperlyConfigured

    ns = undeclared_custom
    url = _url(ns.child, key, **{f"{ns.pub.name}_pk": 987654, "pk": world.book.pk})
    with pytest.raises(ImproperlyConfigured, match=r"ancestor_policy\.actions\["):
        _client(None).post(url)  # anonymous: no login redirect hides the configuration error
    assert events == []
