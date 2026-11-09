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
    """Record ``(user, parent)`` for every bounded immediate-parent gate evaluated on behalf of ``target`` (the
    Guardian link and create helpers call ``_immediate_parent_access`` through these two modules)."""
    from crud_views_guardian.lib import mixins, views

    spy = Mock()
    for module in (mixins, views):

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
    monkeypatch.setattr(links.child, "ancestor_policy", AncestorPolicy(read=CHANGE, actions={"create": VIEW}))
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
        assert categories.get("permissions", 0) > 0, capture.captured_queries
        assert categories.get("other", 0) == 0, capture.captured_queries
        results[temperature] = {"total": len(capture), "categories": categories}
    assert spy.call_count == 2
    assert results["cold"]["total"] > results["warm"]["total"]
    report_measurement(record_property, layer="adapter", renderer=renderer, results=results)


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
    # Both positive and negative decisions use a fresh checker each time.
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
def test_query_denied_actors_and_custom_do_no_permission_work(links, world, monkeypatch, renderer):
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
        assert len(capture) == 0, capture.captured_queries
    spy.assert_not_called()


@pytest.mark.django_db
@pytest.mark.parametrize("renderer", ["context", "card"])
def test_query_create_uses_only_its_existing_parent_check(links, world, monkeypatch, renderer):
    from django.db import connection
    from django.test.utils import CaptureQueriesContext

    actors, parents = world
    actor, parent = actors[0], parents[0]
    _ = links.parent.permissions
    spy = parent_spy(monkeypatch, links.create)
    with CaptureQueriesContext(connection) as baseline:
        assert links.create.cv_has_access(actor, parent) is True
    spy.reset_mock()
    with CaptureQueriesContext(connection) as rendered:
        assert rendered_data(links, renderer, actor, parent, key="create")["cv_access"] is True
    spy.assert_called_once_with(actor, parent)
    assert sql_categories(rendered.captured_queries) == sql_categories(baseline.captured_queries)
    assert len(rendered) == len(baseline)


@pytest.mark.django_db
def test_query_unaffected_core_and_ordinary_actions(links, world, monkeypatch):
    from django.db import connection
    from django.test.utils import CaptureQueriesContext

    actors, parents = world
    actor, parent = actors[0], parents[0]
    target = links.list

    # A core target delegates the original custom policy without any parent machinery.
    class CoreList(ListViewPermissionRequired):
        pass

    CoreList.cv_viewset = links.child
    monkeypatch.setitem(links.child._views, "list", CoreList)
    monkeypatch.setattr(CoreList, "cv_has_access", Mock(return_value=True))
    parent_check = parent_spy(monkeypatch, target)
    for renderer in ("context", "card"):
        with CaptureQueriesContext(connection) as capture:
            assert rendered_data(links, renderer, actor, parent)["cv_access"] is True
        assert len(capture) == 0
    parent_check.assert_not_called()

    # Ordinary Guardian row action cost is unchanged relative to the original access call.
    user_guardian_object_perm(actor, links.parent, "view", parent)
    _ = links.parent.permissions
    view = bound(links.card, actor)
    with CaptureQueriesContext(connection) as baseline:
        assert links.detail.cv_has_access(actor, parent) is True
    with CaptureQueriesContext(connection) as rendered:
        assert view.cv_get_card_action_data(CardAction(key="detail"), parent, actor)["cv_access"] is True
    assert len(rendered) == len(baseline)
    assert sql_categories(rendered.captured_queries) == sql_categories(baseline.captured_queries)
