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
from crud_views_guardian.lib.viewset import GuardianViewSet
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
def test_guardian_child_create_anonymous_exception_only_without_higher_gate(protected_higher, monkeypatch):
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
        assert result["cv_access"] is (not protected_higher)
        if protected_higher:
            create.assert_not_called()
            state.assert_not_called()
        else:
            create.assert_called_once_with(page.request.user, None, world.book)
            state.assert_called_once_with(page.request.user, world.book)


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
            for query in queries for model in ("publisher", "book", "booknote")
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
        kwargs = {} if actor_input == "omitted" else {
            "user": {"none": None, "allowed": actor, "denied": denied}[actor_input]
        }
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
