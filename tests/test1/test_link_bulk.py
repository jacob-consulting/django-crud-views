"""Bulk admission uses known guard objects, independently of Cancel's resolver."""

from unittest.mock import Mock

import django_tables2 as tables
import pytest
from django.contrib.auth.models import Permission, User
from django.core.exceptions import ImproperlyConfigured
from django.db import connection
from django.test.utils import CaptureQueriesContext
from guardian.shortcuts import remove_perm

from crud_views.lib.bulk import BulkSelectionMixin
from crud_views.lib.table import Table
from crud_views.lib.views import CardListViewPermissionRequired, ListViewTableMixin
from crud_views.lib.viewset import AncestorPermissions, AncestorPolicy
from crud_views_guardian.lib.views import GuardianCardListViewPermissionRequired
from tests.test1.test_ancestor_authorization import _client, isolated_routes
from tests.test1.test_bulk_source import action_keys
from tests.test1.test_link_consumer_costs import consumer_actor, consumer_routes, consumer_view, consumer_world

pytestmark = pytest.mark.django_db


def bulk_routes(suffix, composition="core"):
    """Add native table/card sources to the existing three-level test family."""
    ns, routed = consumer_routes(suffix, composition)
    for family, field in ((ns.book, "title"), (ns.note, "note")):
        common = {
            "cv_viewset": family.vs,
            "cv_bulk_actions": ("mark",),
            "cv_context_actions": ["create"],
            "cv_list_actions": ["update", "delete"],
        }
        family.BulkTable = type(
            "BulkTable",
            (BulkSelectionMixin, ListViewTableMixin, family.List),
            {
                **common,
                "cv_key": "bulk_table",
                "cv_path": "bulk-table",
                "table_class": type("BulkTableRows", (Table,), {field: tables.Column()}),
            },
        )
        card_base = (
            GuardianCardListViewPermissionRequired if composition == "guardian" else CardListViewPermissionRequired
        )
        family.BulkCard = type(
            "BulkCard",
            (BulkSelectionMixin, card_base),
            {**common, "cv_key": "bulk_card", "cv_path": "bulk-card", "cv_card_actions": []},
        )
    return ns, routed


@pytest.mark.parametrize("source", ["BulkTable", "BulkCard"])
@pytest.mark.parametrize("parent_change", [False, True])
def test_default_parent_view_without_change_hides_write_links_and_toolbar(source, parent_change):
    with isolated_routes(bulk_routes) as ns:
        world = consumer_world()
        actor = consumer_actor(ns, world)
        if not parent_change:
            actor.user_permissions.remove(Permission.objects.get(codename="change_publisher"))
            actor = User.objects.get(pk=actor.pk)
        page = consumer_view(ns.book, source, actor, world)
        client = _client(actor)
        response = client.get(page.cv_get_url(page.cv_key))
        assert response.status_code == 200
        assert action_keys(response) == (["mark"] if parent_change else [])
        rendered = response.context_data["view"]
        for key in ("update", "delete", "create"):
            context = rendered.cv_get_context(key, obj=world.book, user=response.wsgi_request.user)
            assert context["cv_access"] is parent_change
            assert client.get(page.cv_get_url(key, obj=world.book)).status_code == (200 if parent_change else 403)
        assert client.get(page.cv_get_url("mark")).status_code == (302 if parent_change else 403)


@pytest.mark.parametrize("composition", ["core", "guardian"])
@pytest.mark.parametrize("source", ["BulkTable", "BulkCard"])
@pytest.mark.parametrize("far_allowed", [False, True])
def test_bulk_stricter_far_gate_matches_request(composition, source, far_allowed, monkeypatch):
    with isolated_routes(lambda suffix: bulk_routes(suffix, composition)) as ns:
        world = consumer_world()
        actor = consumer_actor(ns, world)
        if not far_allowed:
            if composition == "guardian":
                remove_perm(ns.pub.vs.permissions["change"], actor, world.pub)
            else:
                actor.user_permissions.remove(Permission.objects.get(codename="change_publisher"))
            actor = User.objects.get(pk=actor.pk)
        ns.note.vs.ancestor_policy = AncestorPolicy(
            cascade=True, actions={"mark": AncestorPermissions(nearest="change", higher="change")}
        )
        page = consumer_view(ns.note, source, actor, world)
        own = Mock(wraps=ns.note.Bulk.cv_has_access)
        state = Mock(wraps=ns.note.Bulk.cv_action_enabled)
        step = Mock(wraps=ns.note.Bulk._cv_link_permission)
        monkeypatch.setattr(ns.note.Bulk, "cv_has_access", own)
        monkeypatch.setattr(ns.note.Bulk, "cv_action_enabled", state)
        monkeypatch.setattr(ns.note.Bulk, "_cv_link_permission", step)
        client = _client(actor)
        response = client.get(page.cv_get_url(page.cv_key))
        assert response.status_code == 200
        assert action_keys(response) == (["mark"] if far_allowed else [])
        rendered = response.context_data["view"]
        if far_allowed:
            own.assert_called_once_with(response.wsgi_request.user, None)
            state.assert_called_once_with(response.wsgi_request.user, rendered._cv_ancestor_state.parent)
            assert state.call_args.args[1] is rendered._cv_ancestor_state.parent
            assert step.call_args.kwargs["rendering_view"] is rendered
        else:
            own.assert_not_called()
            state.assert_not_called()
            step.assert_not_called()
        state.reset_mock()
        assert client.get(page.cv_get_url("mark")).status_code == (302 if far_allowed else 403)
        if not far_allowed:
            state.assert_not_called()


@pytest.mark.parametrize("page_key", ["Source", "Create", "Bulk"])
def test_bulk_without_guard_denies_without_resolving_parent(page_key, monkeypatch):
    with isolated_routes(consumer_routes) as ns:
        world = consumer_world()
        actor = consumer_actor(ns, world)
        page = consumer_view(ns.note, page_key, actor, world, guarded=False)
        page.cv_bulk_actions = ("mark",)
        resolver = Mock(return_value=world.book)
        own, state = Mock(return_value=True), Mock(return_value=True)
        monkeypatch.setattr(page, "cv_get_parent_object", resolver)
        monkeypatch.setattr(ns.note.Bulk, "cv_has_access", own)
        monkeypatch.setattr(ns.note.Bulk, "cv_action_enabled", state)
        # Direct descriptor use models custom create/form pages that opt in to
        # admission without pretending their dispatch ran the ancestor guard.
        with CaptureQueriesContext(connection) as queries:
            assert BulkSelectionMixin._cv_effective_bulk_actions.func(page) == ()
        resolver.assert_not_called()
        own.assert_not_called()
        state.assert_not_called()
        assert len(queries) == 0


@pytest.mark.parametrize("error", ["missing-key", "missing-operation"])
def test_bulk_configuration_errors_escape_real_rendering(error, monkeypatch):
    with isolated_routes(bulk_routes) as ns:
        world = consumer_world()
        actor = consumer_actor(ns, world)
        page = consumer_view(ns.note, "BulkTable", actor, world)
        if error == "missing-key":
            ns.note.vs.ancestor_policy = AncestorPolicy(
                cascade=True, actions={"mark": AncestorPermissions(nearest="view", higher="absent")}
            )
            match = "absent"
        else:
            monkeypatch.setattr(ns.note.Bulk, "_cv_ancestor_operation", None)
            match = "outside the built-in Read/Write families"
        state = Mock(return_value=True)
        monkeypatch.setattr(ns.note.Bulk, "cv_action_enabled", state)
        with pytest.raises(ImproperlyConfigured, match=match):
            _client(actor).get(page.cv_get_url(page.cv_key))
        state.assert_not_called()
