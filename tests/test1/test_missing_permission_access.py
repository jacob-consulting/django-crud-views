"""Missing core declarations deny presentation without replacing request diagnostics."""

import sys
import types
import uuid
from types import SimpleNamespace

import pytest
from django.test import override_settings
from django.urls import clear_url_caches, include, path, reverse
from lxml import html

from crud_views.lib import check as check_module
from crud_views.lib.views import DetailViewPermissionRequired, ListViewPermissionRequired
from crud_views.lib.viewset import _REGISTRY, _REGISTRY_LOCK, ViewSet
from tests.lib.helper.user import user_viewset_permission
from tests.test1.app.models import Publisher


@pytest.fixture
def permission_routes():
    suffix = uuid.uuid4().hex
    name = f"missingpermission{suffix}"
    module_name = f"tests.test1._missing_permission_urls_{suffix}"
    vocabulary = dict(check_module._VOCAB_CACHE)
    try:
        viewset = ViewSet(model=Publisher, name=name, icon_header="fa-solid fa-book")

        class TargetList(ListViewPermissionRequired):
            cv_viewset = viewset
            cv_permission = "undeclared_action"

        class HostDetail(DetailViewPermissionRequired):
            cv_viewset = viewset
            cv_context_actions = ["list"]

        module = types.ModuleType(module_name)
        module.urlpatterns = [*viewset.urlpatterns, path("", include("tests.test1.project.urls"))]
        sys.modules[module_name] = module
        with override_settings(ROOT_URLCONF=module_name):
            clear_url_caches()
            yield SimpleNamespace(viewset=viewset, target=TargetList, host=HostDetail)
    finally:
        with _REGISTRY_LOCK:
            _REGISTRY.pop(name, None)
        check_module._VOCAB_CACHE.clear()
        check_module._VOCAB_CACHE.update(vocabulary)
        sys.modules.pop(module_name, None)
        clear_url_caches()


@pytest.mark.django_db
@pytest.mark.parametrize("mode", ["hide", "disable"])
def test_core_permission_rendered_tracer(permission_routes, client, django_user_model, monkeypatch, mode):
    routes = permission_routes
    publisher = Publisher.objects.create(name="Permission host")
    user = django_user_model.objects.create_user(username="permission_host")
    user_viewset_permission(user, routes.viewset, "view")
    client.force_login(user)
    monkeypatch.setattr(routes.target, "cv_inaccessible_actions", mode)
    host_url = reverse(routes.viewset.get_router_name("detail"), kwargs={"pk": publisher.pk})
    target_url = reverse(routes.viewset.get_router_name("list"))

    response = client.get(host_url)
    assert response.status_code == 200
    buttons = [button for button in response.context["view"].cv_get_context_buttons() if button["cv_key"] == "list"]
    nodes = html.fromstring(response.content).cssselect('[cv-context-container] [cv-key="list"]')
    if mode == "hide":
        assert buttons == []
        assert nodes == []
    else:
        (button,) = buttons
        assert button["cv_disabled"] is True
        assert button["cv_disabled_reason"] == "permission"
        assert button["cv_url"] is None
        (node,) = nodes
        assert node.tag == "button"
        assert node.get("disabled") is not None
        assert node.get("data-cv-disabled") == "permission"
        for attribute in ("href", "data-cv-modal", "onclick", "formaction"):
            assert node.get(attribute) is None
    assert target_url not in response.content.decode()

    with pytest.raises(AssertionError, match=r"permission undeclared_action not found.*migrate.*restart"):
        client.get(target_url)

    monkeypatch.setattr(routes.target, "cv_permission", "view")
    response = client.get(host_url)
    assert response.status_code == 200
    (button,) = [button for button in response.context["view"].cv_get_context_buttons() if button["cv_key"] == "list"]
    assert button["cv_disabled"] is False
    assert button["cv_url"] == target_url
    (node,) = html.fromstring(response.content).cssselect('[cv-context-container] [cv-key="list"]')
    assert node.get("href") == target_url
    assert client.get(target_url).status_code == 200
