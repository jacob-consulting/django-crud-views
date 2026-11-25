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
from guardian.shortcuts import assign_perm

from crud_views.lib import ancestors
from crud_views.lib.ancestor_policy import AncestorPermissions, AncestorPolicy
from crud_views.lib.navbar import CrudViewNavBarMixin, NavBar, NavItem, _build
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
from tests.test1 import test_ancestor_helpers as ancestor_helpers
from tests.test1.app.models import Book, Publisher
from tests.test1.test_ancestor_authorization import _client, _user, isolated_routes
from tests.test1.test_ancestor_helpers import _bound, _grant
from tests.test1.test_guardian_child_link_visibility import parent_spy
from tests.test1.test_navbar import navbar_routes, section_objects, section_routes, section_url

helpers = ancestor_helpers.helpers
data = ancestor_helpers.data
provider_calls = ancestor_helpers.provider_calls


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
        original = ns.target._cv_link_permission
        access = Mock(side_effect=lambda *args, **kwargs: (events.append("access"), original(*args, **kwargs))[1])
        state = Mock(side_effect=lambda *args: (events.append("state"), outcome != "disabled")[1])
        monkeypatch.setattr(ns.target, "_cv_link_permission", access)
        monkeypatch.setattr(ns.target, "cv_action_enabled", state)
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
        access.assert_called_once_with(request_actor, None, original_owner, rendering_view=None)
        own.assert_called_once_with(request_actor, original_owner)
        gate.assert_called_once_with(request_actor, original_owner)
        assert access.call_args.args[2] is original_owner
        if outcome == "denied":
            state.assert_not_called()
            extras.assert_not_called()
            assert events == ["access"]
            assert not response.context["cv_navbar"]
        else:
            state.assert_called_once_with(request_actor, original_owner)
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
        access = Mock(return_value=allowed)
        monkeypatch.setattr(ns.target, "cv_has_access", access)
        state = Mock(side_effect=AssertionError("state ran after denial/error"))
        monkeypatch.setattr(ns.target, "cv_action_enabled", state)
        _, data = lazy_host(ns, actor, owner)
        with pytest.raises(
            ImproperlyConfigured,
            match={"mapping": "undeclared", "operation": "operation|actions", "database": "shard"}[error],
        ):
            Template(TAG).render(Context(data))
        access.assert_not_called()
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
        assert not response.context["cv_navbar"]
        destination = section_url(ns, ns.child, "list", owner, child, grand)
        assert client.get(destination).status_code == 403


@pytest.mark.django_db
@pytest.mark.parametrize("far_allowed", [False, True])
def test_navbar_child_create_own_viewset_higher_denial(helpers, data, monkeypatch, provider_calls, far_allowed):
    """D-55: the navbar checks Publisher while the context create keeps its Book-only rewrite."""
    actor = _user("navbar_own_create")
    _grant(actor, helpers.pub, "view", data.penguin)
    if far_allowed:
        _grant(actor, helpers.pub, "change", data.penguin)
    for key in ("view", "change"):
        _grant(actor, helpers.book, key, data.book)
    helpers.note.vs.ancestor_policy = AncestorPolicy(write=AncestorPermissions(nearest="change", higher="change"))
    kwargs = {
        helpers.book.vs.parent.get_pk_name(): data.penguin.pk,
        helpers.note.vs.parent.get_pk_name(): data.book.pk,
    }
    view = _bound(helpers.note.List, actor, **kwargs)
    view.request.resolver_match = SimpleNamespace(url_name=helpers.note.vs.get_router_name("list"))
    assert view._cv_ancestor_guard() is None
    book, publisher = view._cv_ancestor_state.objects
    view.cv_navbar = NavBar(viewset=helpers.book.vs.name, items=[NavItem(child=helpers.note.vs.name, key="create")])
    create = Mock(wraps=helpers.note.Create.cv_create_has_access)
    state = Mock(wraps=helpers.note.Create.cv_action_enabled)
    monkeypatch.setattr(helpers.note.Create, "cv_create_has_access", create)
    monkeypatch.setattr(helpers.note.Create, "cv_action_enabled", state)
    provider_calls.clear()
    navbar = _build(view)
    assert bool(navbar) is far_allowed
    assert provider_calls[0] == (helpers.pub.vs.name, "app.change_publisher", publisher)
    assert provider_calls[0][2] is publisher
    if far_allowed:
        create.assert_called_once_with(actor, view, book)
        assert create.call_args.args[1] is view
        assert create.call_args.args[2] is book
        state.assert_called_once_with(actor, book)
        assert len(provider_calls) == 2
        assert provider_calls[1][2] is book
    else:
        create.assert_not_called()
        state.assert_not_called()
        assert len(provider_calls) == 1

    create.reset_mock()
    state.reset_mock()
    provider_calls.clear()
    context = view.cv_get_context("create", user=actor, request=view.request)
    assert context["cv_access"] is True
    assert context["cv_action_enabled"] is True
    create.assert_called_once_with(actor, view, book)
    state.assert_called_once_with(actor, book)
    assert provider_calls == [(helpers.book.vs.name, "app.change_book", book)]
    assert provider_calls[0][2] is book
    destination = reverse(helpers.note.vs.get_router_name("create"), kwargs=kwargs)
    assert _client(actor).get(destination).status_code == (200 if far_allowed else 403)


@pytest.mark.django_db
@pytest.mark.parametrize("composition", ["core", "guardian"])
@pytest.mark.parametrize("item_kind", ["owner", "child-list", "child-create"])
@pytest.mark.parametrize("far_allowed", [False, True])
def test_navbar_target_stricter_far_gate(composition, item_kind, far_allowed, monkeypatch):
    from tests.test1.test_link_consumer_costs import consumer_actor, consumer_routes, consumer_view, consumer_world

    with isolated_routes(lambda s: consumer_routes(s, composition)) as ns:
        world = consumer_world()
        actor = consumer_actor(ns, world, allowed=False)
        for family, obj, keys in (
            (ns.pub, world.pub, ("change",) if far_allowed else ()),
            (ns.book, world.book, ("change",)),
            (ns.note, world.note, ("change", "add")),
        ):
            for key in keys:
                assign_perm(family.vs.permissions[key], actor)
                if composition == "guardian":
                    assign_perm(family.vs.permissions[key], actor, obj)
        actor = type(actor).objects.get(pk=actor.pk)
        view = consumer_view(ns.note if item_kind == "owner" else ns.book, "Detail", actor, world)
        key = "update" if item_kind == "owner" else item_kind.removeprefix("child-")
        target = ns.note.vs.get_view_class(key)
        ns.note.vs.ancestor_policy = AncestorPolicy(
            cascade=True, actions={key: AncestorPermissions(nearest="change", higher="change")}
        )
        view.cv_navbar = NavBar(
            viewset=(ns.note if item_kind == "owner" else ns.book).vs.name,
            items=[NavItem(key=key) if item_kind == "owner" else NavItem(child=ns.note.vs.name, key=key)],
        )
        own = Mock(wraps=target.cv_has_access)
        state = Mock(wraps=target.cv_action_enabled)
        monkeypatch.setattr(target, "cv_has_access", own)
        monkeypatch.setattr(target, "cv_action_enabled", state)
        monkeypatch.setattr(
            target, "_cv_page_link_ancestors", Mock(side_effect=AssertionError("navbar used page seam"))
        )
        result = _build(view)
        assert bool(result) is far_allowed
        if far_allowed:
            state.assert_called_once()
            assert state.call_args.args[1] is (world.note if item_kind == "owner" else world.book)
        else:
            own.assert_not_called()
            state.assert_not_called()
        kwargs = {ns.book.vs.parent.get_pk_name(): world.pub.pk, ns.note.vs.parent.get_pk_name(): world.book.pk}
        if item_kind == "owner":
            kwargs[ns.note.vs.pk_name] = world.note.pk
        assert _client(actor).get(reverse(ns.note.vs.get_router_name(key), kwargs=kwargs)).status_code == (
            200 if far_allowed else 403
        )


@pytest.mark.django_db
@pytest.mark.parametrize("item_kind", ["owner", "child"])
@pytest.mark.parametrize("missing", [None, "publisher", "book"])
def test_inherited_navbar_uses_each_guardian_level(helpers, data, provider_calls, monkeypatch, item_kind, missing):
    actor = _user("navbar_levels")
    _grant(actor, helpers.pub, "view", data.penguin)
    _grant(actor, helpers.pub, "change", data.penguin)
    _grant(actor, helpers.book, "view", data.book)
    kwargs = {
        helpers.book.vs.parent.get_pk_name(): data.penguin.pk,
        helpers.note.vs.parent.get_pk_name(): data.book.pk,
    }
    view = _bound(helpers.note.List, actor, **kwargs)
    view.request.resolver_match = SimpleNamespace(url_name=helpers.note.vs.get_router_name("list"))
    assert view._cv_ancestor_guard() is None
    book, publisher = view._cv_ancestor_state.objects
    helpers.note.vs.ancestor_policy = AncestorPolicy(read=AncestorPermissions(nearest="view", higher="change"))
    view.cv_navbar = NavBar(
        viewset=helpers.book.vs.name,
        items=[NavItem(key="detail") if item_kind == "owner" else NavItem(child=helpers.note.vs.name)],
    )
    if missing is not None:
        view._cv_ancestor_state = ancestors._AncestorState(
            (None if missing == "book" else book, None if missing == "publisher" else publisher)
        )
    monkeypatch.setattr(view, "cv_get_parent_object", Mock(side_effect=AssertionError("parent lookup")))
    provider_calls.clear()
    if missing == "book":
        with pytest.raises(ImproperlyConfigured, match=r"owner.*not resolved"):
            _build(view)
        assert provider_calls == []
        return
    result = _build(view)
    assert bool(result) is (item_kind == "child" or missing is None)
    expected = (
        []
        if item_kind == "owner" and missing == "publisher"
        else [(helpers.pub.vs.name, "app.view_publisher", publisher)]
        if item_kind == "owner"
        else [(helpers.book.vs.name, "app.view_book", book)]
        if missing == "publisher"
        else [(helpers.pub.vs.name, "app.change_publisher", publisher), (helpers.book.vs.name, "app.view_book", book)]
    )
    assert provider_calls == expected
    assert all(actual[2] is wanted[2] for actual, wanted in zip(provider_calls, expected, strict=True))


@pytest.mark.django_db
def test_navbar_create_on_deeper_viewset_receives_no_rendering_view(helpers, data, monkeypatch):
    actor = _user("navbar_deeper_create")
    for key in ("view", "change"):
        _grant(actor, helpers.pub, key, data.penguin)
    _grant(actor, helpers.book, "view", data.book)
    view = _bound(
        helpers.note.List,
        actor,
        **{
            helpers.book.vs.parent.get_pk_name(): data.penguin.pk,
            helpers.note.vs.parent.get_pk_name(): data.book.pk,
        },
    )
    assert view._cv_ancestor_guard() is None
    publisher = view._cv_ancestor_state.objects[1]
    view.cv_navbar = NavBar(viewset=helpers.pub.vs.name, items=[NavItem(child=helpers.book.vs.name, key="create")])
    create = Mock(wraps=helpers.book.Create.cv_create_has_access)
    monkeypatch.setattr(helpers.book.Create, "cv_create_has_access", create)
    assert _build(view)
    create.assert_called_once_with(actor, None, publisher)
    assert create.call_args.args[2] is publisher


@pytest.mark.django_db
@pytest.mark.parametrize("missing_higher", [False, True])
def test_inherited_navbar_sibling_keeps_level_specific_guardian_grants(missing_higher, monkeypatch, provider_calls):
    from tests.test1.test_link_consumer_costs import consumer_routes, consumer_view, consumer_world

    with isolated_routes(lambda s: consumer_routes(s, "guardian")) as ns:
        world = consumer_world()
        actor = _user("navbar_sibling_levels")
        # Different model/object grants at each level; no global grants can cover a wrong identity.
        _grant(actor, ns.pub, "view", world.pub)
        _grant(actor, ns.pub, "change", world.pub)
        _grant(actor, ns.book, "view", world.book)
        page = consumer_view(ns.note, "List", actor, world)
        book, publisher = page._cv_ancestor_state.objects
        ns.sibling.vs.ancestor_policy = AncestorPolicy(
            cascade=True, read=AncestorPermissions(nearest="view", higher="change")
        )
        page.cv_navbar = NavBar(viewset=ns.book.vs.name, items=[NavItem(child=ns.sibling.vs.name)])
        if missing_higher:
            page._cv_ancestor_state = ancestors._AncestorState((book, None))
        monkeypatch.setattr(page, "cv_get_parent_object", Mock(side_effect=AssertionError("parent hook")))
        monkeypatch.setattr(ViewSet, "get_queryset", Mock(side_effect=AssertionError("ancestor query")))
        state = Mock(wraps=ns.sibling.List.cv_action_enabled)
        monkeypatch.setattr(ns.sibling.List, "cv_action_enabled", state)
        provider_calls.clear()
        result = _build(page)
        assert result["items"][0]["url"] == reverse(
            ns.sibling.vs.get_router_name("list"),
            kwargs={ns.book.vs.parent.get_pk_name(): world.pub.pk, ns.sibling.vs.parent.get_pk_name(): world.book.pk},
        )
        expected = [] if missing_higher else [(ns.pub.vs.name, "app.change_publisher", publisher)]
        expected.append((ns.book.vs.name, "app.view_book", book))
        assert provider_calls == expected
        assert all(actual[2] is wanted[2] for actual, wanted in zip(provider_calls, expected, strict=True))
        state.assert_called_once_with(actor, book)
        assert state.call_args.args[1] is book


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
