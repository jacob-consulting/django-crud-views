"""Explicit-parent collection links: request parity, preserved policy and measured SQL.

Phase 06.18 migration (D-19/D-28/D-34/D-41): the child's removed ``cv_guardian_parent_permission="change"`` is
the child ViewSet's explicit Read override ``AncestorPolicy(read=CHANGE)``; the removed create override is an
exact ``actions["create"]`` entry; the old None policy is the parent's ``AncestorPolicy(provider="none")``; a
model-only parent grant needs the parent's own ancestor fallback. Rendering helpers consult only the immediate
parent (``_immediate_parent_access``), which the spy below observes in place of the removed
``_guardian_user_has_parent_perm``.
"""

import json
import sys
import types
import uuid
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from django.contrib.auth.backends import AllowAllUsersModelBackend
from django.test import RequestFactory, override_settings
from django.urls import clear_url_caches, include, path, resolve, reverse
from lxml import html

from crud_views.lib import check as check_module
from crud_views.lib.crispy import CrispyViewMixin
from crud_views.lib.view import CardAction, ChildContextButton
from crud_views.lib.view.visibility import cv_resolve_action
from crud_views.lib.views import CreateViewParentMixin, ListViewPermissionRequired
from crud_views.lib.viewset import _REGISTRY, _REGISTRY_LOCK, AncestorPermissions, AncestorPolicy, ParentViewSet
from crud_views_guardian.lib.mixins import GuardianParentPermissionMixin, GuardianQuerysetMixin
from crud_views_guardian.lib.views import (
    GuardianCardListViewPermissionRequired,
    GuardianCreateViewPermissionRequired,
    GuardianDetailViewPermissionRequired,
    GuardianListViewPermissionRequired,
)
from crud_views_guardian.lib.viewset import GuardianViewSet
from tests.lib.helper.guardian import user_guardian_object_perm
from tests.test1.app.models import Book, Publisher
from tests.test1.app.views import BookForm

VIEW = AncestorPermissions(nearest="view", higher="view")
CHANGE = AncestorPermissions(nearest="change", higher="view")
# the removed child-side cv_guardian_parent_permission="change": every Read endpoint needs parent change
CHANGE_READ = AncestorPolicy(read=CHANGE)


class InactiveBookReaderBackend(AllowAllUsersModelBackend):
    """Retain inactive sessions and grant Book read, independently of model grants."""

    def has_perm(self, user_obj, perm, obj=None):
        return user_obj.is_authenticated and not user_obj.is_active and perm == "app.view_book"


@pytest.fixture
def links():
    suffix = uuid.uuid4().hex
    names = [f"linkpub{suffix}", f"linkbook{suffix}"]
    module_name = f"tests.test1._child_link_urls_{suffix}"
    vocabulary = dict(check_module._VOCAB_CACHE)
    try:
        parent = GuardianViewSet(model=Publisher, name=names[0], icon_header="fa-solid fa-book")

        class HostDetail(GuardianDetailViewPermissionRequired):
            cv_viewset = parent
            cv_context_actions = ["children"]

        class HostCard(GuardianCardListViewPermissionRequired):
            cv_viewset = parent
            cv_context_actions = []

        child = GuardianViewSet(
            model=Book,
            name=names[1],
            parent=ParentViewSet(name=parent.name, attribute="publisher"),
            ancestor_policy=CHANGE_READ,
            icon_header="fa-solid fa-book",
        )

        class TargetList(GuardianListViewPermissionRequired):
            cv_viewset = child
            cv_context_actions = []

        class TargetCard(GuardianCardListViewPermissionRequired):
            cv_viewset = child
            cv_context_actions = []

        class TargetCreate(CrispyViewMixin, CreateViewParentMixin, GuardianCreateViewPermissionRequired):
            cv_viewset = child
            form_class = BookForm

        module = types.ModuleType(module_name)
        module.urlpatterns = [*parent.urlpatterns, *child.urlpatterns, path("", include("tests.test1.project.urls"))]
        sys.modules[module_name] = module
        with override_settings(ROOT_URLCONF=module_name):
            clear_url_caches()
            yield SimpleNamespace(
                parent=parent,
                child=child,
                detail=HostDetail,
                card=HostCard,
                list=TargetList,
                target_card=TargetCard,
                create=TargetCreate,
                module=module,
                names=names,
            )
    finally:
        with _REGISTRY_LOCK:
            for name in names:
                _REGISTRY.pop(name, None)
        check_module._VOCAB_CACHE.clear()
        check_module._VOCAB_CACHE.update(vocabulary)
        sys.modules.pop(module_name, None)
        clear_url_caches()


def configure(links, key="list", child=None):
    child = child or links.child
    button = ChildContextButton(key="children", child_name=child.name, child_key=key)
    action = CardAction(child_name=child.name, child_key=key, label="Child collection")
    links.detail.cv_context_buttons = [button]
    links.card.cv_card_actions = [action]
    return button, action


def bound(cls, actor, obj=None):
    view = cls()
    request = RequestFactory().get("/")
    request.user = actor
    request.resolver_match = SimpleNamespace(url_name=cls.cv_viewset.get_router_name(cls.cv_key))
    view.setup(request)
    view.object = obj
    return view


def rendered_data(links, renderer, actor, obj, *, key="list", child=None):
    button, action = configure(links, key, child)
    if renderer == "context":
        view = bound(links.detail, actor, obj)
        raw = button.get_context(view.cv_get_view_context(object=obj))
    else:
        raw = bound(links.card, actor).cv_get_card_action_data(action, obj, actor)
    return cv_resolve_action(raw)


def child_url(links, key, obj):
    return reverse(links.child.get_router_name(key), kwargs={links.child.parent.get_pk_name(): obj.pk})


@pytest.fixture
def plain_links(cv_book, cv_publisher, monkeypatch):
    """Use the shipped plain views, with all presentation overrides restored after each case."""
    target = cv_book.get_view_class("list")
    detail = cv_publisher.get_view_class("update")
    card = cv_publisher.get_view_class("card")
    monkeypatch.setattr(target, "cv_context_action_label_mode", "label")
    monkeypatch.setattr(detail, "cv_context_actions", ["children"])
    monkeypatch.setattr(detail, "cv_context_buttons", [])
    monkeypatch.setattr(card, "cv_card_actions", [])
    monkeypatch.setattr(card, "cv_card_actions_label_mode", "label")
    return SimpleNamespace(parent=cv_publisher, child=cv_book, detail=detail, card=card, list=target)


@pytest.mark.django_db
@pytest.mark.parametrize("renderer", ["context", "card"])
@pytest.mark.parametrize("mode", ["hide", "disable"])
def test_plain_child_link_parent_permission(plain_links, client, django_user_model, monkeypatch, renderer, mode):
    from django.contrib.auth.models import Permission
    from django.template import Context, Template

    parent = Publisher.objects.create(name="Editable publisher")
    actor = django_user_model.objects.create_user(username="plain_editor")
    actor.user_permissions.add(*Permission.objects.filter(codename__in=["view_book", "change_publisher"]))
    monkeypatch.setattr(plain_links.list, "cv_inaccessible_actions", mode)
    configure(plain_links)
    client.force_login(actor)
    host_url = reverse(plain_links.parent.get_router_name("update"), kwargs={"pk": parent.pk})
    destination = child_url(plain_links, "list", parent)
    host = client.get(host_url)
    assert host.status_code == 200
    assert client.get(destination).status_code == 403
    data = rendered_data(plain_links, renderer, actor, parent)
    if mode == "hide":
        assert data is None
    else:
        assert data["cv_disabled"] is True
        assert data["cv_disabled_reason"] == "permission"
        assert data["cv_url"] is None

    if renderer == "context":
        document = html.fromstring(host.content)
        nodes = document.cssselect('[cv-key="list"]')
    else:
        output = Template("{% load crud_views %}{% cv_render_card_action data %}").render(Context({"data": data}))
        document = html.fragment_fromstring(output, create_parent="div")
        nodes = document.cssselect('[cv-key="book"]')
    assert document.xpath("//*[@href=$url]", url=destination) == []
    if mode == "hide":
        assert nodes == []
    else:
        (node,) = nodes
        assert node.tag == "button"
        assert node.get("disabled") is not None
        assert node.get("data-cv-disabled") == "permission"
        for attribute in ("href", "data-cv-modal", "onclick", "formaction"):
            assert node.get(attribute) is None

    actor.user_permissions.add(Permission.objects.get(codename="view_publisher"))
    actor = django_user_model.objects.get(pk=actor.pk)
    assert rendered_data(plain_links, renderer, actor, parent)["cv_url"] == destination
    assert resolve(destination).kwargs[plain_links.child.parent.get_pk_name()] == str(parent.pk)
    response = client.get(destination)
    assert response.status_code == 200
    assert list(response.context["object_list"]) == []


@pytest.mark.django_db
@pytest.mark.parametrize("renderer", ["context", "card"])
def test_plain_child_link_own_denial(plain_links, django_user_model, monkeypatch, renderer):
    from django.contrib.auth.models import Permission

    actor = django_user_model.objects.create_user(username="denied_child")
    actor.user_permissions.add(Permission.objects.get(codename="view_publisher"))
    parent = Publisher.objects.create(name="Original parent")
    own = Mock(return_value=False)
    monkeypatch.setattr(plain_links.list, "cv_has_access", own)
    spy = parent_spy(monkeypatch, plain_links.list)
    assert rendered_data(plain_links, renderer, actor, parent) is None
    own.assert_called_once_with(actor, None)
    spy.assert_called_once_with(actor, parent)


@pytest.fixture(params=["model", "guardian"])
def core_links(request, plain_links, links, monkeypatch):
    """Plain destinations under either a plain or a Guardian parent."""
    if request.param == "model":
        return plain_links

    class CoreList(ListViewPermissionRequired):
        cv_context_actions = []

    from crud_views.lib.views import CreateViewPermissionRequired

    class CoreCreate(CreateViewPermissionRequired):
        fields = ["title"]

    replace_list(links, CoreList, monkeypatch)
    CoreCreate.cv_viewset = links.child
    monkeypatch.setitem(links.child._views, "create", CoreCreate)
    links.list = CoreList
    return links


@pytest.mark.django_db
@pytest.mark.parametrize("renderer", ["context", "card"])
@pytest.mark.parametrize("operation", ["read", "write", "exact-list"])
@pytest.mark.parametrize("grant", ["view", "change"])
def test_plain_child_link_policy(core_links, django_user_model, monkeypatch, renderer, operation, grant):
    from django.contrib.auth.models import Permission

    actor = django_user_model.objects.create_user(username="plain_policy")
    actor.user_permissions.add(*Permission.objects.filter(codename__in=["view_book", "add_book"]))
    parent = Publisher.objects.create(name="Policy parent")
    other = Publisher.objects.create(name="Other parent")
    is_guardian = isinstance(core_links.parent, GuardianViewSet)
    if is_guardian:
        user_guardian_object_perm(actor, core_links.parent, grant, parent)
    else:
        actor.user_permissions.add(Permission.objects.get(codename=f"{grant}_publisher"))
    policy = AncestorPolicy(read=VIEW, write=CHANGE, actions={"list": CHANGE} if operation == "exact-list" else {})
    monkeypatch.setattr(core_links.child, "ancestor_policy", policy)
    key = "create" if operation == "write" else "list"
    target = core_links.child.get_view_class(key)
    spy = parent_spy(monkeypatch, target)
    provider = type(core_links.parent)
    original = provider._ancestor_has_permission
    calls = []

    def checked(self, user, permission, obj, *, view):
        calls.append((self, user, permission, obj))
        return original(self, user, permission, obj, view=view)

    monkeypatch.setattr(provider, "_ancestor_has_permission", checked)
    required = "view" if operation == "read" else "change"
    for supplied in (parent, other):
        spy.reset_mock()
        data = rendered_data(core_links, renderer, actor, supplied, key=key)
        assert (data is not None) is (grant == required and (not is_guardian or supplied is parent))
        spy.assert_called_once_with(actor, supplied)
        assert calls[-1] == (core_links.parent, actor, f"app.{required}_publisher", supplied)
        assert calls[-1][3] is supplied


@pytest.mark.django_db
@pytest.mark.parametrize("renderer", ["context", "card"])
@pytest.mark.parametrize("fallback", [False, True])
@pytest.mark.parametrize("local_fallback", [False, True])
def test_plain_child_link_parent_fallback(links, django_user_model, monkeypatch, renderer, fallback, local_fallback):
    from django.contrib.auth.models import Permission

    class CoreList(ListViewPermissionRequired):
        cv_guardian_accept_global_perms = local_fallback

    replace_list(links, CoreList, monkeypatch)
    monkeypatch.setattr(links.parent, "ancestor_policy", AncestorPolicy(accept_global_perms=fallback))
    actor = django_user_model.objects.create_user(username="plain_fallback")
    actor.user_permissions.add(*Permission.objects.filter(codename__in=["view_book", "change_publisher"]))
    parent = Publisher.objects.create(name="Model grant only")
    spy = parent_spy(monkeypatch, CoreList)
    assert (rendered_data(links, renderer, actor, parent) is not None) is fallback
    spy.assert_called_once_with(actor, parent)


@pytest.mark.django_db
@pytest.mark.parametrize("renderer", ["context", "card"])
@pytest.mark.parametrize("actor_kind", ["anonymous", "inactive"])
@pytest.mark.parametrize("provider_none", [False, True])
def test_plain_child_link_actor_policy(core_links, django_user_model, monkeypatch, renderer, actor_kind, provider_none):
    from django.contrib.auth.models import AnonymousUser

    from crud_views.lib.views import ListView

    class PlainList(ListView):
        cv_context_action_label_mode = "label"

    PlainList.cv_viewset = core_links.child
    monkeypatch.setitem(core_links.child._views, "list", PlainList)
    parent = Publisher.objects.create(name="Actor parent")
    actor = (
        AnonymousUser()
        if actor_kind == "anonymous"
        else django_user_model.objects.create_user(username="inactive_plain", is_active=False)
    )
    if provider_none:
        monkeypatch.setattr(core_links.parent, "ancestor_policy", AncestorPolicy(provider="none"))
    spy = parent_spy(monkeypatch, PlainList)
    assert PlainList.cv_has_access(actor, None) is True
    assert (rendered_data(core_links, renderer, actor, parent) is not None) is provider_none
    spy.assert_called_once_with(actor, parent)
    own = Mock(return_value=False)
    monkeypatch.setattr(PlainList, "cv_has_access", own)
    spy.reset_mock()
    assert rendered_data(core_links, renderer, actor, parent) is None
    spy.assert_called_once_with(actor, parent)
    if provider_none:
        own.assert_called_once_with(actor, None)
    else:
        own.assert_not_called()


@pytest.mark.django_db
@pytest.mark.parametrize("renderer", ["context", "card"])
@pytest.mark.parametrize("mode", ["hide", "disable"])
@pytest.mark.parametrize("actor_kind", ["anonymous", "inactive", "inactive-superuser"])
@pytest.mark.parametrize("provider_none", [False, True], ids=["protected", "none"])
def test_plain_child_link_backend_grant_cannot_waive_actor_rule(
    client, django_user_model, monkeypatch, renderer, mode, actor_kind, provider_none
):
    from django.contrib.auth.models import AnonymousUser
    from django.db import connection
    from django.test.utils import CaptureQueriesContext

    from crud_views.lib.views import CardListView, DetailView, ListView
    from crud_views.lib.viewset import ViewSet
    from tests.test1.app.models import BookNote
    from tests.test1.test_ancestor_actors import ANONYMOUS_READER
    from tests.test1.test_ancestor_authorization import isolated_routes

    def build(suffix):
        parent = ViewSet(model=Book, name=f"actorbook{suffix}", icon_header="fa-solid fa-book")
        child = ViewSet(
            model=BookNote,
            name=f"actornote{suffix}",
            parent=ParentViewSet(name=parent.name, attribute="book"),
        )

        class Host(DetailView):
            cv_viewset = parent
            cv_context_actions = []

        class Cards(CardListView):
            cv_viewset = parent
            cv_context_actions = []
            cv_card_actions_label_mode = "label"

        class Target(ListView):
            cv_viewset = child
            cv_context_actions = []
            cv_context_action_label_mode = "label"
            cv_inaccessible_actions = mode

        return SimpleNamespace(parent=parent, child=child, detail=Host, card=Cards, list=Target), [parent, child]

    actor = (
        AnonymousUser()
        if actor_kind == "anonymous"
        else django_user_model.objects.create_user(
            username="backend_reader", is_active=False, is_superuser=actor_kind == "inactive-superuser"
        )
    )
    parent_obj = Book.objects.create(title="Actor parent", publisher=Publisher.objects.create(name="Publisher"))
    inactive_backend = f"{__name__}.InactiveBookReaderBackend"
    with (
        isolated_routes(build) as family,
        override_settings(AUTHENTICATION_BACKENDS=[ANONYMOUS_READER, inactive_backend]),
    ):
        if provider_none:
            monkeypatch.setattr(family.parent, "ancestor_policy", AncestorPolicy(provider="none"))
        if actor_kind != "anonymous":
            client.force_login(actor, backend=inactive_backend)
        assert actor.has_perm("app.view_book") is True
        assert family.list.cv_has_access(actor, None) is True
        destination = child_url(family, "list", parent_obj)
        response = client.get(destination)
        assert response.status_code == (200 if provider_none else 302 if actor_kind == "anonymous" else 403)
        if response.status_code == 302:
            assert response["Location"] == f"/accounts/login/?next={destination}"
        spy = parent_spy(monkeypatch, family.list)
        with CaptureQueriesContext(connection) as capture:
            data = rendered_data(family, renderer, actor, parent_obj)
        spy.assert_called_once_with(actor, parent_obj)
        assert all('FROM "app_' not in query["sql"] for query in capture.captured_queries)
        if provider_none:
            assert data["cv_access"] is True
            assert data["cv_disabled"] is False
            assert data["cv_url"] == destination
        elif mode == "hide":
            assert data is None
        else:
            assert data["cv_access"] is False
            assert data["cv_disabled"] is True
            assert data["cv_disabled_reason"] == "permission"
            assert data["cv_url"] is None

        own = Mock(return_value=False)
        monkeypatch.setattr(family.list, "cv_has_access", own)
        spy.reset_mock()
        with CaptureQueriesContext(connection) as capture:
            denied = rendered_data(family, renderer, actor, parent_obj)
        assert denied is None if mode == "hide" else denied["cv_url"] is None and denied["cv_disabled"]
        spy.assert_called_once_with(actor, parent_obj)
        if provider_none:
            own.assert_called_once_with(actor, None)
        else:
            own.assert_not_called()
        assert len(capture) == 0


@pytest.mark.django_db
@pytest.mark.parametrize("renderer", ["context", "card"])
@pytest.mark.parametrize("error", ["mapping", "operation", "database"])
@pytest.mark.parametrize("own_allowed", [False, True])
def test_plain_child_link_errors(core_links, django_user_model, monkeypatch, renderer, error, own_allowed):
    from django.contrib.auth.models import Permission
    from django.core.exceptions import ImproperlyConfigured
    from django.db import router

    from crud_views.lib.views import ActionView, ListView

    # Plain own access isolates errors in the parent gate; no permission helper is mocked.
    class Target(ActionView if error == "operation" else ListView):
        cv_key = "list"
        cv_context_action_label_mode = "label"
        cv_action_label_template_code = "Child collection"
        cv_action_short_label_template_code = "Children"

    Target.cv_viewset = core_links.child
    monkeypatch.setitem(core_links.child._views, "list", Target)
    actor = django_user_model.objects.create_user(username="plain_errors")
    parent = Publisher.objects.create(name="Invalid configuration")
    if error == "mapping":
        monkeypatch.setattr(
            core_links.child,
            "ancestor_policy",
            AncestorPolicy(read=AncestorPermissions(nearest="undeclared", higher="view")),
        )
        match = "undeclared"
    elif error == "database":

        class AuthRouter:
            def db_for_read(self, model, **hints):
                return "shard" if model is Permission else None

        monkeypatch.setattr(router, "routers", [AuthRouter()])
        match = "shard"
    else:
        match = "operation|actions"
    spy = parent_spy(monkeypatch, Target)
    if not own_allowed:
        monkeypatch.setattr(Target, "cv_has_access", Mock(return_value=False))
    with pytest.raises(ImproperlyConfigured, match=match):
        rendered_data(core_links, renderer, actor, parent)
    spy.assert_called_once_with(actor, parent)

    # Provider none returns before operation/vocabulary/database checks, then own access still decides.
    monkeypatch.setattr(core_links.parent, "ancestor_policy", AncestorPolicy(provider="none"))
    spy.reset_mock()
    assert (rendered_data(core_links, renderer, actor, parent) is not None) is own_allowed
    assert spy.call_count == 1
    assert Target._cv_link_permission(actor, None, None) is False


@pytest.mark.django_db
@pytest.mark.parametrize("renderer", ["context", "card"])
def test_plain_child_link_farther_ancestor(client, django_user_model, monkeypatch, renderer):
    from django.contrib.auth.models import Permission
    from django.db import connection
    from django.test.utils import CaptureQueriesContext

    from crud_views.lib.views import CardListView, DetailView, ListViewPermissionRequired
    from crud_views.lib.viewset import ViewSet
    from tests.test1.app.models import BookNote
    from tests.test1.test_ancestor_authorization import isolated_routes

    def build(suffix):
        pub = ViewSet(model=Publisher, name=f"far_pub{suffix}")
        book = ViewSet(model=Book, name=f"far_book{suffix}", parent=ParentViewSet(name=pub.name, attribute="publisher"))
        note = ViewSet(model=BookNote, name=f"far_note{suffix}", parent=ParentViewSet(name=book.name, attribute="book"))
        host = type("Host", (DetailView,), {"cv_viewset": book, "cv_context_actions": []})
        card = type(
            "Card",
            (CardListView,),
            {"cv_viewset": book, "cv_context_actions": [], "cv_card_actions_label_mode": "label"},
        )
        target = type(
            "Notes",
            (ListViewPermissionRequired,),
            {"cv_viewset": note, "cv_context_actions": [], "cv_context_action_label_mode": "label"},
        )
        return SimpleNamespace(parent=book, child=note, detail=host, card=card, list=target, grandparent=pub), [
            pub,
            book,
            note,
        ]

    with isolated_routes(build) as family:
        publisher = Publisher.objects.create(name="Denied farther ancestor")
        parent = Book.objects.create(title="Allowed immediate parent", publisher=publisher)
        actor = django_user_model.objects.create_user(username="near_only")
        actor.user_permissions.add(*Permission.objects.filter(codename__in=["view_book", "view_booknote"]))
        button, action = configure(family)
        host = bound(family.detail if renderer == "context" else family.card, actor, parent)
        host.kwargs = {family.parent.parent.get_pk_name(): publisher.pk}
        spy = parent_spy(monkeypatch, family.list)
        original = ViewSet._ancestor_has_permission
        provider_calls = []

        def checked(self, user, permission, obj, *, view):
            provider_calls.append((self.name, permission, obj))
            return original(self, user, permission, obj, view=view)

        monkeypatch.setattr(ViewSet, "_ancestor_has_permission", checked)
        with CaptureQueriesContext(connection) as capture:
            raw = (
                button.get_context(host.cv_get_view_context(object=parent))
                if renderer == "context"
                else host.cv_get_card_action_data(action, parent, actor)
            )
        data = cv_resolve_action(raw)
        assert data["cv_access"] is True
        spy.assert_called_once_with(actor, parent)
        assert provider_calls == [(family.parent.name, "app.view_book", parent)]
        categories = sql_categories(capture.captured_queries)
        assert categories.get("parent_rows", 0) == categories.get("child_or_relation_rows", 0) == 0
        client.force_login(actor)
        assert client.get(data["cv_url"]).status_code == 403


@pytest.mark.django_db
@pytest.mark.parametrize("renderer", ["context", "card"])
@pytest.mark.parametrize("target_key", ["list", "card"])
@pytest.mark.parametrize("mode", ["hide", "disable"])
def test_parity_child_collection(links, client, django_user_model, monkeypatch, renderer, target_key, mode):
    parent = Publisher.objects.create(name="Viewable parent")
    actor = django_user_model.objects.create_user(username="parent_viewer")
    user_guardian_object_perm(actor, links.parent, "view", parent)
    client.force_login(actor)
    configure(links, target_key)
    target = links.child.get_view_class(target_key)
    monkeypatch.setattr(target, "cv_inaccessible_actions", mode)
    host_url = (
        reverse(links.parent.get_router_name("detail"), kwargs={"pk": parent.pk})
        if renderer == "context"
        else reverse(links.parent.get_router_name("card"))
    )
    destination = child_url(links, target_key, parent)

    assert client.get(destination).status_code == 403
    response = client.get(host_url)
    assert response.status_code == 200
    data = rendered_data(links, renderer, actor, parent, key=target_key)
    document = html.fromstring(response.content)
    assert document.xpath("//*[@href=$url]", url=destination) == []
    key = target_key if renderer == "context" else links.child.name
    nodes = document.cssselect(f'[cv-key="{key}"]')
    if mode == "hide":
        assert data is None
        assert nodes == []
    else:
        assert data["cv_disabled"] is True
        assert data["cv_disabled_reason"] == "permission"
        assert data["cv_url"] is None
        (node,) = nodes
        assert node.tag == "button"
        assert node.get("data-cv-disabled") == "permission"
        assert node.get("disabled") is not None
        for attribute in ("href", "data-cv-modal", "onclick", "formaction"):
            assert node.get(attribute) is None

    user_guardian_object_perm(actor, links.parent, "change", parent)
    actor = django_user_model.objects.get(pk=actor.pk)  # The next rendering models a fresh request user.
    response = client.get(host_url)
    assert response.status_code == 200
    assert html.fromstring(response.content).xpath("//*[@href=$url]", url=destination)
    assert rendered_data(links, renderer, actor, parent, key=target_key)["cv_url"] == destination
    response = client.get(destination)
    assert response.status_code == 200
    assert list(response.context["object_list"]) == []


def parent_spy(monkeypatch, target):
    """Record ``(user, parent)`` for every bounded immediate-parent gate evaluated on behalf of ``target`` (the
    Core lazy imports and Guardian aliases are separate lookup sites; each wraps the original helper once)."""
    from crud_views.lib import ancestors
    from crud_views_guardian.lib import mixins, views

    spy = Mock()
    for module in (ancestors, mixins, views):

        def gate(view_class, user, parent_obj, *, rendering_view=None, _original=module._immediate_parent_access):
            if view_class is target:
                spy(user, parent_obj)
            return _original(view_class, user, parent_obj, rendering_view=rendering_view)

        monkeypatch.setattr(module, "_immediate_parent_access", gate)
    return spy


def unprotected_parent(links, monkeypatch):
    """The removed child-side None policy: the (single-scenario) parent ViewSet is unprotected as an ancestor."""
    monkeypatch.setattr(links.parent, "ancestor_policy", AncestorPolicy(provider="none"))


@pytest.fixture
def world(links, django_user_model):
    parents = [Publisher.objects.create(name="Equal label") for _ in range(2)]
    actors = [django_user_model.objects.create_user(username=f"actor_{i}") for i in range(2)]
    for actor, parent in zip(actors, parents, strict=True):
        user_guardian_object_perm(actor, links.parent, "change", parent)
    return actors, parents


@pytest.mark.django_db
@pytest.mark.parametrize("renderer", ["context", "card"])
def test_preservation_identity_interleaving_and_repetition(links, world, monkeypatch, renderer):
    actors, parents = world
    spy = parent_spy(monkeypatch, links.list)
    monkeypatch.setattr(links.list, "cv_inaccessible_actions", "disable")
    original = [(obj.pk, obj.name) for obj in parents]
    # Same labels, opposite grants, repeated calls and reversed inputs retain identity.
    for actor in [*actors, *reversed(actors)]:
        for parent in [*parents, *reversed(parents)]:
            data = rendered_data(links, renderer, actor, parent)
            allowed = actors.index(actor) == parents.index(parent)
            assert data["cv_access"] is allowed
            assert spy.call_args.args[0] is actor
            assert spy.call_args.args[1] is parent
            if allowed:
                match = resolve(data["cv_url"])
                assert match.kwargs[links.child.parent.get_pk_name()] == str(parent.pk)
            else:
                assert data["cv_url"] is None
    assert spy.call_count == 16
    assert [(obj.pk, obj.name) for obj in parents] == original


@pytest.mark.django_db
@pytest.mark.parametrize("renderer", ["context", "card"])
@pytest.mark.parametrize("grant", ["object", "group", "global", "superuser", "none"])
@pytest.mark.parametrize("local_flag", [False, True])
@pytest.mark.parametrize("parent_fallback", [False, True])
def test_preservation_permission_channels(
    links, django_user_model, monkeypatch, renderer, grant, local_flag, parent_fallback
):
    from django.contrib.auth.models import Group, Permission
    from guardian.shortcuts import assign_perm

    parent = Publisher.objects.create(name="Policy parent")
    actor = django_user_model.objects.create_user(username="policy", is_superuser=grant == "superuser")
    if grant == "object":
        user_guardian_object_perm(actor, links.parent, "change", parent)
    elif grant == "group":
        group = Group.objects.create(name="editors")
        actor.groups.add(group)
        assign_perm(links.parent.permissions["change"], group, parent)
    elif grant == "global":
        actor.user_permissions.add(Permission.objects.get(codename="change_publisher"))
    # D-41: a model-only parent grant counts only through the parent's own ancestor fallback; the target list's
    # local cv_guardian_accept_global_perms (formerly the switch here) neither grants nor removes it
    monkeypatch.setattr(links.list, "cv_guardian_accept_global_perms", local_flag)
    monkeypatch.setattr(links.parent, "ancestor_policy", AncestorPolicy(accept_global_perms=parent_fallback))
    allowed = grant in {"object", "group", "superuser"} or (grant == "global" and parent_fallback)
    assert (rendered_data(links, renderer, actor, parent) is not None) is allowed


@pytest.mark.django_db
@pytest.mark.parametrize("renderer", ["context", "card"])
@pytest.mark.parametrize("actor_kind", ["active", "anonymous", "inactive", "inactive_superuser"])
@pytest.mark.parametrize("enabled", [False, True])
def test_preservation_none_policy_actor_state(links, django_user_model, monkeypatch, renderer, actor_kind, enabled):
    from django.contrib.auth.models import AnonymousUser

    parent = Publisher.objects.create(name="No permission gate")
    actor = (
        AnonymousUser()
        if actor_kind == "anonymous"
        else django_user_model.objects.create_user(
            username="none_actor", is_active=actor_kind == "active", is_superuser=actor_kind == "inactive_superuser"
        )
    )
    unprotected_parent(links, monkeypatch)
    monkeypatch.setattr(links.list, "cv_inaccessible_actions", "disable")
    state = Mock(return_value=enabled)
    monkeypatch.setattr(links.list, "cv_action_enabled", state)
    # A concrete always-allow override cannot bypass the nested actor gate.
    access = Mock(return_value=True)
    monkeypatch.setattr(links.list, "cv_has_access", access)
    spy = parent_spy(monkeypatch, links.list)
    data = rendered_data(links, renderer, actor, parent)
    active = actor_kind == "active"
    assert data["cv_access"] is active
    assert data["cv_action_enabled"] is (enabled if active else True)
    assert data["cv_disabled"] is not (active and enabled)
    if data["cv_disabled"]:
        assert data["cv_url"] is None
        assert data["cv_disabled_reason"] == ("state" if active else "permission")
    assert spy.call_count == int(active)
    assert access.call_count == int(active)
    if active:
        state.assert_called_once_with(actor, parent)
    else:
        state.assert_not_called()


@pytest.mark.django_db
@pytest.mark.parametrize("renderer", ["context", "card"])
@pytest.mark.parametrize("allow", [False, True])
def test_preservation_custom_access_and_original_object(links, world, monkeypatch, renderer, allow):
    actors, parents = world
    actor, parent = actors[0], parents[0]
    access = Mock(return_value=allow)
    monkeypatch.setattr(links.list, "cv_has_access", access)
    spy = parent_spy(monkeypatch, links.list)
    result = rendered_data(links, renderer, actor, parent)
    assert (result is not None) is allow
    access.assert_called_once_with(actor, None)
    assert spy.call_count == 1


def replace_list(links, target, monkeypatch):
    """Keep registered URL builders and real destination requests on the replacement class."""
    target.cv_viewset = links.child
    monkeypatch.setitem(links.child._views, "list", target)
    links.child.__dict__.pop("urlpatterns", None)
    links.module.urlpatterns = [
        *links.parent.urlpatterns,
        *links.child.urlpatterns,
        path("", include("tests.test1.project.urls")),
    ]
    clear_url_caches()


@pytest.mark.django_db
@pytest.mark.parametrize("renderer", ["context", "card"])
def test_preservation_queryset_only_composition(links, client, django_user_model, monkeypatch, renderer):
    from django.contrib.auth.models import AnonymousUser

    class QuerysetOnly(GuardianQuerysetMixin, ListViewPermissionRequired):
        cv_context_actions = []

    replace_list(links, QuerysetOnly, monkeypatch)
    assert not issubclass(QuerysetOnly, GuardianParentPermissionMixin)
    parent = Publisher.objects.create(name="No parent grant")
    actor = django_user_model.objects.create_user(username="queryset_only")
    client.force_login(actor)
    data = rendered_data(links, renderer, actor, parent)
    assert data["cv_url"] == child_url(links, "list", parent)
    # D-03/D-19: the request now runs the shared ancestor guard (parent change, the child's Read pair) although
    # the bounded link helper of a queryset-only composition does not consult the parent: a visible link can be
    # denied (first-wave limitation)
    assert client.get(data["cv_url"]).status_code == 403
    user_guardian_object_perm(actor, links.parent, "change", parent)
    response = client.get(data["cv_url"])
    assert response.status_code == 200
    assert list(response.context["object_list"]) == []

    access = Mock(return_value=False)
    monkeypatch.setattr(QuerysetOnly, "cv_has_access", access)
    assert rendered_data(links, renderer, actor, parent) is None
    assert access.call_args.args[1] is None
    access.return_value = True
    for denied in (AnonymousUser(), django_user_model.objects.create_user(username="inactive", is_active=False)):
        access.reset_mock()
        assert rendered_data(links, renderer, denied, parent) is None
        access.assert_not_called()


@pytest.mark.django_db
def test_preservation_inherited_custom_policy(links, django_user_model, monkeypatch):
    from django.contrib.auth.models import Permission

    class CustomQueryset(GuardianQuerysetMixin):
        cv_guardian_accept_global_perms = True

    class Composed(GuardianParentPermissionMixin, CustomQueryset, ListViewPermissionRequired):
        pass

    replace_list(links, Composed, monkeypatch)
    assert Composed.cv_guardian_accept_global_perms is True  # the custom local policy stays inherited
    actor = django_user_model.objects.create_user(username="inherited")
    actor.user_permissions.add(Permission.objects.get(codename="change_publisher"))
    parent = Publisher.objects.create(name="Inherited policy")
    # D-41: the inherited local fallback no longer relaxes the strict Guardian parent ...
    assert rendered_data(links, "context", actor, parent) is None
    # ... the parent's own ancestor fallback does
    monkeypatch.setattr(links.parent, "ancestor_policy", AncestorPolicy(accept_global_perms=True))
    assert rendered_data(links, "context", actor, parent)["cv_access"] is True


@pytest.mark.django_db
@pytest.mark.parametrize("allow", [False, True])
def test_preservation_top_level_delegates_without_actor_or_parent_gate(links, monkeypatch, allow):
    from django.contrib.auth.models import AnonymousUser

    actor = AnonymousUser()
    access = Mock(return_value=allow)
    monkeypatch.setattr(links.card, "cv_has_access", access)
    spy = parent_spy(monkeypatch, links.card)
    assert links.card._cv_link_permission(actor, None, None) is allow
    access.assert_called_once_with(actor, None)
    spy.assert_not_called()


@pytest.mark.django_db
@pytest.mark.parametrize("renderer", ["context", "card"])
@pytest.mark.parametrize("policy", ["explicit", "fallback", "none", "global"])
@pytest.mark.parametrize("enabled", [False, True])
def test_preservation_create_policy_once(links, world, monkeypatch, renderer, policy, enabled):
    from django.contrib.auth.models import Permission

    actors, parents = world
    actor, parent = actors[0], parents[0]
    if policy == "explicit":  # the removed create override "view": an exact create entry
        monkeypatch.setattr(links.child, "ancestor_policy", AncestorPolicy(read=CHANGE, actions={"create": VIEW}))
        user_guardian_object_perm(actor, links.parent, "view", parent)
    if policy == "none":
        unprotected_parent(links, monkeypatch)
    if policy == "global":
        actor = actors[1]  # no object grant on this parent
        actor.user_permissions.add(Permission.objects.get(codename="change_publisher"))
        # D-41: the parent's own ancestor fallback, not the create view's cv_guardian_accept_global_perms
        monkeypatch.setattr(links.parent, "ancestor_policy", AncestorPolicy(accept_global_perms=True))
    monkeypatch.setattr(links.create, "cv_inaccessible_actions", "disable")
    state = Mock(return_value=enabled)
    monkeypatch.setattr(links.create, "cv_action_enabled", state)
    spy = parent_spy(monkeypatch, links.create)
    data = rendered_data(links, renderer, actor, parent, key="create")
    assert data["cv_access"] is True
    assert data["cv_action_enabled"] is enabled
    assert data["cv_disabled"] is not enabled
    spy.assert_called_once_with(actor, parent)
    state.assert_called_once_with(actor, parent)
    if not enabled:
        assert data["cv_disabled_reason"] == "state"
        assert data["cv_url"] is None
    access = Mock(return_value=False)
    monkeypatch.setattr(links.create, "cv_create_has_access", access)
    spy.reset_mock()
    data = rendered_data(links, renderer, actor, parent, key="create")
    assert data["cv_disabled_reason"] == "permission"
    access.assert_called_once_with(actor, None, parent)
    spy.assert_not_called()


@pytest.mark.django_db
@pytest.mark.parametrize("renderer", ["context", "card"])
def test_preservation_interleaved_create_custom_and_collection(links, world, monkeypatch, renderer):
    actors, parents = world
    actor, parent = actors[0], parents[0]
    monkeypatch.setattr(links.child, "ancestor_policy", AncestorPolicy(read=CHANGE, actions={"create": VIEW}))
    custom = Mock(return_value=False)
    monkeypatch.setattr(links.target_card, "cv_has_access", custom)
    for key in ["list", "create", "card", "list", "card", "create"]:
        assert (rendered_data(links, renderer, actor, parent, key=key) is not None) is (key == "list")
    assert custom.call_count == 2
    assert all(call.args[1] is None for call in custom.call_args_list)


@pytest.mark.django_db
@pytest.mark.parametrize("rows", [0, 1])
def test_preservation_empty_context_and_collection_rows(links, world, client, rows):
    actors, parents = world
    actor, parent = actors[0], parents[0]
    if rows:
        book = Book.objects.create(title="One child", publisher=parent)
        user_guardian_object_perm(actor, links.child, "view", book)
    button, _ = configure(links)
    view = bound(links.detail, actor)
    assert button.get_context(view.cv_get_view_context(object=None)) == {}
    client.force_login(actor)
    for renderer in ("context", "card"):
        data = rendered_data(links, renderer, actor, parent)
        response = client.get(data["cv_url"])
        assert response.status_code == 200
        assert len(response.context["object_list"]) == rows


@pytest.mark.django_db
def test_preservation_configured_order_and_repeated_actions(links, world, monkeypatch):
    actors, parents = world
    actor, parent = actors[0], parents[0]
    monkeypatch.setattr(links.target_card, "cv_has_access", Mock(return_value=False))
    actions = [
        CardAction(child_name=links.child.name, child_key="list", label="First"),
        CardAction(child_name=links.child.name, child_key="card", label="Denied"),
        CardAction(child_name=links.child.name, child_key="list", label="Last"),
    ]
    for ordered in (actions, list(reversed(actions))):
        links.card.cv_card_actions = ordered
        group = bound(links.card, actor).cv_get_card_action_group(parent)
        assert [data["cv_label"] for data in group.inline] == [a.label for a in ordered if a.child_key == "list"]


@pytest.fixture(params=["m2m", "same-model", "core"])
def alternate_child(links, request):
    from crud_views.lib.viewset import ViewSet
    from tests.test1.app.models import Genre

    kind = request.param
    name = f"{kind.replace('-', '')}{uuid.uuid4().hex}"
    links.names.append(name)
    viewset_cls = ViewSet if kind == "core" else GuardianViewSet
    model = {"m2m": Genre, "same-model": Publisher, "core": Book}[kind]
    parent_args = {"name": links.parent.name, "attribute": "publisher"}
    if kind == "m2m":
        parent_args.update(attribute="publishers", many_to_many_through_attribute="genres")
    child = viewset_cls(model=model, name=name, parent=ParentViewSet(**parent_args))
    if kind != "core":
        child.ancestor_policy = CHANGE_READ
    base = ListViewPermissionRequired if kind == "core" else GuardianListViewPermissionRequired

    class AlternateList(base):
        cv_viewset = child
        cv_context_actions = []

    links.module.urlpatterns = [*child.urlpatterns, *links.module.urlpatterns]
    clear_url_caches()
    return kind, child, AlternateList


@pytest.mark.django_db
@pytest.mark.parametrize("renderer", ["context", "card"])
def test_preservation_explicit_m2m_same_model_and_core(links, alternate_child, world, monkeypatch, renderer, client):
    """Same-model coverage is adapter/rendering only: no invented self-relation or request parity."""
    from django.contrib.auth.models import Permission

    kind, child, target = alternate_child
    actors, parents = world
    actor = actors[0]
    if kind == "core":
        actor.user_permissions.add(Permission.objects.get(codename="view_book"))
        user_guardian_object_perm(actor, links.parent, "view", parents[0])
        own = Mock(wraps=target.cv_has_access)
        monkeypatch.setattr(target, "cv_has_access", own)
    spy = parent_spy(monkeypatch, target)
    for parent in parents:
        result = rendered_data(links, renderer, actor, parent, child=child)
        assert spy.call_args.args[1] is parent
        allowed = parent is parents[0]
        assert (result is not None) is allowed
        if allowed:
            assert resolve(result["cv_url"]).kwargs[child.parent.get_pk_name()] == str(parent.pk)
            if kind == "m2m":
                client.force_login(actor)
                response = client.get(result["cv_url"])
                assert response.status_code == 200
                assert list(response.context["object_list"]) == []
    if kind == "core":
        own.assert_called_once_with(actor, None)


@pytest.mark.django_db
def test_preservation_ordinary_row_and_sibling_actions(links, world, monkeypatch):
    from crud_views.lib.view import ContextButton, SiblingContextButton

    actors, parents = world
    actor, parent = actors[0], parents[0]
    # Ordinary row actions retain object access, without entering a parent gate.
    user_guardian_object_perm(actor, links.parent, "view", parent)
    detail_gate = parent_spy(monkeypatch, links.detail)
    view = bound(links.card, actor)
    row = view.cv_get_card_action_data(CardAction(key="detail"), parent, actor)
    assert row["cv_access"] is True
    assert resolve(row["cv_url"].split("?")[0]).kwargs["pk"] == str(parent.pk)
    own = ContextButton(key="detail", key_target="detail").get_context(view.cv_get_view_context(object=parent))
    assert own["cv_access"] is True
    detail_gate.assert_not_called()

    # A sibling collection remains on its pre-existing general access path (outside this fix).
    list_gate = parent_spy(monkeypatch, links.list)
    sibling = SiblingContextButton(key="sibling", sibling_name=links.child.name)
    host = bound(links.target_card, actor)
    host.kwargs = {links.child.parent.get_pk_name(): parents[1].pk}
    data = sibling.get_context(host.cv_get_view_context())
    assert data["cv_access"] is True
    assert resolve(data["cv_url"]).kwargs[links.child.parent.get_pk_name()] == str(parents[1].pk)
    list_gate.assert_not_called()


@pytest.mark.django_db
@pytest.mark.parametrize("renderer", ["context", "card"])
def test_preservation_existing_parent_declaration_error_propagates(links, world, monkeypatch, renderer):
    actors, parents = world
    from django.core.exceptions import ImproperlyConfigured

    # an undeclared key in the requested ViewSet's pair surfaces as a configuration error (never hidden or granted)
    monkeypatch.setattr(
        links.child, "ancestor_policy", AncestorPolicy(read=AncestorPermissions(nearest="undeclared", higher="view"))
    )
    with pytest.raises(ImproperlyConfigured, match="'undeclared'"):
        rendered_data(links, renderer, actors[0], parents[0])


def sql_categories(queries):
    """Classify outer SELECTs: permission joins mentioning content types are still permission work."""
    from collections import Counter

    counts = Counter()
    for query in queries:
        sql = query["sql"].lower()
        if 'from "app_publisher"' in sql:
            kind = "parent_rows"
        elif 'from "app_book"' in sql or 'from "app_genre' in sql:
            kind = "child_or_relation_rows"
        elif 'from "auth_permission"' in sql:
            kind = "permissions"
        elif 'from "django_content_type"' in sql:
            kind = "content_type"
        elif 'from "auth_user"' in sql:
            kind = "actor"
        elif 'from "django_session"' in sql:
            kind = "session"
        else:
            kind = "other"
        counts[kind] += 1
    return dict(counts)


def reset_discovery(links):
    from django.contrib.contenttypes.models import ContentType
    from guardian.shortcuts import clear_ct_cache

    ContentType.objects.clear_cache()
    clear_ct_cache()
    links.parent._default_permissions = None
    links.child._default_permissions = None


def report_measurement(record_property, **values):
    text = json.dumps(values, sort_keys=True)
    record_property("measurement", text)
    print(text)


@pytest.mark.django_db
@pytest.mark.parametrize("renderer", ["context", "card"])
@pytest.mark.parametrize("actor_cache", ["fresh", "warm"])
@pytest.mark.parametrize("vocabulary", ["cold", "warm"])
def test_query_plain_child_link_cost(
    core_links, world, django_user_model, monkeypatch, record_property, renderer, actor_cache, vocabulary
):
    from django.contrib.auth.models import Permission
    from django.db import connection
    from django.test.utils import CaptureQueriesContext

    actors, parents = world
    actor, parent = actors[0], parents[0]
    is_guardian = isinstance(core_links.parent, GuardianViewSet)
    # Mixed core/Guardian inherits CHANGE_READ and world's real object change grant.
    # Plain/core instead uses default Read=view and a model-level Publisher view grant.
    actor.user_permissions.add(Permission.objects.get(codename="view_book"))
    if not is_guardian:
        actor.user_permissions.add(Permission.objects.get(codename="view_publisher"))
    target = core_links.list
    spy = parent_spy(monkeypatch, target)
    results = {}
    for layer in ("own_access", "rendered"):
        current = django_user_model.objects.get(pk=actor.pk)
        if actor_cache == "warm":
            assert current.has_perm("app.view_book") is True
        reset_discovery(core_links)
        if vocabulary == "warm":
            _ = core_links.parent.permissions, core_links.child.permissions
        spy.reset_mock()
        with CaptureQueriesContext(connection) as capture:
            if layer == "own_access":
                assert target.cv_has_access(current, None) is True
            else:
                assert rendered_data(core_links, renderer, current, parent)["cv_access"] is True
        assert spy.call_count == int(layer == "rendered")
        if layer == "rendered":
            spy.assert_called_once_with(current, parent)
        categories = sql_categories(capture.captured_queries)
        assert categories.get("parent_rows", 0) == categories.get("child_or_relation_rows", 0) == 0
        assert categories.get("actor", 0) == categories.get("other", 0) == 0
        results[layer] = {"total": len(capture), "categories": categories, "helper_calls": spy.call_count}
    if is_guardian:
        assert results["rendered"]["categories"].get("permissions", 0) > 0
        assert results["rendered"]["total"] > results["own_access"]["total"]
    elif vocabulary == "warm":
        assert results["rendered"]["total"] == results["own_access"]["total"]
    report_measurement(
        record_property,
        layer="plain_destination",
        parent_provider="guardian" if is_guardian else "model",
        renderer=renderer,
        actor_cache=actor_cache,
        vocabulary=vocabulary,
        results=results,
    )


@pytest.mark.django_db
@pytest.mark.parametrize("renderer", ["context", "card"])
def test_query_cold_and_warm_discovery(links, world, django_user_model, monkeypatch, record_property, renderer):
    from django.db import connection
    from django.test.utils import CaptureQueriesContext

    actors, parents = world
    actor = django_user_model.objects.get(pk=actors[0].pk)
    parent = parents[0]
    configure(links)
    spy = parent_spy(monkeypatch, links.list)
    reset_discovery(links)
    results = {}
    for temperature in ("cold", "warm"):
        with CaptureQueriesContext(connection) as capture:
            data = rendered_data(links, renderer, actor, parent)
        assert data["cv_access"] is True
        categories = sql_categories(capture.captured_queries)
        assert categories.get("parent_rows", 0) == 0, capture.captured_queries
        assert categories.get("child_or_relation_rows", 0) == 0, capture.captured_queries
        assert categories.get("other", 0) == 0, capture.captured_queries
        results[temperature] = {"total": len(capture), "categories": categories}
    assert spy.call_count == 2
    assert results["cold"]["total"] > results["warm"]["total"]
    report_measurement(record_property, layer="adapter", renderer=renderer, results=results)
    assert results == {
        "cold": {"total": 6, "categories": {"content_type": 2, "permissions": 4}},
        "warm": {"total": 0, "categories": {}},
    }


@pytest.mark.django_db
@pytest.mark.parametrize("size", [0, 1, 3])
@pytest.mark.parametrize("temperature", ["cold", "warm"])
@pytest.mark.parametrize("materialized", [True, False])
def test_query_full_card_page_control(
    links, client, django_user_model, monkeypatch, record_property, size, temperature, materialized
):
    from django.db import connection
    from django.test.utils import CaptureQueriesContext
    from guardian.shortcuts import get_objects_for_user

    actor = django_user_model.objects.create_user(username="page_measurement")
    parents = [Publisher.objects.create(name=f"Measured parent {i}") for i in range(size)]
    for parent in parents:
        for permission in ("view", "change"):
            user_guardian_object_perm(actor, links.parent, permission, parent)
    client.force_login(actor)
    # Registration appends manage even to an empty declaration. This control measures
    # child-link costs; manage membership projection is covered in test_manage.py.
    monkeypatch.setattr(links.card, "cv_context_actions", [])
    if materialized:
        # Isolate rendering supplied objects; the second lane retains the real Guardian host queryset.
        monkeypatch.setattr(links.card, "get_queryset", lambda self: parents)
    _, action = configure(links)
    spy = parent_spy(monkeypatch, links.list)
    host_url = reverse(links.parent.get_router_name("card"))
    results = {}
    for scoped in (False, True):
        links.card.cv_card_actions = [action] if scoped else []
        reset_discovery(links)
        if temperature == "warm":
            # Warm only discovery, not a checker's object-permission cache or request actor.
            _ = links.parent.permissions, links.child.permissions
            get_objects_for_user(actor, links.parent.permissions["view"], Publisher, accept_global_perms=False)
        spy.reset_mock()
        with CaptureQueriesContext(connection) as capture:
            response = client.get(host_url)
        assert response.status_code == 200
        assert spy.call_count == (size if scoped else 0)
        if materialized and scoped:
            assert all(call.args[1] is parent for call, parent in zip(spy.call_args_list, parents, strict=True))
        document = html.fromstring(response.content)
        for parent in parents:
            assert len(document.xpath("//*[@href=$url]", url=child_url(links, "list", parent))) == int(scoped)
        categories = sql_categories(capture.captured_queries)
        assert categories.get("other", 0) == 0, capture.captured_queries
        results["scoped" if scoped else "control"] = {"total": len(capture), "categories": categories}
    control, scoped = results["control"], results["scoped"]
    assert scoped["categories"].get("parent_rows", 0) == control["categories"].get("parent_rows", 0)
    assert scoped["categories"].get("child_or_relation_rows", 0) == 0
    assert control["categories"].get("parent_rows", 0) == (0 if materialized else 1)
    if size == 0:
        assert scoped == control
    else:
        assert scoped["total"] > control["total"]
    report_measurement(
        record_property,
        layer="full_page",
        size=size,
        temperature=temperature,
        materialized=materialized,
        results=results,
        incremental=scoped["total"] - control["total"],
    )


@pytest.mark.django_db
@pytest.mark.parametrize("order", ["distinct", "repeated", "reversed"])
def test_query_card_occurrences_remain_independent(links, world, monkeypatch, record_property, order):
    from django.db import connection
    from django.test.utils import CaptureQueriesContext

    actors, parents = world
    actor = actors[0]
    objects = {"distinct": parents, "repeated": [parents[0], parents[0]], "reversed": list(reversed(parents))}[order]
    configure(links)
    spy = parent_spy(monkeypatch, links.list)
    # Each occurrence evaluates its own decision; loaded grants are shared only
    # for the same user/object, including repeated allowed or denied occurrences.
    _ = links.parent.permissions
    view = bound(links.card, actor)
    monkeypatch.setattr(links.card, "get_queryset", lambda self: objects)
    with CaptureQueriesContext(connection) as capture:
        response = links.card.as_view()(view.request)
        response.render()
    assert response.status_code == 200
    assert spy.call_count == len(objects)
    assert all(call.args[1] is obj for call, obj in zip(spy.call_args_list, objects, strict=True))
    document = html.fromstring(response.content)
    assert len(document.xpath("//*[@href=$url]", url=child_url(links, "list", parents[0]))) == sum(
        obj is parents[0] for obj in objects
    )
    assert document.xpath("//*[@href=$url]", url=child_url(links, "list", parents[1])) == []
    categories = sql_categories(capture.captured_queries)
    assert categories.get("parent_rows", 0) == 0
    assert categories.get("child_or_relation_rows", 0) == 0
    report_measurement(record_property, layer="occurrences", order=order, total=len(capture), categories=categories)


@pytest.mark.django_db
@pytest.mark.parametrize("renderer", ["context", "card"])
def test_query_denied_actors_and_custom_do_no_permission_work(links, world, monkeypatch, record_property, renderer):
    from django.contrib.auth.models import AnonymousUser
    from django.db import connection
    from django.test.utils import CaptureQueriesContext

    actors, parents = world
    spy = parent_spy(monkeypatch, links.list)
    actor = actors[0]
    for reason in ("anonymous", "inactive", "custom"):
        current = AnonymousUser() if reason == "anonymous" else actor
        actor.is_active = reason != "inactive"
        monkeypatch.setattr(links.list, "cv_has_access", Mock(return_value=reason != "custom"))
        with CaptureQueriesContext(connection) as capture:
            assert rendered_data(links, renderer, current, parents[0]) is None
        if reason == "custom":
            spy.assert_called_once_with(current, parents[0])
            report_measurement(
                record_property,
                layer="own_denied",
                renderer=renderer,
                total=len(capture),
                categories=sql_categories(capture.captured_queries),
                helper_calls=spy.call_count,
            )
        else:
            assert len(capture) == 0, capture.captured_queries
            spy.assert_not_called()


@pytest.mark.django_db
@pytest.mark.parametrize("renderer", ["context", "card"])
def test_query_create_uses_only_its_existing_parent_check(links, world, monkeypatch, record_property, renderer):
    from django.db import connection
    from django.test.utils import CaptureQueriesContext

    actors, parents = world
    actor, parent = actors[0], parents[0]
    _ = links.parent.permissions
    spy = parent_spy(monkeypatch, links.create)
    with CaptureQueriesContext(connection) as baseline:
        assert links.create.cv_create_has_access(actor, None, parent) is True
    spy.reset_mock()
    with CaptureQueriesContext(connection) as rendered:
        assert rendered_data(links, renderer, actor, parent, key="create")["cv_access"] is True
    spy.assert_called_once_with(actor, parent)
    report_measurement(
        record_property,
        layer="create_baseline",
        renderer=renderer,
        baseline=len(baseline),
        baseline_categories=sql_categories(baseline.captured_queries),
        rendered=len(rendered),
        categories=sql_categories(rendered.captured_queries),
        helper_calls=spy.call_count,
    )
    assert len(baseline) == 2
    assert sql_categories(baseline.captured_queries) == {"permissions": 2}
    assert len(rendered) == 0
    assert sql_categories(rendered.captured_queries) == {}


@pytest.mark.django_db
def test_query_unaffected_core_and_ordinary_actions(links, world, monkeypatch, record_property):
    from django.db import connection
    from django.test.utils import CaptureQueriesContext

    actors, parents = world
    actor, parent = actors[0], parents[0]
    user_guardian_object_perm(actor, links.parent, "view", parent)

    # The core target retains own policy and checks the real Guardian parent with CHANGE_READ.
    class CoreList(ListViewPermissionRequired):
        pass

    CoreList.cv_viewset = links.child
    monkeypatch.setitem(links.child._views, "list", CoreList)
    monkeypatch.setattr(CoreList, "cv_has_access", Mock(return_value=True))
    parent_check = parent_spy(monkeypatch, CoreList)
    mixed_results = []
    for renderer in ("context", "card"):
        parent_check.reset_mock()
        with CaptureQueriesContext(connection) as capture:
            assert rendered_data(links, renderer, actor, parent)["cv_access"] is True
        parent_check.assert_called_once_with(actor, parent)
        categories = sql_categories(capture.captured_queries)
        mixed_results.append({"total": len(capture), "categories": categories})
        assert categories.get("parent_rows", 0) == categories.get("child_or_relation_rows", 0) == 0
        report_measurement(
            record_property,
            layer="mixed_core_guardian",
            renderer=renderer,
            total=len(capture),
            categories=categories,
            helper_calls=parent_check.call_count,
        )

    # Both grants were prepared before the mixed loop loaded this parent's grants.
    # Direct and rendered ordinary actions reuse that same actor's loaded grants.
    _ = links.parent.permissions
    view = bound(links.card, actor)
    parent_check.reset_mock()
    with CaptureQueriesContext(connection) as baseline:
        assert links.detail.cv_has_access(actor, parent) is True
    with CaptureQueriesContext(connection) as rendered:
        assert view.cv_get_card_action_data(CardAction(key="detail"), parent, actor)["cv_access"] is True
    assert len(rendered) == len(baseline) == 0
    assert sql_categories(rendered.captured_queries) == sql_categories(baseline.captured_queries) == {}
    parent_check.assert_not_called()
    report_measurement(
        record_property,
        layer="ordinary_baseline",
        baseline=len(baseline),
        baseline_categories=sql_categories(baseline.captured_queries),
        rendered=len(rendered),
        categories=sql_categories(rendered.captured_queries),
        helper_calls=parent_check.call_count,
    )
    assert mixed_results == [
        {"total": 2, "categories": {"permissions": 2}},
        {"total": 0, "categories": {}},
    ]
