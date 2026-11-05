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
from crud_views.lib.view import CardAction, ChildContextButton
from crud_views.lib.view.visibility import cv_resolve_action
from crud_views.lib.viewset import _REGISTRY, _REGISTRY_LOCK, ParentViewSet
from crud_views_guardian.lib.views import (
    GuardianCardListViewPermissionRequired,
    GuardianDetailViewPermissionRequired,
    GuardianListViewPermissionRequired,
)
from crud_views_guardian.lib.viewset import GuardianViewSet
from tests.lib.helper.guardian import user_guardian_object_perm
from tests.test1.app.models import Book, Publisher


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
def test_parity_child_collection(links, client, django_user_model, monkeypatch):
    renderer, target_key, mode = "context", "list", "disable"
    parent = Publisher.objects.create(name="Viewable parent")
    actor = django_user_model.objects.create_user(username="parent_viewer")
    user_guardian_object_perm(actor, links.parent, "view", parent)
    client.force_login(actor)
    configure(links, target_key)
    target = links.child.get_view_class(target_key)
    monkeypatch.setattr(target, "cv_inaccessible_actions", mode)
    host_url = reverse(links.parent.get_router_name("detail"), kwargs={"pk": parent.pk})
    destination = child_url(links, target_key, parent)

    assert client.get(destination).status_code == 403
    response = client.get(host_url)
    assert response.status_code == 200
    data = rendered_data(links, renderer, actor, parent, key=target_key)
    assert data["cv_disabled"] is True
    assert data["cv_disabled_reason"] == "permission"
    assert data["cv_url"] is None
    document = html.fromstring(response.content)
    assert document.xpath("//*[@href=$url]", url=destination) == []
    (node,) = document.cssselect('[cv-context-container] [cv-key="list"]')
    assert node.tag == "button"
    assert node.get("data-cv-disabled") == "permission"
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
