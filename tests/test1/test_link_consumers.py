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
from crud_views.lib.view import ContextButton
from tests.test1.test_ancestor_authorization import isolated_routes
from tests.test1.test_link_consumer_costs import consumer_actor, consumer_routes, consumer_view, consumer_world


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
