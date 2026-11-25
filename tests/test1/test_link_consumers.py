"""Actual-target link contracts for the stage-3a consumers."""

from unittest.mock import Mock

import pytest
from django.contrib.auth.models import Permission, User
from django.core.exceptions import ImproperlyConfigured
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from lxml import html

from crud_views.lib import ancestors, link_access
from crud_views.lib.view import ChildContextButton, ContextButton, ParentContextButton, SiblingContextButton
from crud_views.lib.viewset import AncestorPermissions, AncestorPolicy, ViewSet
from crud_views.templatetags.crud_views import cv_context_has_permission
from crud_views_guardian.lib.viewset import GuardianViewSet
from tests.test1.test_ancestor_authorization import isolated_routes
from tests.test1.test_link_consumer_costs import consumer_actor, consumer_routes, consumer_view, consumer_world

# Collection-only destinations are explicit: sibling/child URLs cannot supply an
# own object, navbar owner items require one, and bulk targets are form views.
CONSUMER_SHAPES = [
    ("context", "update"),
    ("context", "list"),
    ("parent", "update"),
    ("parent", "list"),
    ("sibling", "list"),
    ("child", "list"),
    ("view_key", "update"),
    ("view_key", "list"),
    ("table_row", "update"),
    ("table_row", "list"),
    ("card_own", "update"),
    ("card_own", "list"),
    ("card_child", "list"),
    ("navbar_owner", "update"),
    ("navbar_child", "list"),
    ("filter", "update"),
    ("filter", "list"),
    ("cancel", "update"),
    ("cancel", "list"),
    ("bulk", "mark"),
]


@pytest.mark.django_db
def test_guardian_actor_tracer(monkeypatch):
    """The real parent page cannot expose create through an override after parent denial."""
    from guardian.shortcuts import assign_perm

    with isolated_routes(lambda suffix: consumer_routes(suffix, "guardian")) as ns:
        world = consumer_world()
        actor = consumer_actor(ns, world, allowed=False)
        button = ChildContextButton(key="new", child_name=ns.book.vs.name, child_key="create", label_mode="both")
        monkeypatch.setattr(ns.pub.Detail, "cv_context_buttons", [button])
        monkeypatch.setattr(ns.pub.Detail, "cv_context_actions", ["new"])
        create, state = Mock(return_value=True), Mock(return_value=True)
        monkeypatch.setattr(ns.book.Create, "cv_create_has_access", create)
        monkeypatch.setattr(ns.book.Create, "cv_action_enabled", state)
        destination = reverse(
            ns.book.vs.get_router_name("create"), kwargs={ns.book.vs.parent.get_pk_name(): world.pub.pk}
        )
        host = reverse(ns.pub.vs.get_router_name("detail"), kwargs={"pk": world.pub.pk})
        client = Client()
        client.force_login(actor)
        response = client.get(host)
        assert response.status_code == 200
        assert not html.fromstring(response.content).xpath("//*[@href=$url]", url=destination)
        create.assert_not_called()
        state.assert_not_called()
        assert client.get(destination).status_code == 403
        state.assert_not_called()

        assign_perm(ns.pub.vs.permissions["change"], actor, world.pub)
        fresh = User.objects.get(pk=actor.pk)
        client.force_login(fresh)
        response = client.get(host)
        assert response.status_code == 200
        assert html.fromstring(response.content).xpath("//*[@href=$url]", url=destination)
        create.assert_called_once()
        assert create.call_args.args[0].pk == fresh.pk
        assert create.call_args.args[1] is None  # A child control crosses ViewSets.
        assert create.call_args.args[2] is response.context["view"].object
        assert client.get(destination).status_code == 200

        create.reset_mock()
        create.return_value = False
        state.reset_mock()
        response = client.get(host)
        assert response.status_code == 200
        assert not html.fromstring(response.content).xpath("//*[@href=$url]", url=destination)
        create.assert_called_once()
        state.assert_not_called()
        assert client.get(destination).status_code == 200


@pytest.mark.django_db
def test_guardian_anonymous_object_link_on_plain_host(monkeypatch):
    from django.contrib.auth.models import AnonymousUser
    from guardian.conf import settings as guardian_settings
    from guardian.shortcuts import assign_perm

    from crud_views.lib.views import DetailView

    def routes(suffix):
        ns, families = consumer_routes(suffix, "guardian")
        ns.pub.vs.ancestor_policy = AncestorPolicy(provider="none")
        ns.Host = type(
            "PlainHost",
            (DetailView,),
            {
                "cv_viewset": ns.book.vs,
                "cv_key": "host",
                "cv_path": "host",
                "cv_context_actions": ["target"],
                "cv_context_buttons": [ContextButton(key="target", key_target="detail", label_mode="both")],
            },
        )
        return ns, families

    with isolated_routes(routes) as ns:
        world = consumer_world()
        backing = User.objects.create_user(username="guardian_anonymous")
        monkeypatch.setattr(guardian_settings, "ANONYMOUS_USER_NAME", backing.username)
        actor = AnonymousUser()
        assign_perm(ns.book.vs.permissions["view"], actor, world.book)
        assert ns.book.Detail.cv_has_access(actor, world.book) is True
        kwargs = {ns.book.vs.parent.get_pk_name(): world.pub.pk, "pk": world.book.pk}
        destination = reverse(ns.book.vs.get_router_name("detail"), kwargs=kwargs)
        client = Client()
        response = client.get(reverse(ns.book.vs.get_router_name("host"), kwargs=kwargs))
        assert response.status_code == 200
        assert not html.fromstring(response.content).xpath("//*[@href=$url]", url=destination)
        response = client.get(destination)
        assert response.status_code == 302
        assert response.url.startswith("/accounts/login/?next=")


def grid_routes(suffix, composition):
    """Use a Resource leaf to render a parent link to the existing three-level target."""
    from crud_views.lib.resource import ResourceViewMixin
    from crud_views.lib.views import DetailView
    from crud_views.lib.viewset import ParentViewSet
    from tests.test1.test_ancestor_resources import TopFile

    ns, routed = consumer_routes(suffix, composition)
    leaf = ViewSet(model=TopFile, name=f"consumerleaf{suffix}", parent=ParentViewSet(name=ns.note.vs.name))
    ns.Leaf = type("ConsumerLeaf", (ResourceViewMixin, DetailView), {"cv_viewset": leaf})
    return ns, [*routed, leaf]


def grid_consumer(ns, world, actor, surface, key):
    """Bind each named entry point independently, retaining its normal URL shape."""
    from types import SimpleNamespace

    from crud_views.lib.bulk import BulkSelectionMixin
    from crud_views.lib.navbar import NavBar, NavItem, _build
    from crud_views.lib.view import CardAction
    from crud_views.lib.view.visibility import cv_resolve_action
    from tests.test1.test_ancestor_helpers import _bound
    from tests.test1.test_ancestor_resources import TopFile

    family = ns.sibling if surface == "sibling" else ns.note
    target = family.vs.get_view_class(key)
    source = ns.book if surface in {"child", "card_child", "navbar_child"} else ns.note
    page_key = "Card" if surface in {"card_own", "card_child"} else "List" if surface == "table_row" else "Detail"
    page = consumer_view(source, page_key, actor, world)
    if surface == "parent":
        kwargs = {
            edge.get_pk_name(): obj.pk
            for (edge, _), obj in zip(
                ancestors._walk_ancestors(ns.Leaf.cv_viewset), (world.note, world.book, world.pub), strict=True
            )
        }
        page = _bound(ns.Leaf, actor, pk="known-file", **kwargs)
        page.object = TopFile(key="known-file")
        page.request.resolver_match = SimpleNamespace(url_name=ns.Leaf.cv_viewset.get_router_name("detail"))
        assert page._cv_ancestor_guard() is None
    own = ancestors._resolved_ancestor(page, ns.note.vs.name) if surface == "parent" else world.note
    own = own if target.cv_object else None
    nearest = world.book if source is ns.book else ancestors._resolved_ancestor(page, ns.book.vs.name)
    far = ancestors._resolved_ancestor(page, ns.pub.vs.name)
    page.cv_cancel_key = key
    page.cv_bulk_actions = (key,)
    page.cv_navbar = NavBar(
        viewset=source.vs.name,
        items=[NavItem(child=family.vs.name, key=key) if surface == "navbar_child" else NavItem(key=key)],
    )

    def render():
        user = page.request.user
        context = page.cv_get_view_context(object=page.object)
        if surface == "context":
            result = ContextButton(key="grid", key_target=key).get_context(context)
        elif surface == "parent":
            result = ParentContextButton(key="grid", key_target=key).get_context(context)
        elif surface == "sibling":
            result = SiblingContextButton(key="grid", sibling_name=family.vs.name, sibling_key=key).get_context(context)
        elif surface == "child":
            result = ChildContextButton(key="grid", child_name=family.vs.name, child_key=key).get_context(context)
        elif surface in {"view_key", "table_row"}:
            result = page.cv_get_context(
                key, obj=world.note, user=user, location="list" if surface == "table_row" else "context"
            )
        elif surface in {"card_own", "card_child"}:
            action = (
                CardAction(child_name=family.vs.name, child_key=key) if surface == "card_child" else CardAction(key=key)
            )
            result = page.cv_get_card_action_data(action, world.book if surface == "card_child" else world.note, user)
        elif surface.startswith("navbar"):
            return bool(_build(page))
        elif surface == "filter":
            return cv_context_has_permission(page, key)
        elif surface == "cancel":
            return page.cv_get_cancel_url() is not None
        elif surface == "bulk":
            # Each observation is a fresh admission calculation, not the source
            # page's intentionally cached effective-actions presentation property.
            return bool(BulkSelectionMixin._cv_effective_bulk_actions.func(page))
        else:
            raise AssertionError(surface)
        resolved = cv_resolve_action(result)
        return resolved is not None and not resolved["cv_disabled"]

    return page, target, own, nearest, far, render


@pytest.mark.django_db
@pytest.mark.parametrize("composition", ["core", "guardian"])
@pytest.mark.parametrize("surface,key", CONSUMER_SHAPES)
def test_consumer_grid_real_far_denial_and_fresh_grant(composition, surface, key, monkeypatch):
    """A reachable page uses Read while its target needs change at the actual far object."""
    from guardian.shortcuts import assign_perm, remove_perm

    with isolated_routes(lambda suffix: grid_routes(suffix, composition)) as ns:
        world = consumer_world()
        actor = consumer_actor(ns, world)
        actor.user_permissions.remove(Permission.objects.get(codename="change_publisher"))
        if composition == "guardian":
            remove_perm(ns.pub.vs.permissions["change"], actor, world.pub)
        actor = User.objects.get(pk=actor.pk)
        page, target, own_obj, nearest, far, render = grid_consumer(ns, world, actor, surface, key)
        target.cv_viewset.ancestor_policy = AncestorPolicy(
            cascade=True, actions={key: AncestorPermissions(nearest="view", higher="change")}
        )
        events = []
        provider = GuardianViewSet if composition == "guardian" else ViewSet
        original = provider._ancestor_has_permission

        def gate(vs, user, permission, obj, *, view):
            events.append((vs.name, obj, permission))
            return original(vs, user, permission, obj, view=view)

        monkeypatch.setattr(provider, "_ancestor_has_permission", gate)
        own = Mock(wraps=target.cv_has_access)
        state = Mock(return_value=True)
        monkeypatch.setattr(target, "cv_has_access", own)
        monkeypatch.setattr(target, "cv_action_enabled", state)
        retained_cancel = composition == "guardian" and surface == "cancel"
        assert render() is retained_cancel
        expected_far = (ns.pub.vs.name, far, ns.pub.vs.permissions["change"])
        expected_near = (ns.book.vs.name, nearest, ns.book.vs.permissions["view"])
        assert events == ([expected_near] if retained_cancel else [expected_far])
        assert events[0][1] is (nearest if retained_cancel else far)
        if not retained_cancel:
            own.assert_not_called()
            state.assert_not_called()
        else:
            own.assert_called_once_with(actor, own_obj)
            state.assert_called_once_with(actor, own_obj if target.cv_object else nearest)
        destination = reverse(
            target.cv_viewset.get_router_name(key),
            kwargs={
                ns.book.vs.parent.get_pk_name(): world.pub.pk,
                target.cv_viewset.parent.get_pk_name(): world.book.pk,
                **({"pk": world.note.pk} if target.cv_object else {}),
            },
        )
        client = Client()
        client.force_login(actor)
        state.reset_mock()
        assert client.get(destination).status_code == 403
        state.assert_not_called()

        assign_perm(ns.pub.vs.permissions["change"], actor)
        if composition == "guardian":
            assign_perm(ns.pub.vs.permissions["change"], actor, world.pub)
        fresh = User.objects.get(pk=actor.pk)
        assert fresh is not actor
        page.request.user = fresh
        events.clear()
        own.reset_mock()
        assert render() is True
        assert events == ([expected_near] if retained_cancel else [expected_far, expected_near])
        assert all(
            event[1] is wanted[1]
            for event, wanted in zip(
                events, [expected_near] if retained_cancel else [expected_far, expected_near], strict=True
            )
        )
        own.assert_called_once_with(fresh, own_obj)
        assert own.call_args.args[1] is own_obj
        if surface == "filter":
            state.assert_not_called()
        else:
            state.assert_called_once_with(fresh, own_obj if target.cv_object else nearest)
            assert state.call_args.args[1] is (own_obj if target.cv_object else nearest)


@pytest.mark.django_db
@pytest.mark.parametrize("composition", ["core", "guardian"])
@pytest.mark.parametrize("surface,key", CONSUMER_SHAPES)
@pytest.mark.parametrize("problem", ["ancestor-key", "operation", "auth-database", "own-key"])
def test_consumer_grid_errors_and_missing_own_key(composition, surface, key, problem, monkeypatch):
    with isolated_routes(lambda suffix: grid_routes(suffix, composition)) as ns:
        world = consumer_world()
        actor = consumer_actor(ns, world)
        _page, target, _, _, _, render = grid_consumer(ns, world, actor, surface, key)
        state = Mock(side_effect=AssertionError("state after permission failure"))
        monkeypatch.setattr(target, "cv_action_enabled", state)
        if problem == "ancestor-key":
            target.cv_viewset.ancestor_policy = AncestorPolicy(
                cascade=True, actions={key: AncestorPermissions(nearest="absent", higher="view")}
            )
        elif problem == "operation":
            monkeypatch.setattr(target, "_cv_ancestor_operation", "unmapped", raising=False)
        elif problem == "auth-database":
            monkeypatch.setattr(actor._state, "db", "other")
        else:
            monkeypatch.setattr(target, "cv_permission", "absent")
        if problem == "own-key":
            assert render() is False
        else:
            with pytest.raises(ImproperlyConfigured):
                render()
        state.assert_not_called()


@pytest.mark.django_db
@pytest.mark.parametrize("surface,key", CONSUMER_SHAPES)
@pytest.mark.parametrize("changed", ["permission", "state"])
def test_consumer_repeated_target_rechecks_public_decisions(surface, key, changed, monkeypatch):
    with isolated_routes(lambda suffix: grid_routes(suffix, "guardian")) as ns:
        world = consumer_world()
        actor = consumer_actor(ns, world)
        _page, target, own_obj, nearest, _, render = grid_consumer(ns, world, actor, surface, key)
        own, state = Mock(return_value=True), Mock(return_value=True)
        changing = own if changed == "permission" else state
        changing.side_effect = [True, False]
        monkeypatch.setattr(target, "cv_has_access", own)
        monkeypatch.setattr(target, "cv_action_enabled", state)
        assert render() is True
        assert render() is (surface == "filter" and changed == "state")
        assert own.call_count == 2
        assert all(call.args[0] is actor and call.args[1] is own_obj for call in own.call_args_list)
        assert state.call_count == (0 if surface == "filter" else 1 if changed == "permission" else 2)
        assert all(call.args[1] is (own_obj if target.cv_object else nearest) for call in state.call_args_list)


@pytest.mark.django_db
@pytest.mark.parametrize("surface,key", [("parent", "update"), ("parent", "list"), ("sibling", "list")])
@pytest.mark.parametrize("missing", ["nearest", "higher"])
def test_guardian_cross_viewset_buttons_keep_unknown_level_positions(surface, key, missing, monkeypatch):
    with isolated_routes(lambda suffix: grid_routes(suffix, "guardian")) as ns:
        world = consumer_world()
        actor = consumer_actor(ns, world)
        page, target, own_obj, nearest, _, render = grid_consumer(ns, world, actor, surface, key)
        objects = list(page._cv_ancestor_state.objects)
        objects[(-2 if missing == "nearest" else -1)] = None
        page._cv_ancestor_state = ancestors._AncestorState(tuple(objects))
        events = []
        original = GuardianViewSet._ancestor_has_permission

        def gate(vs, user, permission, obj, *, view):
            events.append((vs.name, obj))
            return original(vs, user, permission, obj, view=view)

        monkeypatch.setattr(GuardianViewSet, "_ancestor_has_permission", gate)
        own, state = Mock(wraps=target.cv_has_access), Mock(return_value=True)
        monkeypatch.setattr(target, "cv_has_access", own)
        monkeypatch.setattr(target, "cv_action_enabled", state)
        assert render() is (missing == "higher")
        if missing == "higher":
            assert events == [(ns.book.vs.name, nearest)]
            assert events[0][1] is nearest
            own.assert_called_once_with(actor, own_obj)
            state.assert_called_once_with(actor, own_obj if target.cv_object else nearest)
        else:
            assert events == []
            own.assert_not_called()
            state.assert_not_called()


@pytest.mark.django_db
@pytest.mark.parametrize("page_kind", ["List", "GuardianCard"])
@pytest.mark.parametrize("button_kind", ["parent", "sibling"])
@pytest.mark.parametrize("page_create_allowed", [False, True])
def test_guardian_list_and_card_rewrite_parent_and_sibling_keys(
    page_kind, button_kind, page_create_allowed, monkeypatch
):
    from crud_views_guardian.lib.views import GuardianCardListViewPermissionRequired

    def build(suffix):
        ns, routed = consumer_routes(suffix, "guardian")
        ns.note.GuardianCard = type(
            "RewriteCard",
            (GuardianCardListViewPermissionRequired,),
            {
                "cv_viewset": ns.note.vs,
                "cv_key": "guardian_card",
                "cv_path": "guardian-card",
                "cv_card_actions": [],
            },
        )
        return ns, routed

    with isolated_routes(build) as ns:
        world = consumer_world()
        actor = consumer_actor(ns, world)
        page = consumer_view(ns.note, page_kind, actor, world)
        target = ns.book.Create if button_kind == "parent" else ns.sibling.List
        button = (
            ParentContextButton(key="create", key_target="create")
            if button_kind == "parent"
            else SiblingContextButton(key="create", sibling_name=ns.sibling.vs.name, sibling_key="list")
        )
        page.cv_context_buttons = [button]
        actual = Mock(return_value=not page_create_allowed)
        rewritten = Mock(return_value=page_create_allowed)
        monkeypatch.setattr(target, "cv_create_has_access" if button_kind == "parent" else "cv_has_access", actual)
        monkeypatch.setattr(ns.note.Create, "cv_create_has_access", rewritten)
        result = page.cv_get_context("create", user=actor)
        assert result["cv_access"] is page_create_allowed
        assert result["cv_action_enabled"] is True
        assert result["cv_url"] == reverse(
            target.cv_viewset.get_router_name(target.cv_key),
            kwargs={
                ns.book.vs.parent.get_pk_name(): world.pub.pk,
                **({ns.sibling.vs.parent.get_pk_name(): world.book.pk} if button_kind == "sibling" else {}),
            },
        )
        if button_kind == "parent":
            actual.assert_called_once_with(actor, None, page._cv_ancestor_state.objects[1])
        else:
            actual.assert_called_once_with(actor, None)
        rewritten.assert_called_once_with(actor, page, page._cv_ancestor_state.parent)
        assert rewritten.call_args.args[1] is page
        assert rewritten.call_args.args[2] is page._cv_ancestor_state.parent


@pytest.mark.django_db
@pytest.mark.parametrize("surface", ["button", "filter", "card"])
@pytest.mark.parametrize("far_allowed", [False, True])
def test_queryset_only_links_keep_nearest_skip_but_gate_higher(surface, far_allowed, monkeypatch):
    from guardian.shortcuts import remove_perm

    from crud_views.lib.view import CardAction
    from tests.test1.test_link_cancel import guardian_cancel_routes

    with isolated_routes(guardian_cancel_routes) as ns:
        world = consumer_world()
        actor = consumer_actor(ns, world)
        remove_perm(ns.book.vs.permissions["change"], actor, world.book)
        if not far_allowed:
            remove_perm(ns.pub.vs.permissions["change"], actor, world.pub)
        actor = User.objects.get(pk=actor.pk)
        page = consumer_view(ns.note, "Card" if surface == "card" else "Detail", actor, world)
        ns.note.vs.ancestor_policy = AncestorPolicy(
            cascade=True,
            actions={
                "queryset": AncestorPermissions(nearest="change", higher="change"),
            },
        )
        own, state = Mock(wraps=ns.note.QuerysetOnly.cv_has_access), Mock(return_value=True)
        monkeypatch.setattr(ns.note.QuerysetOnly, "cv_has_access", own)
        monkeypatch.setattr(ns.note.QuerysetOnly, "cv_action_enabled", state)
        gates = []
        original = GuardianViewSet._ancestor_has_permission

        def gate(vs, user, permission, obj, *, view):
            gates.append((vs.name, obj))
            return original(vs, user, permission, obj, view=view)

        monkeypatch.setattr(GuardianViewSet, "_ancestor_has_permission", gate)
        if surface == "filter":
            result = cv_context_has_permission(page, "queryset")
        elif surface == "card":
            result = page.cv_get_card_action_data(CardAction(key="queryset"), world.note, actor)["cv_access"]
        else:
            result = ContextButton(key="only", key_target="queryset").get_context(page.cv_get_view_context())[
                "cv_access"
            ]
        assert result is far_allowed
        assert gates == [(ns.pub.vs.name, page._cv_ancestor_state.objects[1])]
        assert gates[0][1] is page._cv_ancestor_state.objects[1]
        if far_allowed:
            own.assert_called_once_with(actor, None)
        else:
            own.assert_not_called()
        if far_allowed and surface != "filter":
            state.assert_called_once_with(actor, page._cv_ancestor_state.parent)
        else:
            state.assert_not_called()
        client = Client()
        client.force_login(actor)
        assert client.get(page.cv_get_url("queryset")).status_code == 403


@pytest.mark.django_db
@pytest.mark.parametrize("surface", ["button", "card", "navbar"])
@pytest.mark.parametrize("kind", ["anonymous", "inactive"])
@pytest.mark.parametrize("higher_protected", [False, True])
def test_guardian_child_create_actor_rule_precedes_hook(surface, kind, higher_protected, monkeypatch):
    from django.contrib.auth.models import AnonymousUser

    from crud_views.lib.navbar import NavBar, NavItem, _build
    from crud_views.lib.view import CardAction

    with isolated_routes(lambda suffix: consumer_routes(suffix, "guardian")) as ns:
        world = consumer_world()
        actor = consumer_actor(ns, world)
        page = consumer_view(ns.book, "Card" if surface == "card" else "Detail", actor, world)
        ns.book.vs.ancestor_policy = AncestorPolicy(provider="none")
        ns.pub.vs.ancestor_policy = AncestorPolicy(provider="guardian" if higher_protected else "none")
        actor.is_active = False
        page.request.user = AnonymousUser() if kind == "anonymous" else actor
        create = Mock(wraps=ns.note.Create.cv_create_has_access)
        state = Mock(return_value=True)
        monkeypatch.setattr(ns.note.Create, "cv_create_has_access", create)
        monkeypatch.setattr(ns.note.Create, "cv_action_enabled", state)
        if surface == "button":
            result = ChildContextButton(key="new", child_name=ns.note.vs.name, child_key="create").get_context(
                page.cv_get_view_context(object=world.book)
            )["cv_access"]
        elif surface == "card":
            result = page.cv_get_card_action_data(
                CardAction(child_name=ns.note.vs.name, child_key="create"), world.book, page.request.user
            )["cv_access"]
        else:
            page.cv_navbar = NavBar(viewset=ns.book.vs.name, items=[NavItem(child=ns.note.vs.name, key="create")])
            result = bool(_build(page))
        assert result is False
        create.assert_not_called()
        state.assert_not_called()


@pytest.mark.django_db
@pytest.mark.parametrize("family_name", ["book", "note"])
@pytest.mark.parametrize("outcome", ["allowed", "nearest", "higher", "own", "missing", "hole"])
def test_permission_filter_checks_known_ancestry_without_state(family_name, outcome, monkeypatch):
    with isolated_routes(consumer_routes) as ns:
        world = consumer_world()
        actor = consumer_actor(ns, world)
        family = getattr(ns, family_name)
        page = consumer_view(family, "Detail", actor, world, guarded=outcome != "missing")
        target = family.Update
        family.vs.ancestor_policy = AncestorPolicy(
            cascade=True, actions={"update": AncestorPermissions(nearest="change", higher="change")}
        )
        if outcome == "hole" and family_name == "note":
            page._cv_ancestor_state = ancestors._AncestorState((page._cv_ancestor_state.parent, None))
        known = link_access._known_link_ancestors(target, page)
        events = []
        original = ViewSet._ancestor_has_permission

        def gate(vs, user, permission, obj, *, view):
            events.append((vs.name, obj))
            denied = (outcome == "nearest" and vs.name == family.vs.parent.name) or (
                outcome == "higher" and family_name == "note" and vs.name == ns.pub.vs.name
            )
            return not denied and original(vs, user, permission, obj, view=view)

        monkeypatch.setattr(ViewSet, "_ancestor_has_permission", gate)
        own = Mock(return_value=outcome != "own")
        state = Mock(return_value=False)
        monkeypatch.setattr(target, "cv_has_access", own)
        monkeypatch.setattr(target, "cv_action_enabled", state)
        monkeypatch.setattr(page, "cv_get_parent_object", Mock(side_effect=AssertionError("filter lookup")))
        allowed = outcome in {"allowed", "hole"} or (outcome == "higher" and family_name == "book")
        with CaptureQueriesContext(connection) as queries:
            assert cv_context_has_permission(page, "update") is allowed
        state.assert_not_called()  # Even a state-disabled action can pass this predicate.
        if outcome in {"missing", "nearest"} or (outcome == "higher" and family_name == "note"):
            own.assert_not_called()
        else:
            own.assert_called_once_with(actor, page.object)
            assert own.call_args.args[1] is page.object
        expected = [
            (ancestor.name, obj)
            for (_, ancestor), obj in reversed(list(zip(ancestors._walk_ancestors(family.vs), known, strict=True)))
            if obj is not None
        ]
        if outcome == "higher" and family_name == "note":
            expected = expected[:1]
        assert events == expected
        assert not any(
            f'from "app_{model}"' in query["sql"].lower()
            for query in queries
            for model in ("publisher", "book", "booknote")
        )


@pytest.mark.django_db
@pytest.mark.parametrize("problem", ["permission", "operation", "auth_database"])
def test_permission_filter_keeps_lookup_and_configuration_error_boundaries(problem, monkeypatch):
    with isolated_routes(consumer_routes) as ns:
        world = consumer_world()
        actor = consumer_actor(ns, world)
        page = consumer_view(ns.note, "Detail", actor, world)
        state = Mock(side_effect=AssertionError("filter state"))
        monkeypatch.setattr(ns.note.Update, "cv_action_enabled", state)
        assert cv_context_has_permission(page, "not_registered") is False
        if problem == "permission":
            ns.note.vs.ancestor_policy = AncestorPolicy(
                cascade=True, actions={"update": AncestorPermissions(nearest="view", higher="missing")}
            )
        elif problem == "operation":
            monkeypatch.setattr(ns.note.Update, "_cv_ancestor_operation", "unmapped", raising=False)
        else:
            monkeypatch.setattr(actor._state, "db", "other")
        with pytest.raises(ImproperlyConfigured):
            cv_context_has_permission(page, "update")
        state.assert_not_called()


@pytest.mark.django_db
def test_permission_filter_guardian_create_retains_immediate_only_seam(monkeypatch):
    from guardian.shortcuts import remove_perm

    with isolated_routes(lambda s: consumer_routes(s, "guardian")) as ns:
        world = consumer_world()
        actor = consumer_actor(ns, world)
        actor.user_permissions.remove(Permission.objects.get(codename="change_publisher"))
        remove_perm(ns.pub.vs.permissions["change"], actor, world.pub)
        actor = User.objects.get(pk=actor.pk)
        page = consumer_view(ns.note, "Detail", actor, world)
        ns.note.vs.ancestor_policy = AncestorPolicy(
            cascade=True, actions={"create": AncestorPermissions(nearest="change", higher="change")}
        )
        create = Mock(wraps=ns.note.Create.cv_create_has_access)
        state = Mock(side_effect=AssertionError("filter state"))
        monkeypatch.setattr(ns.note.Create, "cv_create_has_access", create)
        monkeypatch.setattr(ns.note.Create, "cv_action_enabled", state)
        assert cv_context_has_permission(page, "create") is True
        create.assert_called_once_with(actor, page, page._cv_ancestor_state.parent)
        assert create.call_args.args[1] is page
        state.assert_not_called()


@pytest.mark.django_db
@pytest.mark.parametrize("composition", ["core", "guardian"])
@pytest.mark.parametrize("key", ["update", "list"])
def test_permission_filter_real_far_denial_matches_request(composition, key, monkeypatch):
    from guardian.shortcuts import remove_perm

    with isolated_routes(lambda s: consumer_routes(s, composition)) as ns:
        world = consumer_world()
        actor = consumer_actor(ns, world)
        actor.user_permissions.remove(Permission.objects.get(codename="change_publisher"))
        if composition == "guardian":
            remove_perm(ns.pub.vs.permissions["change"], actor, world.pub)
        actor = User.objects.get(pk=actor.pk)
        page = consumer_view(ns.note, "Detail", actor, world)
        ns.note.vs.ancestor_policy = AncestorPolicy(
            cascade=True, actions={key: AncestorPermissions(nearest="view", higher="change")}
        )
        state = Mock(side_effect=AssertionError("state after denied far permission"))
        monkeypatch.setattr(ns.note.vs.get_view_class(key), "cv_action_enabled", state)
        assert cv_context_has_permission(page, key) is False
        client = Client()
        client.force_login(actor)
        assert client.get(page.cv_get_url(key, obj=world.note)).status_code == 403
        state.assert_not_called()


@pytest.mark.django_db
def test_context_tracer(monkeypatch):
    """A real page remains permitted while its stricter target link follows request denial."""
    with isolated_routes(consumer_routes) as ns:
        world = consumer_world()
        actor = consumer_actor(ns, world)
        actor.user_permissions.remove(Permission.objects.get(codename="change_publisher"))
        actor = User.objects.get(pk=actor.pk)
        monkeypatch.setattr(
            ns.book.Detail,
            "cv_context_buttons",
            [
                ContextButton(key="permitted", key_target="list"),
                ContextButton(key="stricter", key_target="update"),
            ],
        )
        monkeypatch.setattr(ns.book.Detail, "cv_context_actions", ["permitted", "stricter"])
        state = Mock(return_value=True)
        monkeypatch.setattr(ns.book.Update, "cv_action_enabled", state)
        client = Client()
        client.force_login(actor)
        kwargs = {ns.book.vs.parent.get_pk_name(): world.pub.pk, "pk": world.book.pk}
        update_url = reverse(ns.book.vs.get_router_name("update"), kwargs=kwargs)
        list_url = reverse(ns.book.vs.get_router_name("list"), kwargs={ns.book.vs.parent.get_pk_name(): world.pub.pk})
        assert client.get(update_url).status_code == 403
        state.assert_not_called()
        response = client.get(reverse(ns.book.vs.get_router_name("detail"), kwargs=kwargs))
        assert response.status_code == 200
        links = [url.split("?", 1)[0] for url in html.fromstring(response.content).xpath("//a/@href")]
        assert list_url in links
        assert update_url not in links, "parent view without change must hide the update button"
        state.assert_not_called()
        # Independent permitted control reaches state exactly once, with the own object.
        editor = consumer_actor_for_editor(actor)
        client.force_login(editor)
        response = client.get(reverse(ns.book.vs.get_router_name("detail"), kwargs=kwargs))
        assert response.status_code == 200
        links = [url.split("?", 1)[0] for url in html.fromstring(response.content).xpath("//a/@href")]
        assert update_url in links
        state.assert_called_once()
        assert state.call_args.args[1] is response.context["view"].object


def consumer_actor_for_editor(actor):
    actor.user_permissions.add(Permission.objects.get(codename="change_publisher"))
    return User.objects.get(pk=actor.pk)


@pytest.mark.django_db
@pytest.mark.parametrize("composition", ["core", "guardian"])
def test_alignment_target_levels_holes_and_explicit_parent(composition, monkeypatch):
    with isolated_routes(lambda s: consumer_routes(s, composition)) as ns:
        world = consumer_world()
        actor = consumer_actor(ns, world)
        view = consumer_view(ns.note, "Detail", actor, world)
        book, publisher = view._cv_ancestor_state.objects
        helper = getattr(link_access, "_known_link_ancestors", None)
        assert callable(helper), "the target-alignment helper must exist"
        monkeypatch.setattr(view, "cv_get_parent_object", Mock(side_effect=AssertionError("parent hook consulted")))
        with CaptureQueriesContext(connection) as queries:
            assert helper(ns.note.Detail, view) == (book, publisher)
            assert helper(ns.sibling.List, view) == (book, publisher)
            assert helper(ns.book.Detail, view) == (publisher,)
            assert helper(ns.pub.Detail, view) == ()
            assert helper(ns.note.List, view, immediate_parent=world.book) == (world.book, publisher)
            assert helper(ns.note.List, view, immediate_parent=None) == (None, publisher)
            view._cv_ancestor_state = ancestors._AncestorState((None, publisher))
            assert helper(ns.note.List, view) == (None, publisher)
            view._cv_ancestor_state = ancestors._AncestorState((book, None))
            assert helper(ns.note.List, view) == (book, None)
            del view._cv_ancestor_state
            assert helper(ns.note.List, view) == (None, None)
            assert helper(ns.note.List, view, immediate_parent=book) == (book, None)
        assert len(queries) == 0


@pytest.mark.django_db
def test_alignment_missing_parent_denies_and_configuration_errors_propagate(monkeypatch):
    with isolated_routes(consumer_routes) as ns:
        world = consumer_world()
        actor = consumer_actor(ns, world)
        view = consumer_view(ns.note, "Detail", actor, world, guarded=False)
        own, state = Mock(return_value=True), Mock(return_value=True)
        monkeypatch.setattr(ns.note.Update, "cv_has_access", own)
        monkeypatch.setattr(ns.note.Update, "cv_action_enabled", state)
        data = ContextButton(key="edit", key_target="update").get_context(view.cv_get_view_context(object=world.note))
        assert data["cv_access"] is False
        assert data["cv_action_enabled"] is True  # unevaluated, not a state rejection
        own.assert_not_called()
        state.assert_not_called()
        helper = getattr(link_access, "_known_link_ancestors", None)
        assert callable(helper)
        monkeypatch.setattr(ns.note.vs.parent, "name", "unregistered_ancestor")
        with pytest.raises(ImproperlyConfigured, match="not registered"):
            helper(ns.note.Update, view)


def button_case(ns, world, actor, consumer, *, guarded=True):
    page = consumer_view(ns.book if consumer == "child" else ns.note, "Detail", actor, world, guarded=guarded)
    if consumer == "context":
        target, button = ns.note.Update, ContextButton(key="edit", key_target="update")
    elif consumer == "parent":
        target, button = ns.book.Update, ParentContextButton(key="up", key_target="update")
    elif consumer == "sibling":
        target, button = ns.sibling.List, SiblingContextButton(key="across", sibling_name=ns.sibling.vs.name)
    else:
        target, button = ns.note.List, ChildContextButton(key="down", child_name=ns.note.vs.name)
    return page, target, button


@pytest.mark.django_db
@pytest.mark.parametrize("composition", ["core", "guardian"])
@pytest.mark.parametrize("consumer", ["context", "parent", "sibling", "child"])
@pytest.mark.parametrize("outcome", ["allowed", "ancestor", "own", "state"])
def test_button_order_and_target_identities(composition, consumer, outcome, monkeypatch):
    with isolated_routes(lambda s: consumer_routes(s, composition)) as ns:
        world = consumer_world()
        actor = consumer_actor(ns, world)
        page, target, button = button_case(ns, world, actor, consumer)
        target.cv_viewset.ancestor_policy = AncestorPolicy(
            cascade=True, actions={target.cv_key: AncestorPermissions(nearest="change", higher="change")}
        )
        known = link_access._known_link_ancestors(target, page)
        if consumer == "child":
            known = (world.book, *known[1:])
        expected_own = ancestors._resolved_ancestor(page, ns.book.vs.name) if consumer == "parent" else world.note
        expected_own = expected_own if target.cv_object else None
        events = []
        originals = {cls: cls._ancestor_has_permission for cls in (ViewSet, GuardianViewSet)}
        for cls, original in originals.items():

            def provider(vs, user, permission, obj, *, view, _original=original):
                events.append(("ancestor", vs.name, obj, user))
                return outcome != "ancestor" and _original(vs, user, permission, obj, view=view)

            monkeypatch.setattr(cls, "_ancestor_has_permission", provider)
        own = Mock(side_effect=lambda user, obj: events.append(("own", obj, user)) or outcome != "own")
        state = Mock(side_effect=lambda user, obj: events.append(("state", obj, user)) or outcome != "state")
        monkeypatch.setattr(target, "cv_has_access", own)
        monkeypatch.setattr(target, "cv_action_enabled", state)
        monkeypatch.setattr(page, "cv_get_parent_object", Mock(side_effect=AssertionError("parent lookup")))
        with CaptureQueriesContext(connection) as queries:
            result = button.get_context(page.cv_get_view_context(object=page.object))
        assert result["cv_access"] is (outcome not in {"ancestor", "own"})
        assert result["cv_action_enabled"] is (outcome != "state")
        chain = ancestors._walk_ancestors(target.cv_viewset)
        gates = [
            ("ancestor", ancestor.name, obj, actor)
            for (_, ancestor), obj in reversed(list(zip(chain, known, strict=True)))
        ]
        if outcome == "ancestor":
            assert events == gates[:1]
            own.assert_not_called()
            state.assert_not_called()
        else:
            assert events[: len(gates)] == gates
            own.assert_called_once_with(actor, expected_own)
            assert own.call_args.args[1] is expected_own
            if outcome == "own":
                assert [event[0] for event in events] == ["ancestor"] * len(gates) + ["own"]
                state.assert_not_called()
            else:
                state_obj = expected_own if target.cv_object else known[0]
                state.assert_called_once_with(actor, state_obj)
                assert state.call_args.args[1] is state_obj
                assert [event[0] for event in events] == ["ancestor"] * len(gates) + ["own", "state"]
        for query in queries:
            assert not any(f'from "app_{model}"' in query["sql"].lower() for model in ("publisher", "book", "booknote"))


@pytest.mark.django_db
@pytest.mark.parametrize("consumer", ["context", "parent", "sibling"])
@pytest.mark.parametrize("composition", ["core", "guardian"])
def test_button_unguarded_nested_target_skips_own_and_state(consumer, composition, monkeypatch):
    with isolated_routes(lambda s: consumer_routes(s, composition)) as ns:
        world = consumer_world()
        actor = consumer_actor(ns, world)
        page, target, button = button_case(ns, world, actor, consumer, guarded=False)
        own, state = Mock(return_value=True), Mock(return_value=True)
        monkeypatch.setattr(target, "cv_has_access", own)
        monkeypatch.setattr(target, "cv_action_enabled", state)
        monkeypatch.setattr(page, "cv_get_parent_object", Mock(side_effect=AssertionError("parent lookup")))
        result = button.get_context(page.cv_get_view_context(object=page.object))
        assert result["cv_access"] is False
        assert result["cv_action_enabled"] is True
        own.assert_not_called()
        state.assert_not_called()


@pytest.mark.django_db
@pytest.mark.parametrize("outcome", ["allowed", "own", "state"])
def test_parent_top_level_object_without_guard_preserves_none_contract(outcome, monkeypatch):
    with isolated_routes(consumer_routes) as ns:
        world = consumer_world()
        actor = consumer_actor(ns, world)
        page = consumer_view(ns.book, "Create", actor, world, guarded=False)
        target = ns.pub.Detail
        own, state = Mock(return_value=outcome != "own"), Mock(return_value=outcome != "state")
        monkeypatch.setattr(target, "cv_has_access", own)
        monkeypatch.setattr(target, "cv_action_enabled", state)
        resolver = Mock(side_effect=AssertionError("no parent lookup for a button"))
        monkeypatch.setattr(page, "cv_get_parent_object", resolver)
        result = ParentContextButton(key="parent_detail", key_target="detail").get_context(page.cv_get_view_context())
        assert result["cv_url"] == reverse(ns.pub.vs.get_router_name("detail"), kwargs={"pk": world.pub.pk})
        assert result["cv_access"] is (outcome != "own")
        assert result["cv_action_enabled"] is (outcome != "state")
        own.assert_called_once_with(actor, None)
        if outcome == "own":
            state.assert_not_called()
        else:
            state.assert_called_once_with(actor, None)
        resolver.assert_not_called()


@pytest.mark.django_db
def test_guardian_parent_detail_granted_but_unguarded_denies(
    user_guardian, cv_guardian_publisher, publisher_a, monkeypatch
):
    from tests.lib.helper.guardian import user_guardian_object_perm
    from tests.test1.app.views import GuardianPublisherDetailView
    from tests.test1.test_guardian import _make_book_list_view

    user_guardian_object_perm(user_guardian, cv_guardian_publisher, "view", publisher_a)
    page = _make_book_list_view(user_guardian, publisher_a)
    state = Mock(return_value=True)
    monkeypatch.setattr(GuardianPublisherDetailView, "cv_action_enabled", state)
    result = page.cv_get_context("publisher_detail", obj=None, user=user_guardian)
    assert result["cv_access"] is False
    state.assert_not_called()


@pytest.mark.django_db
@pytest.mark.parametrize("key", ["update", "delete", "create"])
def test_default_parent_view_without_change_hides_write_button_and_request(key, monkeypatch):
    with isolated_routes(consumer_routes) as ns:
        world = consumer_world()
        actor = consumer_actor(ns, world)
        actor.user_permissions.remove(Permission.objects.get(codename="change_publisher"))
        actor = User.objects.get(pk=actor.pk)
        page = consumer_view(ns.book, "Detail", actor, world)
        target = ns.book.vs.get_view_class(key)
        state = Mock(return_value=True)
        monkeypatch.setattr(target, "cv_action_enabled", state)
        result = ContextButton(key="write", key_target=key).get_context(page.cv_get_view_context(object=world.book))
        assert result["cv_access"] is False
        state.assert_not_called()
        client = Client()
        client.force_login(actor)
        assert client.get(result["cv_url"]).status_code == 403
        state.assert_not_called()


@pytest.mark.django_db
@pytest.mark.parametrize("consumer", ["context", "parent", "sibling", "child"])
def test_guardian_create_buttons_keep_seam_and_rendering_view_identity(consumer, monkeypatch):
    with isolated_routes(lambda s: consumer_routes(s, "guardian")) as ns:
        world = consumer_world()
        actor = consumer_actor(ns, world)
        page = consumer_view(ns.book if consumer == "child" else ns.note, "Detail", actor, world)
        if consumer == "context":
            target, button = ns.note.Create, ContextButton(key="new", key_target="create")
        elif consumer == "parent":
            target, button = ns.book.Create, ParentContextButton(key="up", key_target="create")
        elif consumer == "sibling":
            target, button = (
                ns.sibling.Create,
                SiblingContextButton(key="across", sibling_name=ns.sibling.vs.name, sibling_key="create"),
            )
        else:
            target, button = (
                ns.note.Create,
                ChildContextButton(key="down", child_name=ns.note.vs.name, child_key="create"),
            )
        create = Mock(wraps=target.cv_create_has_access)
        state = Mock(return_value=True)
        monkeypatch.setattr(target, "cv_create_has_access", create)
        monkeypatch.setattr(target, "cv_action_enabled", state)
        result = button.get_context(page.cv_get_view_context(object=page.object))
        if consumer == "sibling":
            assert result["cv_access"] is False  # The retained seam's () stays authoritative.
            create.assert_not_called()
            state.assert_not_called()
        else:
            parent = (
                world.book if consumer == "child" else ancestors._resolved_ancestor(page, target.cv_viewset.parent.name)
            )
            assert result["cv_access"] is True
            create.assert_called_once_with(actor, page if consumer == "context" else None, parent)
            assert create.call_args.args[2] is parent
            state.assert_called_once_with(actor, parent)


@pytest.mark.django_db
def test_core_create_button_uses_guard_parent_instead_of_hook_or_child_fk(monkeypatch):
    from tests.test1.app.models import Book, Publisher

    with isolated_routes(consumer_routes) as ns:
        world = consumer_world()
        actor = consumer_actor(ns, world)
        page = consumer_view(ns.book, "Detail", actor, world)
        different = Publisher.objects.create(name="Wrong FK")
        mismatched = Book(pk=world.book.pk, title="Own child", publisher=different)
        monkeypatch.setattr(page, "cv_get_parent_object", Mock(side_effect=AssertionError("overridden parent hook")))
        state = Mock(return_value=True)
        monkeypatch.setattr(ns.book.Create, "cv_action_enabled", state)
        result = ContextButton(key="new", key_target="create").get_context(page.cv_get_view_context(object=mismatched))
        assert result["cv_access"] is True
        state.assert_called_once_with(actor, page._cv_ancestor_state.parent)
        assert state.call_args.args[1] is page._cv_ancestor_state.parent
        assert state.call_args.args[1] is not different


@pytest.mark.django_db
def test_child_button_keeps_unknown_higher_level_and_url_parent(monkeypatch):
    with isolated_routes(lambda s: consumer_routes(s, "guardian")) as ns:
        world = consumer_world()
        actor = consumer_actor(ns, world)
        page = consumer_view(ns.book, "Detail", actor, world)
        page._cv_ancestor_state = ancestors._AncestorState((None,))
        state = Mock(return_value=True)
        monkeypatch.setattr(ns.note.List, "cv_action_enabled", state)
        result = ChildContextButton(key="notes", child_name=ns.note.vs.name).get_context(
            page.cv_get_view_context(object=world.book)
        )
        assert result["cv_access"] is True
        state.assert_called_once_with(actor, world.book)
        assert state.call_args.args[1] is world.book


@pytest.mark.django_db
@pytest.mark.parametrize("shape", ["create", "form", "non-crud", "resource", "direct"])
def test_context_without_guard_on_reachable_shapes_denies(shape, monkeypatch):
    from types import SimpleNamespace

    from django.views.generic import TemplateView

    from crud_views.lib.resource import ResourceViewMixin
    from crud_views.lib.view import CrudView
    from crud_views.lib.views import DetailView, ListView
    from crud_views.lib.viewset import ParentViewSet
    from tests.test1.test_ancestor_helpers import _bound
    from tests.test1.test_ancestor_resources import TopFile

    def build(suffix):
        ns, routed = consumer_routes(suffix)
        ns.Report = type(
            "ConsumerReport",
            (CrudView, TemplateView),
            {
                "cv_viewset": ns.book.vs,
                "cv_key": "report",
                "cv_path": "report",
                "cv_object": False,
            },
        )
        resource_vs = ViewSet(model=TopFile, name=f"consumerfile{suffix}", parent=ParentViewSet(name=ns.pub.vs.name))
        ns.Resource = type("ConsumerResource", (ResourceViewMixin, DetailView), {"cv_viewset": resource_vs})
        ns.ResourceList = type("ConsumerResourceList", (ResourceViewMixin, ListView), {"cv_viewset": resource_vs})
        return ns, [*routed, resource_vs]

    with isolated_routes(build) as ns:
        world = consumer_world()
        actor = consumer_actor(ns, world)
        source = {
            "create": ns.book.Create,
            "form": ns.book.Bulk,
            "non-crud": ns.Report,
            "resource": ns.Resource,
            "direct": ns.book.Detail,
        }[shape]
        target = ns.ResourceList if shape == "resource" else ns.book.List
        kwargs = {source.cv_viewset.parent.get_pk_name(): world.pub.pk}
        obj = TopFile(key="known-file") if shape == "resource" else world.book if shape == "direct" else None
        if obj is not None:
            kwargs["pk"] = obj.pk
        page = _bound(source, actor, **kwargs)
        page.request.resolver_match = SimpleNamespace(url_name=source.cv_viewset.get_router_name(source.cv_key))
        own, state = Mock(return_value=True), Mock(return_value=True)
        monkeypatch.setattr(target, "cv_has_access", own)
        monkeypatch.setattr(target, "cv_action_enabled", state)
        monkeypatch.setattr(page, "cv_get_parent_object", Mock(side_effect=AssertionError("button parent lookup")))
        with CaptureQueriesContext(connection) as queries:
            result = ContextButton(key="home", key_target="list").get_context(page.cv_get_view_context(object=obj))
        assert result["cv_access"] is False
        assert result["cv_action_enabled"] is True
        own.assert_not_called()
        state.assert_not_called()
        assert len(queries) == 0


@pytest.mark.django_db
@pytest.mark.parametrize("protected_higher", [False, True])
def test_guardian_child_create_anonymous_denied_with_or_without_higher_gate(protected_higher, monkeypatch):
    from django.contrib.auth.models import AnonymousUser

    with isolated_routes(lambda s: consumer_routes(s, "guardian")) as ns:
        world = consumer_world()
        actor = consumer_actor(ns, world)
        page = consumer_view(ns.book, "Detail", actor, world)
        ns.book.vs.ancestor_policy = AncestorPolicy(provider="none")
        ns.pub.vs.ancestor_policy = AncestorPolicy(provider="guardian" if protected_higher else "none")
        page.request.user = AnonymousUser()
        create = Mock(wraps=ns.note.Create.cv_create_has_access)
        state = Mock(return_value=True)
        monkeypatch.setattr(ns.note.Create, "cv_create_has_access", create)
        monkeypatch.setattr(ns.note.Create, "cv_action_enabled", state)
        result = ChildContextButton(key="new", child_name=ns.note.vs.name, child_key="create").get_context(
            page.cv_get_view_context(object=world.book)
        )
        assert result["cv_access"] is False
        create.assert_not_called()
        state.assert_not_called()


@pytest.mark.django_db
@pytest.mark.parametrize("composition", ["core", "guardian"])
@pytest.mark.parametrize("surface", ["view_key", "table_row"])
@pytest.mark.parametrize("key", ["update", "list"])
@pytest.mark.parametrize("outcome", ["allowed", "ancestor", "own", "state"])
def test_view_key_and_table_row_order(composition, surface, key, outcome, monkeypatch):
    """Each surface checks the actual target's stricter far gate before own permission/state."""
    with isolated_routes(lambda s: consumer_routes(s, composition)) as ns:
        world = consumer_world()
        actor = consumer_actor(ns, world)
        page = consumer_view(ns.note, "Detail" if surface == "view_key" else "List", actor, world)
        target = ns.note.vs.get_view_class(key)
        ns.note.vs.ancestor_policy = AncestorPolicy(
            cascade=True, actions={key: AncestorPermissions(nearest="change", higher="change")}
        )
        book, publisher = page._cv_ancestor_state.objects
        events = []
        provider_cls = GuardianViewSet if composition == "guardian" else ViewSet
        original = provider_cls._ancestor_has_permission

        def provider(vs, user, permission, obj, *, view):
            events.append(("gate", vs.name, obj, permission))
            return outcome != "ancestor" and original(vs, user, permission, obj, view=view)

        monkeypatch.setattr(provider_cls, "_ancestor_has_permission", provider)
        own = Mock(side_effect=lambda user, obj: events.append(("own", obj)) or outcome != "own")
        state = Mock(side_effect=lambda user, obj: events.append(("state", obj)) or outcome != "state")
        monkeypatch.setattr(target, "cv_has_access", own)
        monkeypatch.setattr(target, "cv_action_enabled", state)
        monkeypatch.setattr(page, "cv_get_parent_object", Mock(side_effect=AssertionError("parent hook")))
        with CaptureQueriesContext(connection) as queries:
            result = page.cv_get_context(
                key, obj=world.note, user=actor, location="context" if surface == "view_key" else "list"
            )
        assert result["cv_access"] is (outcome not in {"ancestor", "own"})
        assert result["cv_action_enabled"] is (outcome != "state")
        gates = [
            ("gate", ns.pub.vs.name, publisher, ns.pub.vs.permissions["change"]),
            ("gate", ns.book.vs.name, book, ns.book.vs.permissions["change"]),
        ]
        if outcome == "ancestor":
            assert events == gates[:1]
            own.assert_not_called()
            state.assert_not_called()
        else:
            own_obj = world.note if key == "update" else None
            assert events[:2] == gates
            own.assert_called_once_with(actor, own_obj)
            assert own.call_args.args[1] is own_obj
            if outcome == "own":
                assert events[2:] == [("own", own_obj)]
                state.assert_not_called()
            else:
                state_obj = world.note if key == "update" else book
                assert events[2:] == [("own", own_obj), ("state", state_obj)]
                assert state.call_args.args[1] is state_obj
        assert not any(
            f'from "app_{model}"' in query["sql"].lower()
            for query in queries
            for model in ("publisher", "book", "booknote")
        )


@pytest.mark.django_db
@pytest.mark.parametrize("surface", ["view_key", "table_row"])
@pytest.mark.parametrize("key", ["update", "delete", "create"])
def test_view_key_table_row_rendered_default_parent_denial(surface, key, monkeypatch):
    from django.template import RequestContext, Template
    from django.template.loader import render_to_string

    with isolated_routes(consumer_routes) as ns:
        world = consumer_world()
        actor = consumer_actor(ns, world)
        actor.user_permissions.remove(Permission.objects.get(codename="change_publisher"))
        actor = User.objects.get(pk=actor.pk)
        page = consumer_view(ns.book, "Detail" if surface == "view_key" else "List", actor, world)
        target = ns.book.vs.get_view_class(key)
        state = Mock(return_value=True)
        monkeypatch.setattr(target, "cv_action_enabled", state)
        page.cv_context_actions = [key, "list"]
        page.cv_list_actions = [key, "detail"]

        def rendered():
            context = {"view": page, "record": world.book, "object": world.book}
            if surface == "table_row":
                return render_to_string("crud_views/columns/actions.html", context, page.request)
            return Template("{% load crud_views %}{% cv_context_actions object %}").render(
                RequestContext(page.request, context)
            )

        target_url = page.cv_get_url(key, obj=world.book).split("?", 1)[0]
        markup = rendered()
        assert target_url not in markup
        state.assert_not_called()
        client = Client()
        client.force_login(actor)
        assert client.get(target_url).status_code == 403
        state.assert_not_called()
        page.request.user = consumer_actor_for_editor(actor)
        assert target_url in rendered()
        state.assert_called_once()
        expected = world.book if target.cv_object else page._cv_ancestor_state.parent
        assert state.call_args.args[1] is expected


@pytest.mark.django_db
@pytest.mark.parametrize("actor_input", ["omitted", "none", "allowed", "denied"])
def test_view_key_direct_actor_is_explicit(actor_input, monkeypatch):
    from tests.test1.test_ancestor_authorization import _user

    with isolated_routes(consumer_routes) as ns:
        world = consumer_world()
        actor = consumer_actor(ns, world)
        page = consumer_view(ns.note, "Detail", actor, world)
        state = Mock(return_value=True)
        monkeypatch.setattr(ns.note.Update, "cv_action_enabled", state)
        denied = _user("denied_view_key")
        kwargs = (
            {}
            if actor_input == "omitted"
            else {"user": {"none": None, "allowed": actor, "denied": denied}[actor_input]}
        )
        if actor_input in {"omitted", "none"}:
            with pytest.raises(AttributeError, match="is_authenticated"):
                page.cv_get_context("update", obj=world.note, **kwargs)
            state.assert_not_called()
        else:
            result = page.cv_get_context("update", obj=world.note, **kwargs)
            assert result["cv_access"] is (actor_input == "allowed")
            if actor_input == "allowed":
                state.assert_called_once_with(actor, world.note)
            else:
                state.assert_not_called()
        assert page.request.user is actor


@pytest.mark.django_db
@pytest.mark.parametrize("case", ["guardian_unguarded_list_view_key", "guardian_guarded_list_view_key"])
def test_guardian_list_view_key_requires_guard(case, user_guardian, cv_guardian_publisher, publisher_a, monkeypatch):
    from tests.lib.helper.guardian import user_guardian_object_perm
    from tests.test1.app.views import GuardianBookCreateView, GuardianBookListView
    from tests.test1.test_guardian import _make_book_list_view

    guarded = case == "guardian_guarded_list_view_key"
    user_guardian_object_perm(user_guardian, cv_guardian_publisher, "view", publisher_a)
    page = _make_book_list_view(user_guardian, publisher_a, guarded=guarded)
    own = Mock(wraps=GuardianBookListView.cv_has_access)
    state = Mock(return_value=True)
    create = Mock(side_effect=AssertionError("non-create must not use rewrite"))
    monkeypatch.setattr(GuardianBookListView, "cv_has_access", own)
    monkeypatch.setattr(GuardianBookListView, "cv_action_enabled", state)
    monkeypatch.setattr(GuardianBookCreateView, "cv_create_has_access", create)
    result = page.cv_get_context("list", obj=None, user=user_guardian)
    assert result["cv_access"] is guarded
    if guarded:
        own.assert_called_once_with(user_guardian, None)
        state.assert_called_once_with(user_guardian, page._cv_ancestor_state.parent)
    else:
        own.assert_not_called()
        state.assert_not_called()
    create.assert_not_called()


@pytest.mark.django_db
@pytest.mark.parametrize("problem", ["ancestry", "permission", "operation", "auth_database"])
def test_view_key_configuration_errors_remain_observable(problem, monkeypatch):
    with isolated_routes(consumer_routes) as ns:
        world = consumer_world()
        actor = consumer_actor(ns, world)
        page = consumer_view(ns.note, "Detail", actor, world)
        assert page.cv_get_context("not_registered", obj=world.note, user=actor) == {}
        own, state = Mock(return_value=True), Mock(return_value=True)
        monkeypatch.setattr(ns.note.Update, "cv_has_access", own)
        monkeypatch.setattr(ns.note.Update, "cv_action_enabled", state)
        if problem == "ancestry":
            monkeypatch.setattr(ns.note.vs.parent, "name", "not_registered")
        elif problem == "permission":
            ns.note.vs.ancestor_policy = AncestorPolicy(
                cascade=True, actions={"update": AncestorPermissions(nearest="missing", higher="view")}
            )
        elif problem == "operation":
            # An unrecognized operation marker reaches the existing configuration error.
            monkeypatch.setattr(ns.note.Update, "_cv_ancestor_operation", "unmapped", raising=False)
        else:
            monkeypatch.setattr(actor._state, "db", "other")
        with pytest.raises(ImproperlyConfigured):
            page.cv_get_context("update", obj=world.note, user=actor)
        own.assert_not_called()
        state.assert_not_called()


@pytest.mark.django_db
@pytest.mark.parametrize("composition", ["core", "guardian"])
@pytest.mark.parametrize("consumer,key", [("own", "update"), ("own", "list"), ("child", "list")])
@pytest.mark.parametrize("outcome", ["allowed", "ancestor", "own", "state"])
def test_card_actions_order_and_row_identity(composition, consumer, key, outcome, monkeypatch):
    from crud_views.lib.view import CardAction
    from tests.test1.app.models import Book, BookNote

    with isolated_routes(lambda s: consumer_routes(s, composition)) as ns:
        world = consumer_world()
        actor = consumer_actor(ns, world)
        page = consumer_view(ns.note if consumer == "own" else ns.book, "Card", actor, world)
        row = world.note if consumer == "own" else world.book
        # The row, not the page-level object or its relation, supplies the URL parent/own object.
        page.object = (
            BookNote(book=Book(), note="Different page") if consumer == "own" else Book(title="Different page")
        )
        target = ns.note.vs.get_view_class(key)
        ns.note.vs.ancestor_policy = AncestorPolicy(
            cascade=True, actions={key: AncestorPermissions(nearest="change", higher="change")}
        )
        book = page._cv_ancestor_state.parent if consumer == "own" else row
        publisher = ancestors._resolved_ancestor(page, ns.pub.vs.name)
        events = []
        provider_cls = GuardianViewSet if composition == "guardian" else ViewSet
        original = provider_cls._ancestor_has_permission

        def provider(vs, user, permission, obj, *, view):
            events.append(("gate", vs.name, obj))
            return outcome != "ancestor" and original(vs, user, permission, obj, view=view)

        monkeypatch.setattr(provider_cls, "_ancestor_has_permission", provider)
        own = Mock(side_effect=lambda user, obj: events.append(("own", obj)) or outcome != "own")
        state = Mock(side_effect=lambda user, obj: events.append(("state", obj)) or outcome != "state")
        monkeypatch.setattr(target, "cv_has_access", own)
        monkeypatch.setattr(target, "cv_action_enabled", state)
        monkeypatch.setattr(page, "cv_get_parent_object", Mock(side_effect=AssertionError("card parent hook")))
        options = {"key": key} if consumer == "own" else {"child_name": ns.note.vs.name, "child_key": key}
        action = CardAction(**options, label="Target action", variant="warning", flex=True, label_mode="both")
        with CaptureQueriesContext(connection) as queries:
            result = page.cv_get_card_action_data(action, row, actor)
        assert result["cv_access"] is (outcome not in {"ancestor", "own"})
        assert result["cv_action_enabled"] is (outcome != "state")
        assert result["cv_label"] == "Target action"
        assert result["cv_variant"] == "warning"
        assert result["cv_flex"] is True
        assert result["cv_label_mode"] == "both"
        assert result["cv_icon_action"] == target.cv_icon_action
        assert result["cv_list_action_method"] == "get"
        expected_url = (
            page.cv_get_link_url(target, key, row)
            if consumer == "own"
            else page.cv_get_child_url(ns.note.vs.name, key, row)
        )
        assert result["cv_url"] == expected_url
        if consumer == "own":
            assert result["cv_oid"] == page.cv_get_oid(key, obj=row)
        gates = [("gate", ns.pub.vs.name, publisher), ("gate", ns.book.vs.name, book)]
        own_obj = row if target.cv_object else None
        if outcome == "ancestor":
            assert events == gates[:1]
            own.assert_not_called()
            state.assert_not_called()
        else:
            assert events[:2] == gates
            own.assert_called_once_with(actor, own_obj)
            assert own.call_args.args[1] is own_obj
            if outcome == "own":
                assert events[2:] == [("own", own_obj)]
                state.assert_not_called()
            else:
                state_obj = row if target.cv_object else book
                assert events[2:] == [("own", own_obj), ("state", state_obj)]
                assert state.call_args.args[1] is state_obj
        assert not any(
            f'from "app_{model}"' in query["sql"].lower()
            for query in queries
            for model in ("publisher", "book", "booknote")
        )


@pytest.mark.django_db
@pytest.mark.parametrize("composition", ["core", "guardian"])
@pytest.mark.parametrize("consumer", ["own", "child"])
@pytest.mark.parametrize("far_allowed", [True, False])
def test_card_create_seam_and_rendering_view(composition, consumer, far_allowed, monkeypatch):
    from guardian.shortcuts import remove_perm

    from crud_views.lib.view import CardAction

    with isolated_routes(lambda s: consumer_routes(s, composition)) as ns:
        world = consumer_world()
        actor = consumer_actor(ns, world)
        if not far_allowed:
            actor.user_permissions.remove(Permission.objects.get(codename="change_publisher"))
            if composition == "guardian":
                remove_perm(ns.pub.vs.permissions["change"], actor, world.pub)
            actor = User.objects.get(pk=actor.pk)
        page = consumer_view(ns.note if consumer == "own" else ns.book, "Card", actor, world)
        target = ns.note.Create
        ns.note.vs.ancestor_policy = AncestorPolicy(
            cascade=True, actions={"create": AncestorPermissions(nearest="change", higher="change")}
        )
        row = world.note if consumer == "own" else world.book
        action = (
            CardAction(key="create")
            if consumer == "own"
            else CardAction(child_name=ns.note.vs.name, child_key="create")
        )
        state = Mock(return_value=True)
        monkeypatch.setattr(target, "cv_action_enabled", state)
        monkeypatch.setattr(page, "cv_get_parent_object", Mock(side_effect=AssertionError("card parent hook")))
        # The create hook exists on Guardian; core still uses its regular own permission.
        create = Mock(wraps=target.cv_create_has_access) if composition == "guardian" else None
        if create is not None:
            monkeypatch.setattr(target, "cv_create_has_access", create)
        result = page.cv_get_card_action_data(action, row, actor)
        permitted = far_allowed or (composition == "guardian" and consumer == "own")
        assert result["cv_access"] is permitted
        if permitted:
            parent = page._cv_ancestor_state.parent if consumer == "own" else row
            state.assert_called_once_with(actor, parent)
            assert state.call_args.args[1] is parent
            if create is not None:
                create.assert_called_once_with(actor, page if consumer == "own" else None, parent)
        else:
            state.assert_not_called()
            if create is not None:
                create.assert_not_called()


@pytest.mark.django_db
@pytest.mark.parametrize("reason", ["unguarded", "permission"])
@pytest.mark.parametrize("composition", ["core", "guardian"])
def test_own_card_create_denied_skips_state(composition, reason, monkeypatch):
    from crud_views.lib.view import CardAction
    from tests.test1.test_ancestor_authorization import _user

    with isolated_routes(lambda s: consumer_routes(s, composition)) as ns:
        world = consumer_world()
        actor = consumer_actor(ns, world)
        page = consumer_view(ns.note, "Card", actor, world, guarded=reason != "unguarded")
        if reason == "permission":
            actor = _user("denied_card")
        state = Mock(return_value=True)
        monkeypatch.setattr(ns.note.Create, "cv_action_enabled", state)
        result = page.cv_get_card_action_data(CardAction(key="create"), world.note, actor)
        assert result["cv_access"] is False
        assert result["cv_action_enabled"] is True
        state.assert_not_called()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "nested,key", [(False, "detail"), (False, "list"), (True, "detail"), (True, "list"), (True, "create")]
)
@pytest.mark.parametrize("surface", ["view_key", "card"])
def test_action_object_follows_request_definition(nested, key, surface, monkeypatch):
    from crud_views.lib.view import CardAction

    with isolated_routes(consumer_routes) as ns:
        world = consumer_world()
        actor = consumer_actor(ns, world)
        family, row = (ns.book, world.book) if nested else (ns.pub, world.pub)
        page = consumer_view(family, "Card", actor, world)
        target = family.vs.get_view_class(key)
        state = Mock(return_value=True)
        monkeypatch.setattr(target, "cv_action_enabled", state)
        result = (
            page.cv_get_context(key, obj=row, user=actor)
            if surface == "view_key"
            else page.cv_get_card_action_data(CardAction(key=key), row, actor)
        )
        assert result["cv_access"] is True
        expected = row if target.cv_object else page._cv_ancestor_state.parent if nested else None
        state.assert_called_once_with(actor, expected)
        assert state.call_args.args[1] is expected


@pytest.mark.django_db
@pytest.mark.parametrize("composition", ["core", "guardian"])
@pytest.mark.parametrize(
    "surface,key",
    [
        ("view_key", "update"),
        ("view_key", "list"),
        ("table_row", "update"),
        ("table_row", "list"),
        ("card-own", "update"),
        ("card-own", "list"),
        ("card-child", "list"),
    ],
)
def test_view_key_table_row_card_real_far_denial_matches_request(composition, surface, key, monkeypatch):
    from guardian.shortcuts import remove_perm

    from crud_views.lib.view import CardAction

    with isolated_routes(lambda s: consumer_routes(s, composition)) as ns:
        world = consumer_world()
        actor = consumer_actor(ns, world)
        actor.user_permissions.remove(Permission.objects.get(codename="change_publisher"))
        if composition == "guardian":
            remove_perm(ns.pub.vs.permissions["change"], actor, world.pub)
        actor = User.objects.get(pk=actor.pk)
        # Target-specific far write permission is stricter than either source page's Read policy.
        ns.note.vs.ancestor_policy = AncestorPolicy(
            cascade=True, actions={key: AncestorPermissions(nearest="view", higher="change")}
        )
        page = consumer_view(
            ns.book if surface == "card-child" else ns.note,
            "Detail" if surface == "view_key" else "Card",
            actor,
            world,
        )
        target = ns.note.vs.get_view_class(key)
        state = Mock(return_value=True)
        monkeypatch.setattr(target, "cv_action_enabled", state)
        if surface.startswith("card"):
            action = (
                CardAction(child_name=ns.note.vs.name, child_key=key)
                if surface == "card-child"
                else CardAction(key=key)
            )
            result = page.cv_get_card_action_data(action, world.book if surface == "card-child" else world.note, actor)
        else:
            result = page.cv_get_context(
                key, obj=world.note, user=actor, location="list" if surface == "table_row" else "context"
            )
        assert result["cv_access"] is False
        assert result["cv_action_enabled"] is True
        state.assert_not_called()
        client = Client()
        client.force_login(actor)
        assert client.get(result["cv_url"]).status_code == 403
        state.assert_not_called()
