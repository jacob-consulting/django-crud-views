"""Navbar admission consumes existing policy; real destination requests remain authoritative."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from django.contrib.auth.models import AnonymousUser, Permission
from django.core.exceptions import ImproperlyConfigured
from django.db import router
from django.template import Context, Template
from django.test import Client, RequestFactory
from django.urls import reverse

from crud_views.lib.ancestor_policy import AncestorPermissions, AncestorPolicy
from crud_views.lib.navbar import CrudViewNavBarMixin, NavBar, NavItem
from crud_views.lib.views import (
    CreateViewPermissionRequired,
    DetailView,
    DetailViewPermissionRequired,
    ListViewPermissionRequired,
)
from crud_views.lib.viewset import ParentViewSet, ViewSet
from crud_views_guardian.lib.views import (
    GuardianCreateViewPermissionRequired,
    GuardianDetailViewPermissionRequired,
    GuardianListViewPermissionRequired,
)
from crud_views_guardian.lib.viewset import GuardianViewSet
from tests.lib.helper.guardian import user_guardian_object_perm
from tests.test1.app.models import Book, Publisher
from tests.test1.test_guardian_child_link_visibility import parent_spy
from tests.test1.test_navbar import navbar_routes, section_objects, section_routes, section_url


def permission_routes(sfx, *, composition="plain", key="list"):
    """One public host, one protected owner item, one real nested destination."""
    guardian_parent = composition != "plain"
    guardian_child = composition == "guardian"
    owner = (GuardianViewSet if guardian_parent else ViewSet)(model=Publisher, name=f"permowner{sfx}")
    child = (GuardianViewSet if guardian_child else ViewSet)(
        model=Book, name=f"permchild{sfx}", parent=ParentViewSet(name=owner.name, attribute="publisher")
    )
    bar = NavBar(viewset=owner.name, items=[NavItem(key="detail", label="Details"), NavItem(child=child.name, key=key)])
    common = {"cv_context_actions": [], "cv_list_actions": [], "cv_extends_template": "navbar/base.html"}
    host = type(
        "Host",
        (CrudViewNavBarMixin, DetailView),
        {**common, "cv_viewset": owner, "cv_key": "host", "cv_path": "host", "cv_navbar": bar},
    )
    detail = type(
        "Details",
        (GuardianDetailViewPermissionRequired if guardian_parent else DetailViewPermissionRequired,),
        {**common, "cv_viewset": owner},
    )
    base = (
        (GuardianListViewPermissionRequired if guardian_child else ListViewPermissionRequired)
        if key == "list"
        else (GuardianCreateViewPermissionRequired if guardian_child else CreateViewPermissionRequired)
    )
    target = type("Target", (base,), {**common, "cv_viewset": child, "fields": ["title"]})
    return SimpleNamespace(owner=owner, child=child, bar=bar, host=host, detail=detail, target=target), [owner, child]


def grant(ns, actor, owner, *, owner_access=True, child_access=True):
    if owner_access:
        if isinstance(ns.owner, GuardianViewSet):
            for key in ("view", "change"):
                user_guardian_object_perm(actor, ns.owner, key, owner)
        else:
            actor.user_permissions.add(*Permission.objects.filter(codename__in=["view_publisher", "change_publisher"]))
    if child_access:
        actor.user_permissions.add(*Permission.objects.filter(codename__in=["view_book", "add_book"]))


def host_response(ns, actor, owner):
    client = Client()
    if actor.is_authenticated:
        client.force_login(actor)
    return client, client.get(reverse(ns.owner.get_router_name("host"), kwargs={"pk": owner.pk}))


def lazy_host(ns, actor, owner):
    view = ns.host()
    request = RequestFactory().get("/")
    request.user = actor
    view.setup(request, pk=owner.pk)
    view.object = owner
    return view, view.get_context_data()


TAG = "{% load crud_views %}{% cv_navbar %}"


@pytest.mark.django_db
@pytest.mark.parametrize("composition", ["plain", "guardian", "mixed"])
@pytest.mark.parametrize("key", ["list", "create"])
@pytest.mark.parametrize("outcome", ["allowed", "denied", "disabled"])
def test_rendered_admission_order_and_exact_owner(composition, key, outcome, django_user_model, monkeypatch):
    with navbar_routes(lambda sfx: permission_routes(sfx, composition=composition, key=key)) as ns:
        owner = Publisher.objects.create(name="Navigation owner")
        actor = django_user_model.objects.create_user(username="reader")
        grant(ns, actor, owner, owner_access=outcome != "denied")
        events = []
        original = ns.target._cv_child_link_has_access
        access = Mock(side_effect=lambda *args: (events.append("access"), original(*args))[1])
        state = Mock(side_effect=lambda *args: (events.append("state"), outcome != "disabled")[1])
        monkeypatch.setattr(ns.target, "_cv_child_link_has_access", access)
        monkeypatch.setattr(ns.target, "_cv_action_enabled_for_rendering", state)
        gate = parent_spy(monkeypatch, ns.target)
        own = Mock(wraps=ns.detail.cv_has_access)
        monkeypatch.setattr(ns.detail, "cv_has_access", own)
        extras = Mock(wraps=ns.target.cv_get_url_extra_kwargs)
        monkeypatch.setattr(ns.target, "cv_get_url_extra_kwargs", extras)
        client, response = host_response(ns, actor, owner)
        assert response.status_code == 200
        view = response.context["view"]
        request_actor = view.request.user
        original_owner = view.object
        access.assert_called_once_with(request_actor, original_owner)
        own.assert_called_once_with(request_actor, original_owner)
        gate.assert_called_once_with(request_actor, original_owner)
        assert access.call_args.args[1] is original_owner
        if outcome == "denied":
            state.assert_not_called()
            extras.assert_not_called()
            assert events == ["access"]
            assert not response.context["cv_navbar"]
        else:
            state.assert_called_once_with(request_actor, original_owner, view)
            assert state.call_args.args[1] is original_owner
            assert events == ["access", "state"]
            items = response.context["cv_navbar"]["items"]
            assert len(items) == (2 if outcome == "allowed" else 1)
            assert extras.call_count == (outcome == "allowed")
            if outcome == "allowed":
                destination = client.get(items[-1]["url"])
                assert destination.status_code == 200
                if key == "list":
                    assert list(destination.context["object_list"]) == []


@pytest.mark.django_db
@pytest.mark.parametrize("composition", ["plain", "guardian", "mixed"])
@pytest.mark.parametrize("disabled", ["detail", "create"])
def test_state_hidden_link_and_direct_request_403(composition, disabled, django_user_model, monkeypatch):
    with navbar_routes(lambda sfx: permission_routes(sfx, composition=composition, key="create")) as ns:
        owner = Publisher.objects.create(name="Locked")
        actor = django_user_model.objects.create_user(username="state")
        grant(ns, actor, owner)
        target = ns.detail if disabled == "detail" else ns.target
        state = Mock(return_value=False)
        monkeypatch.setattr(target, "cv_action_enabled", state)
        client, response = host_response(ns, actor, owner)
        assert response.status_code == 200
        state.assert_called_once_with(response.context["view"].request.user, response.context["view"].object)
        url = reverse(
            target.cv_viewset.get_router_name(disabled),
            kwargs={"pk" if disabled == "detail" else ns.child.parent.get_pk_name(): owner.pk},
        )
        assert url not in [item["url"] for item in response.context["cv_navbar"]["items"]]
        assert client.get(url).status_code == 403


@pytest.mark.django_db
@pytest.mark.parametrize("error", ["mapping", "operation", "database"])
@pytest.mark.parametrize("allowed", [False, True])
def test_reached_policy_errors_propagate(error, allowed, django_user_model, monkeypatch):
    from crud_views.lib.views import ActionView, ListView

    def build(sfx):
        ns, routed = permission_routes(sfx)
        # A GET-capable action with no operation intentionally reaches the existing policy diagnostic.
        base = ActionView if error == "operation" else ListView
        ns.target = type(
            "InvalidTarget",
            (base,),
            {"cv_key": "invalid", "cv_object": False, "cv_viewset": ns.child, "get": lambda self, request: None},
        )
        ns.bar.items = [NavItem(child=ns.child.name, key="invalid")]
        return ns, routed

    with navbar_routes(build) as ns:
        actor = django_user_model.objects.create_user(username="errors")
        owner = Publisher.objects.create(name="Owner")
        if error == "mapping":
            ns.child.ancestor_policy = AncestorPolicy(read=AncestorPermissions(nearest="undeclared", higher="view"))
        elif error == "database":

            class AuthRouter:
                def db_for_read(self, model, **hints):
                    return "shard" if model is Permission else None

            monkeypatch.setattr(router, "routers", [AuthRouter()])
        monkeypatch.setattr(ns.target, "cv_has_access", Mock(return_value=allowed))
        state = Mock(side_effect=AssertionError("state ran after denial/error"))
        monkeypatch.setattr(ns.target, "_cv_action_enabled_for_rendering", state)
        _, data = lazy_host(ns, actor, owner)
        if allowed:
            with pytest.raises(
                ImproperlyConfigured,
                match={"mapping": "undeclared", "operation": "operation|actions", "database": "shard"}[error],
            ):
                Template(TAG).render(Context(data))
        else:
            assert Template(TAG).render(Context(data)) == ""
        state.assert_not_called()


@pytest.mark.django_db
@pytest.mark.parametrize("composition", ["plain", "guardian", "mixed"])
@pytest.mark.parametrize("kind", ["anonymous", "inactive", "inactive-superuser"])
@pytest.mark.parametrize("provider_none", [False, True])
def test_actor_and_provider_controls(composition, kind, provider_none, django_user_model, monkeypatch):
    with navbar_routes(lambda sfx: permission_routes(sfx, composition=composition)) as ns:
        ns.bar.items = [NavItem(child=ns.child.name)]
        if provider_none:
            ns.owner.ancestor_policy = AncestorPolicy(provider="none")
        actor = (
            AnonymousUser()
            if kind == "anonymous"
            else django_user_model.objects.create_user(
                username="inactive", is_active=False, is_superuser=kind == "inactive-superuser"
            )
        )
        owner = Publisher.objects.create(name="Owner")
        # Custom own admission cannot waive the existing protected-parent actor rule.
        monkeypatch.setattr(ns.target, "cv_has_access", Mock(return_value=True))
        _, data = lazy_host(ns, actor, owner)
        result = Template(TAG).render(Context(data))
        assert bool(result) is (provider_none and composition != "guardian")


@pytest.mark.django_db
def test_reachable_nested_host_does_not_predict_farther_policy(django_user_model):
    def build(sfx):
        ns, routed = section_routes(sfx, nested=True)
        ns.tenant.ancestor_policy = AncestorPolicy()
        ns.owner.ancestor_policy = AncestorPolicy(read=AncestorPermissions(nearest="view", higher="view"))
        ns.child.ancestor_policy = AncestorPolicy(read=AncestorPermissions(nearest="view", higher="change"))
        ns.bar.items = [NavItem(child=ns.child.name)]
        return ns, routed

    with navbar_routes(build) as ns:
        owner, child, grand = section_objects(ns)
        actor = django_user_model.objects.create_user(username="near")
        actor.user_permissions.add(
            *Permission.objects.filter(codename__in=["view_publisher", "view_book", "view_booknote"])
        )
        client = Client()
        client.force_login(actor)
        response = client.get(section_url(ns, ns.owner, "detail", owner, child, grand))
        assert response.status_code == 200
        destination = response.context["cv_navbar"]["items"][0]["url"]
        assert client.get(destination).status_code == 403


@pytest.mark.django_db
def test_visible_owner_link_does_not_bypass_project_queryset(django_user_model, monkeypatch):
    with navbar_routes(permission_routes) as ns:
        owner = Publisher.objects.create(name="Outside project scope")
        actor = django_user_model.objects.create_user(username="scoped")
        grant(ns, actor, owner)
        monkeypatch.setattr(ns.detail, "get_queryset", lambda self: Publisher.objects.none())
        client, response = host_response(ns, actor, owner)
        assert response.status_code == 200
        assert client.get(response.context["cv_navbar"]["items"][0]["url"]).status_code == 404
