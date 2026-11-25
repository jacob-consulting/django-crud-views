"""Cancel shares declared gates while preserving its parent hook and parent-only exception."""

from copy import copy
from unittest.mock import Mock

import pytest
from django.contrib.auth.models import Permission, User
from django.db import DatabaseError, connection
from django.http import Http404, HttpResponse
from django.test import Client, RequestFactory
from django.test.utils import CaptureQueriesContext
from guardian.shortcuts import remove_perm

from crud_views.lib.view import ContextButton
from crud_views.lib.views import ListViewPermissionRequired
from crud_views.lib.views.form import CustomFormNoObjectView, CustomFormNoObjectViewPermissionRequired
from crud_views.lib.viewset import AncestorPermissions, AncestorPolicy, ViewSet
from crud_views.templatetags.crud_views import cv_context_has_permission
from crud_views_guardian.lib.mixins import GuardianParentPermissionMixin, GuardianQuerysetMixin
from crud_views_guardian.lib.viewset import GuardianViewSet
from tests.test1.test_ancestor_authorization import isolated_routes
from tests.test1.test_link_consumer_costs import consumer_actor, consumer_routes, consumer_view, consumer_world


@pytest.mark.django_db
@pytest.mark.parametrize("key", ["detail", "list"])
@pytest.mark.parametrize("guarded", [False, True])
@pytest.mark.parametrize("composition", ["core", "guardian"])
def test_cancel_parent_lookup_and_object_identity(key, guarded, composition, monkeypatch):
    with isolated_routes(lambda suffix: consumer_routes(suffix, composition)) as ns:
        world = consumer_world()
        actor = consumer_actor(ns, world)
        page = consumer_view(ns.note, "Update", actor, world, guarded=guarded)
        page.cv_cancel_key = key
        target = ns.note.vs.get_view_class(key)
        own, state = Mock(return_value=True), Mock(return_value=True)
        monkeypatch.setattr(target, "cv_has_access", own)
        monkeypatch.setattr(target, "cv_action_enabled", state)
        gates = []
        provider = GuardianViewSet if composition == "guardian" else ViewSet
        original = provider._ancestor_has_permission

        def gate(vs, user, permission, obj, *, view):
            gates.append((vs.name, obj))
            return original(vs, user, permission, obj, view=view)

        monkeypatch.setattr(provider, "_ancestor_has_permission", gate)
        with CaptureQueriesContext(connection) as queries:
            assert page.cv_get_cancel_url() == page.cv_get_url(key, obj=world.note)
        parent = gates[-1][1]
        assert parent.pk == world.book.pk
        if guarded:
            assert parent is page._cv_ancestor_state.parent
            assert gates == [(ns.pub.vs.name, page._cv_ancestor_state.objects[1]), (ns.book.vs.name, parent)]
        else:
            assert gates == [(ns.book.vs.name, parent)]  # No higher object is fetched.
        domain_sql = [
            query["sql"]
            for query in queries
            if any(f'from "app_{model}"' in query["sql"].lower() for model in ("publisher", "book", "booknote"))
        ]
        assert len(domain_sql) == (0 if guarded else 1)
        if not guarded:
            assert 'FROM "app_book"' in domain_sql[0]
        own_obj = world.note if target.cv_object else None
        own.assert_called_once_with(actor, own_obj)
        assert own.call_args.args[1] is own_obj
        state.assert_called_once_with(actor, world.note if target.cv_object else parent)
        assert state.call_args.args[1] is (world.note if target.cv_object else parent)


@pytest.mark.django_db
@pytest.mark.parametrize("key", ["detail", "list"])
def test_core_cancel_custom_parent_and_request_bound_owner(key, monkeypatch):
    with isolated_routes(consumer_routes) as ns:
        world = consumer_world()
        actor = consumer_actor(ns, world)
        page = consumer_view(ns.note, "Update", actor, world)
        page.cv_cancel_key = key
        override = RequestFactory().get("/")
        override.user = User.objects.get(pk=actor.pk)
        annotated = copy(world.book)
        annotated.cancel_annotation = "project parent"
        owners = []

        def parent_hook(owner):
            owners.append(owner)
            assert owner.request is override
            return annotated

        monkeypatch.setattr(ns.note.Update, "cv_get_parent_object", parent_hook)
        target = ns.note.vs.get_view_class(key)
        step = Mock(wraps=target._cv_link_permission)
        own, state = Mock(return_value=True), Mock(return_value=True)
        monkeypatch.setattr(target, "_cv_link_permission", step)
        monkeypatch.setattr(target, "cv_has_access", own)
        monkeypatch.setattr(target, "cv_action_enabled", state)
        gates = []
        original = ViewSet._ancestor_has_permission

        def gate(vs, user, permission, obj, *, view):
            gates.append((vs.name, obj, user))
            return original(vs, user, permission, obj, view=view)

        monkeypatch.setattr(ViewSet, "_ancestor_has_permission", gate)
        assert page.cv_get_cancel_url(request=override) == page.cv_get_url(key, obj=world.note)
        assert len(owners) == 1
        owner = owners[0]
        assert owner is not page and type(owner) is type(page)
        assert owner.object is world.note and owner._cv_ancestor_state is page._cv_ancestor_state
        assert page.request.user is actor and page.request is not override
        own_obj = world.note if target.cv_object else None
        step.assert_called_once_with(override.user, own_obj, annotated, rendering_view=owner)
        assert step.call_args.kwargs["rendering_view"] is owner
        assert gates[-1] == (ns.book.vs.name, annotated, override.user)
        assert gates[-1][1] is annotated and gates[-1][2] is override.user
        own.assert_called_once_with(override.user, own_obj)
        state.assert_called_once_with(override.user, world.note if target.cv_object else annotated)
        assert state.call_args.args[1] is (world.note if target.cv_object else annotated)


@pytest.mark.django_db
@pytest.mark.parametrize("key", ["detail", "list"])
@pytest.mark.parametrize("composition", ["core", "guardian"])
def test_cancel_missing_builtin_parent_is_unavailable(key, composition, monkeypatch):
    with isolated_routes(lambda suffix: consumer_routes(suffix, composition)) as ns:
        world = consumer_world()
        actor = consumer_actor(ns, world)
        page = consumer_view(ns.note, "Update", actor, world, guarded=False)
        page.cv_cancel_key = key
        page.kwargs[ns.note.vs.parent.get_pk_name()] = 999999
        target = ns.note.vs.get_view_class(key)
        own, state = Mock(return_value=True), Mock(return_value=True)
        monkeypatch.setattr(target, "cv_has_access", own)
        monkeypatch.setattr(target, "cv_action_enabled", state)
        assert page.cv_get_cancel_url() is None
        own.assert_not_called()
        state.assert_not_called()
        client = Client()
        client.force_login(actor)
        assert client.get(page.cv_get_url(key, obj=world.note)).status_code == 404
        own.assert_not_called()
        state.assert_not_called()


@pytest.mark.django_db
@pytest.mark.parametrize("key", ["detail", "list"])
@pytest.mark.parametrize("error", [Http404, KeyError, DatabaseError])
@pytest.mark.parametrize("composition", ["core", "guardian"])
def test_cancel_custom_parent_errors_reach_both_target_shapes(key, error, composition, monkeypatch):
    with isolated_routes(lambda suffix: consumer_routes(suffix, composition)) as ns:
        world = consumer_world()
        actor = consumer_actor(ns, world)
        page = consumer_view(ns.note, "Update", actor, world)
        page.cv_cancel_key = key
        monkeypatch.setattr(ns.note.Update, "cv_get_parent_object", Mock(side_effect=error("project parent")))
        with pytest.raises(error, match="project parent"):
            page.cv_get_cancel_url()


@pytest.mark.django_db
@pytest.mark.parametrize("key", ["update", "list"])
@pytest.mark.parametrize("denial", [None, "nearest", "higher"])
def test_core_cancel_real_target_gates_match_request(key, denial, monkeypatch):
    with isolated_routes(consumer_routes) as ns:
        world = consumer_world()
        actor = consumer_actor(ns, world)
        if denial:
            model = "book" if denial == "nearest" else "publisher"
            actor.user_permissions.remove(Permission.objects.get(codename=f"change_{model}"))
            actor = User.objects.get(pk=actor.pk)
        page = consumer_view(ns.note, "Detail", actor, world)
        page.cv_cancel_key = key
        ns.note.vs.ancestor_policy = AncestorPolicy(
            cascade=True, actions={key: AncestorPermissions(nearest="change", higher="change")}
        )
        target = ns.note.vs.get_view_class(key)
        state = Mock(return_value=True)
        monkeypatch.setattr(target, "cv_action_enabled", state)
        destination = page.cv_get_url(key, obj=world.note)
        assert page.cv_get_cancel_url() == (destination if denial is None else None)
        if denial:
            state.assert_not_called()
        else:
            state.assert_called_once_with(actor, world.note if target.cv_object else page._cv_ancestor_state.parent)
        state.reset_mock()
        client = Client()
        client.force_login(actor)
        assert client.get(page.cv_get_url("detail", obj=world.note)).status_code == 200
        assert client.get(destination).status_code == (200 if denial is None else 403)
        if denial:
            state.assert_not_called()


@pytest.mark.django_db
@pytest.mark.parametrize("page_key", ["Create", "Bulk"])
def test_no_guard_create_and_form_deny_other_links_but_cancel_resolves_parent(page_key, monkeypatch):
    with isolated_routes(consumer_routes) as ns:
        world = consumer_world()
        actor = consumer_actor(ns, world)
        page = consumer_view(ns.note, page_key, actor, world, guarded=False)
        page.cv_cancel_key = "list"
        state = Mock(return_value=True)
        monkeypatch.setattr(ns.note.List, "cv_action_enabled", state)
        assert cv_context_has_permission(page, "list") is False
        assert (
            ContextButton(key="list", key_target="list").get_context(page.cv_get_view_context())["cv_access"] is False
        )
        state.assert_not_called()
        with CaptureQueriesContext(connection) as queries:
            assert page.cv_get_cancel_url() == page.cv_get_url("list")
        state.assert_called_once()
        assert state.call_args.args[1].pk == world.book.pk
        assert sum('FROM "app_book"' in query["sql"] for query in queries) == 1
        assert not any('FROM "app_publisher"' in query["sql"] for query in queries)


def guardian_cancel_routes(suffix):
    ns, families = consumer_routes(suffix, "guardian")
    ns.note.QuerysetOnly = type(
        "CancelQuerysetOnly",
        (GuardianQuerysetMixin, ListViewPermissionRequired),
        {"cv_viewset": ns.note.vs, "cv_key": "queryset", "cv_path": "queryset", "cv_context_actions": []},
    )
    for name, base in (
        ("ParentOnly", CustomFormNoObjectViewPermissionRequired),
        ("PlainParent", CustomFormNoObjectView),
    ):
        key = name.lower()
        setattr(
            ns.note,
            name,
            type(
                name,
                (GuardianParentPermissionMixin, base),
                {
                    "cv_viewset": ns.note.vs,
                    "cv_key": key,
                    "cv_path": key,
                    "cv_context_actions": [],
                    "get": lambda self, request, *args, **kwargs: HttpResponse("Parent-only destination"),
                },
            ),
        )
    return ns, families


@pytest.mark.django_db
@pytest.mark.parametrize("key", ["detail", "list", "queryset"])
@pytest.mark.parametrize("far_allowed", [False, True])
def test_guardian_cancel_targets_apply_declared_gates(key, far_allowed, monkeypatch):
    with isolated_routes(guardian_cancel_routes) as ns:
        world = consumer_world()
        actor = consumer_actor(ns, world)
        # D-47: without Book change, queryset-only denies after a successful far gate too.
        remove_perm(ns.book.vs.permissions["change"], actor, world.book)
        if not far_allowed:
            remove_perm(ns.pub.vs.permissions["change"], actor, world.pub)
        actor = User.objects.get(pk=actor.pk)
        page = consumer_view(ns.note, "Detail", actor, world)
        page.cv_cancel_key = key
        ns.note.vs.ancestor_policy = AncestorPolicy(
            cascade=True,
            actions={key: AncestorPermissions(nearest="change" if key == "queryset" else "view", higher="change")},
        )
        target = ns.note.vs.get_view_class(key)
        state = Mock(return_value=True)
        monkeypatch.setattr(target, "cv_action_enabled", state)
        gates = []
        original = GuardianViewSet._ancestor_has_permission

        def gate(vs, user, permission, obj, *, view):
            gates.append((vs.name, obj))
            return original(vs, user, permission, obj, view=view)

        monkeypatch.setattr(GuardianViewSet, "_ancestor_has_permission", gate)
        allowed = far_allowed and key != "queryset"
        destination = page.cv_get_url(key, obj=world.note)
        assert page.cv_get_cancel_url() == (destination if allowed else None)
        expected = [(ns.pub.vs.name, page._cv_ancestor_state.objects[1])]
        if far_allowed:
            expected.append((ns.book.vs.name, page._cv_ancestor_state.parent))
        assert gates == expected
        assert all(event[1] is wanted[1] for event, wanted in zip(gates, expected, strict=True))
        if allowed:
            state.assert_called_once_with(actor, world.note if target.cv_object else page._cv_ancestor_state.parent)
        else:
            state.assert_not_called()
        state.reset_mock()
        client = Client()
        client.force_login(actor)
        # Requests keep their existing full-policy result.
        assert client.get(destination).status_code == (200 if far_allowed and key != "queryset" else 403)
        if not far_allowed or key == "queryset":
            state.assert_not_called()


@pytest.mark.django_db
@pytest.mark.parametrize("key", ["detail", "list", "create", "queryset"])
@pytest.mark.parametrize("explicit_allowed", [False, True])
def test_guardian_cancel_explicit_actor_and_request(key, explicit_allowed, monkeypatch):
    with isolated_routes(guardian_cancel_routes) as ns:
        world = consumer_world()
        permitted = consumer_actor(ns, world)
        denied = User.objects.create_user(username="cancel_denied")
        actor, request_actor = (permitted, denied) if explicit_allowed else (denied, permitted)
        page = consumer_view(ns.note, "Detail", permitted, world)
        original_request = page.request
        page.cv_cancel_key = key
        page.cv_cancel_keys = None
        request = RequestFactory().get("/")
        request.user = request_actor
        owners = []
        parent = page._cv_ancestor_state.parent

        def parent_hook(owner):
            owners.append(owner)
            assert owner.request is request
            return parent

        monkeypatch.setattr(ns.note.Detail, "cv_get_parent_object", parent_hook)
        target = ns.note.vs.get_view_class(key)
        create = Mock(wraps=ns.note.Create.cv_create_has_access)
        state = Mock(return_value=True)
        monkeypatch.setattr(ns.note.Create, "cv_create_has_access", create)
        monkeypatch.setattr(target, "cv_action_enabled", state)
        destination = page.cv_get_url(key, obj=world.note)
        assert page.cv_get_cancel_url(user=actor, request=request) == (destination if explicit_allowed else None)
        assert len(owners) == 1
        owner = owners[0]
        assert owner is not page and type(owner) is type(page)
        assert owner.object is world.note and owner._cv_ancestor_state is page._cv_ancestor_state
        assert owner.request is request and page.request is original_request
        assert page.request.user is permitted and request.user is request_actor
        if explicit_allowed:
            action_obj = world.note if target.cv_object else parent
            state.assert_called_once_with(actor, action_obj)
            assert state.call_args.args[1] is action_obj
        else:
            state.assert_not_called()
        if key == "create" and explicit_allowed:
            create.assert_called_once_with(actor, owner, parent)
            assert create.call_args.args[1] is owner and create.call_args.args[2] is parent
        else:
            create.assert_not_called()


@pytest.mark.django_db
@pytest.mark.parametrize("base", ["ParentOnly", "PlainParent"])
@pytest.mark.parametrize("far_allowed", [False, True])
def test_guardian_parent_only_cancel_higher_gates(base, far_allowed, monkeypatch):
    with isolated_routes(guardian_cancel_routes) as ns:
        world = consumer_world()
        actor = consumer_actor(ns, world)
        actor.user_permissions.remove(Permission.objects.get(codename="view_booknote"))
        if not far_allowed:
            remove_perm(ns.pub.vs.permissions["change"], actor, world.pub)
        actor = User.objects.get(pk=actor.pk)
        assert not actor.has_perm("app.view_booknote")
        page = consumer_view(ns.note, "List", actor, world)
        target = getattr(ns.note, base)
        key = target.cv_key
        page.cv_cancel_key = key
        page.cv_cancel_keys = None
        ns.note.vs.ancestor_policy = AncestorPolicy(
            cascade=True, actions={key: AncestorPermissions(nearest="view", higher="change")}
        )
        state = Mock(return_value=True)
        own = Mock(wraps=target.cv_has_access)
        monkeypatch.setattr(target, "cv_action_enabled", state)
        monkeypatch.setattr(target, "cv_has_access", own)
        destination = page.cv_get_url(key)
        assert cv_context_has_permission(page, key) is (far_allowed and base == "PlainParent")
        state.assert_not_called()
        own.reset_mock()
        assert page.cv_get_cancel_url() == (destination if far_allowed else None)
        own.assert_not_called()
        if far_allowed:
            state.assert_called_once_with(actor, page._cv_ancestor_state.parent)
            assert state.call_args.args[1] is page._cv_ancestor_state.parent
        else:
            state.assert_not_called()
        state.reset_mock()
        # The parent-only omission is based on target shape, even for a custom own denial.
        own.side_effect = AssertionError("Cancel must not ask parent-only own access")
        assert page.cv_get_cancel_url() == (destination if far_allowed else None)
        own.assert_not_called()
        state.reset_mock()
        client = Client()
        client.force_login(actor)
        assert client.get(destination).status_code == (200 if far_allowed else 403)
        own.assert_not_called()
        if not far_allowed:
            state.assert_not_called()
        state.reset_mock()
        state.return_value = False
        assert page.cv_get_cancel_url() is None
        if far_allowed:
            state.assert_called_once_with(actor, page._cv_ancestor_state.parent)
        else:
            state.assert_not_called()


@pytest.mark.django_db
@pytest.mark.parametrize("denial", ["nearest", "higher", "hook", None])
def test_guardian_cancel_create_override_boundaries(denial, monkeypatch):
    with isolated_routes(guardian_cancel_routes) as ns:
        world = consumer_world()
        actor = consumer_actor(ns, world)
        if denial in {"nearest", "higher"}:
            family, obj = (ns.book, world.book) if denial == "nearest" else (ns.pub, world.pub)
            remove_perm(family.vs.permissions["change"], actor, obj)
            actor = User.objects.get(pk=actor.pk)
        page = consumer_view(ns.note, "Detail", actor, world)
        page.cv_cancel_key = "create"
        page.cv_cancel_keys = None
        hook = Mock(return_value=denial != "hook")
        state = Mock(return_value=True)
        monkeypatch.setattr(ns.note.Create, "cv_create_has_access", hook)
        monkeypatch.setattr(ns.note.Create, "cv_action_enabled", state)
        destination = page.cv_get_url("create")
        assert page.cv_get_cancel_url() == (destination if denial is None else None)
        if denial in {"nearest", "higher"}:
            hook.assert_not_called()
        else:
            hook.assert_called_once()
            assert hook.call_args.args[0] is actor
            assert hook.call_args.args[1] is not page
            assert hook.call_args.args[1].request is page.request
            assert hook.call_args.args[2] is page._cv_ancestor_state.parent
        if denial is None:
            state.assert_called_once_with(actor, page._cv_ancestor_state.parent)
        else:
            state.assert_not_called()
        state.reset_mock()
        hook.reset_mock()
        client = Client()
        client.force_login(actor)
        assert client.get(destination).status_code == (403 if denial in {"nearest", "higher"} else 200)
        hook.assert_not_called()  # This link hook is not request authorization.
        if denial in {"nearest", "higher"}:
            state.assert_not_called()
