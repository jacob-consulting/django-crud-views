"""Explicit-parent collection links: request parity, preserved policy and measured SQL."""

import sys
import types
import uuid
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from django.test import RequestFactory, override_settings
from django.urls import clear_url_caches, include, path, resolve, reverse
from lxml import html

from crud_views.lib import check as check_module
from crud_views.lib.crispy import CrispyViewMixin
from crud_views.lib.view import CardAction, ChildContextButton
from crud_views.lib.view.visibility import cv_resolve_action
from crud_views.lib.views import CreateViewParentMixin, ListViewPermissionRequired
from crud_views.lib.viewset import _REGISTRY, _REGISTRY_LOCK, ParentViewSet
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
            cv_guardian_parent_permission="change",
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
    response = client.get(host_url)
    assert response.status_code == 200
    assert html.fromstring(response.content).xpath("//*[@href=$url]", url=destination)
    assert rendered_data(links, renderer, actor, parent, key=target_key)["cv_url"] == destination
    response = client.get(destination)
    assert response.status_code == 200
    assert list(response.context["object_list"]) == []


def parent_spy(monkeypatch, target):
    spy = Mock(wraps=target._guardian_user_has_parent_perm)
    monkeypatch.setattr(target, "_guardian_user_has_parent_perm", spy)
    return spy


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
@pytest.mark.parametrize("accept_global", [False, True])
def test_preservation_permission_channels(links, django_user_model, monkeypatch, renderer, grant, accept_global):
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
    monkeypatch.setattr(links.list, "cv_guardian_accept_global_perms", accept_global)
    allowed = grant in {"object", "group", "superuser"} or (grant == "global" and accept_global)
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
    monkeypatch.setattr(links.child, "cv_guardian_parent_permission", None)
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
    assert data["cv_action_enabled"] is enabled
    assert data["cv_disabled"] is not (active and enabled)
    if data["cv_disabled"]:
        assert data["cv_url"] is None
        assert data["cv_disabled_reason"] == ("state" if active else "permission")
    assert spy.call_count == int(active)
    assert access.call_count == int(active)
    state.assert_called_once_with(actor, parent)


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
    access.assert_called_once_with(actor, parent)
    assert access.call_args.args[1] is parent
    assert spy.call_count == int(allow)


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
    assert not hasattr(QuerysetOnly, "_guardian_user_has_parent_perm")
    parent = Publisher.objects.create(name="No parent grant")
    actor = django_user_model.objects.create_user(username="queryset_only")
    client.force_login(actor)
    data = rendered_data(links, renderer, actor, parent)
    assert data["cv_url"] == child_url(links, "list", parent)
    response = client.get(data["cv_url"])
    assert response.status_code == 200
    assert list(response.context["object_list"]) == []

    access = Mock(return_value=False)
    monkeypatch.setattr(QuerysetOnly, "cv_has_access", access)
    assert rendered_data(links, renderer, actor, parent) is None
    assert access.call_args.args[1] is parent
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
    actor = django_user_model.objects.create_user(username="inherited")
    actor.user_permissions.add(Permission.objects.get(codename="change_publisher"))
    parent = Publisher.objects.create(name="Inherited policy")
    assert rendered_data(links, "context", actor, parent)["cv_access"] is True


@pytest.mark.django_db
@pytest.mark.parametrize("allow", [False, True])
def test_preservation_top_level_delegates_without_actor_or_parent_gate(links, monkeypatch, allow):
    from django.contrib.auth.models import AnonymousUser

    actor = AnonymousUser()
    access = Mock(return_value=allow)
    monkeypatch.setattr(links.card, "cv_has_access", access)
    parent = Publisher(name="Supplied original")
    spy = parent_spy(monkeypatch, links.card)
    assert links.card._cv_child_link_has_access(actor, parent) is allow
    access.assert_called_once_with(actor, parent)
    spy.assert_not_called()


@pytest.mark.django_db
@pytest.mark.parametrize("renderer", ["context", "card"])
@pytest.mark.parametrize("policy", ["explicit", "fallback", "none", "global"])
@pytest.mark.parametrize("enabled", [False, True])
def test_preservation_create_policy_once(links, world, monkeypatch, renderer, policy, enabled):
    from django.contrib.auth.models import Permission

    actors, parents = world
    actor, parent = actors[0], parents[0]
    monkeypatch.setattr(links.child, "cv_guardian_parent_permission", None if policy == "none" else "change")
    monkeypatch.setattr(links.child, "cv_guardian_parent_create_permission", "view" if policy == "explicit" else None)
    if policy == "explicit":
        user_guardian_object_perm(actor, links.parent, "view", parent)
    if policy == "global":
        actor = actors[1]  # no object grant on this parent
        actor.user_permissions.add(Permission.objects.get(codename="change_publisher"))
        monkeypatch.setattr(links.create, "cv_guardian_accept_global_perms", True, raising=False)
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
    monkeypatch.setattr(links.create, "cv_has_access", access)
    spy.reset_mock()
    data = rendered_data(links, renderer, actor, parent, key="create")
    assert data["cv_disabled_reason"] == "permission"
    assert access.call_args.args[1] is parent
    spy.assert_not_called()


@pytest.mark.django_db
@pytest.mark.parametrize("renderer", ["context", "card"])
def test_preservation_interleaved_create_custom_and_collection(links, world, monkeypatch, renderer):
    actors, parents = world
    actor, parent = actors[0], parents[0]
    monkeypatch.setattr(links.child, "cv_guardian_parent_create_permission", "view")
    custom = Mock(return_value=False)
    monkeypatch.setattr(links.target_card, "cv_has_access", custom)
    for key in ["list", "create", "card", "list", "card", "create"]:
        assert (rendered_data(links, renderer, actor, parent, key=key) is not None) is (key == "list")
    assert custom.call_count == 2
    assert all(call.args[1] is parent for call in custom.call_args_list)


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
        child.cv_guardian_parent_permission = "change"
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
        spy = Mock(wraps=target.cv_has_access)
        monkeypatch.setattr(target, "cv_has_access", spy)
    else:
        spy = parent_spy(monkeypatch, target)
    for parent in parents:
        result = rendered_data(links, renderer, actor, parent, child=child)
        assert spy.call_args.args[1] is parent
        allowed = kind == "core" or parent is parents[0]
        assert (result is not None) is allowed
        if allowed:
            assert resolve(result["cv_url"]).kwargs[child.parent.get_pk_name()] == str(parent.pk)
            if kind == "m2m":
                client.force_login(actor)
                response = client.get(result["cv_url"])
                assert response.status_code == 200
                assert list(response.context["object_list"]) == []


@pytest.mark.django_db
def test_preservation_ordinary_row_and_sibling_actions(links, world, monkeypatch):
    from crud_views.lib.view import ContextButton, SiblingContextButton

    actors, parents = world
    actor, parent = actors[0], parents[0]
    # Ordinary row actions retain object access, without entering the new child hook.
    user_guardian_object_perm(actor, links.parent, "view", parent)
    hook = Mock(side_effect=AssertionError("ordinary path entered child adapter"))
    monkeypatch.setattr(links.detail, "_cv_child_link_has_access", hook)
    view = bound(links.card, actor)
    row = view.cv_get_card_action_data(CardAction(key="detail"), parent, actor)
    assert row["cv_access"] is True
    assert resolve(row["cv_url"].split("?")[0]).kwargs["pk"] == str(parent.pk)
    own = ContextButton(key="detail", key_target="detail").get_context(view.cv_get_view_context(object=parent))
    assert own["cv_access"] is True
    hook.assert_not_called()

    # A sibling collection remains on its pre-existing general access path (outside this fix).
    monkeypatch.setattr(links.list, "_cv_child_link_has_access", hook)
    sibling = SiblingContextButton(key="sibling", sibling_name=links.child.name)
    host = bound(links.target_card, actor)
    host.kwargs = {links.child.parent.get_pk_name(): parents[1].pk}
    data = sibling.get_context(host.cv_get_view_context())
    assert data["cv_access"] is True
    assert resolve(data["cv_url"]).kwargs[links.child.parent.get_pk_name()] == str(parents[1].pk)
    hook.assert_not_called()


@pytest.mark.django_db
@pytest.mark.parametrize("renderer", ["context", "card"])
def test_preservation_existing_parent_declaration_error_propagates(links, world, monkeypatch, renderer):
    actors, parents = world
    monkeypatch.setattr(links.child, "cv_guardian_parent_permission", "undeclared")
    with pytest.raises(AttributeError, match="split"):
        rendered_data(links, renderer, actors[0], parents[0])
