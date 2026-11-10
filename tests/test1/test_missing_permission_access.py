"""Missing core declarations deny presentation without replacing request diagnostics."""

import sys
import types
import uuid
from types import SimpleNamespace
from unittest.mock import Mock

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
@pytest.mark.parametrize("state_enabled", [False, True])
def test_core_permission_rendered_tracer(
    permission_routes, client, django_user_model, monkeypatch, mode, state_enabled
):
    routes = permission_routes
    publisher = Publisher.objects.create(name="Permission host")
    user = django_user_model.objects.create_user(username="permission_host")
    user_viewset_permission(user, routes.viewset, "view")
    client.force_login(user)
    monkeypatch.setattr(routes.target, "cv_inaccessible_actions", mode)
    monkeypatch.setattr(routes.target, "cv_action_enabled", classmethod(lambda cls, user, obj=None: state_enabled))
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
    assert html.fromstring(response.content).xpath("//*[@href=$url]", url=target_url) == []

    with pytest.raises(AssertionError, match=r"permission undeclared_action not found.*migrate.*restart"):
        client.get(target_url)

    monkeypatch.setattr(routes.target, "cv_permission", "view")
    monkeypatch.setattr(routes.target, "cv_action_enabled", classmethod(lambda cls, user, obj=None: True))
    response = client.get(host_url)
    assert response.status_code == 200
    (button,) = [button for button in response.context["view"].cv_get_context_buttons() if button["cv_key"] == "list"]
    assert button["cv_disabled"] is False
    assert button["cv_url"] == target_url
    (node,) = html.fromstring(response.content).cssselect('[cv-context-container] [cv-key="list"]')
    assert node.get("href") == target_url
    assert client.get(target_url).status_code == 200


@pytest.fixture(params=["ordinary", "anonymous", "superuser"])
def actor(request, django_user_model):
    from django.contrib.auth.models import AnonymousUser

    if request.param == "anonymous":
        return AnonymousUser()
    return django_user_model.objects.create_user(username=request.param, is_superuser=request.param == "superuser")


@pytest.mark.django_db
@pytest.mark.parametrize("declaration", ["empty", "missing-key", "empty-string", "none", "false"])
def test_missing_declaration_never_checks_actor_permissions(permission_routes, actor, declaration, monkeypatch):
    routes = permission_routes
    mappings = {
        "empty": {},
        "missing-key": {"view": "app.view_publisher"},
        "empty-string": {"undeclared_action": ""},
        "none": {"undeclared_action": None},
        "false": {"undeclared_action": False},
    }
    monkeypatch.setattr(routes.viewset, "_default_permissions", mappings[declaration])
    has_perms = Mock(wraps=actor.has_perms)
    monkeypatch.setattr(actor, "has_perms", has_perms)
    assert routes.target.cv_has_access(actor) is False
    has_perms.assert_not_called()
    with pytest.raises(AssertionError, match=r"permission undeclared_action not found.*migrate.*restart"):
        _ = routes.target().permission_required


@pytest.mark.django_db
@pytest.mark.parametrize("grant", [False, True])
def test_declared_permission_retains_actor_result(permission_routes, actor, grant, monkeypatch):
    routes = permission_routes
    monkeypatch.setattr(routes.target, "cv_permission", "view")
    if grant and actor.is_authenticated:
        user_viewset_permission(actor, routes.viewset, "view")
    has_perms = Mock(wraps=actor.has_perms)
    monkeypatch.setattr(actor, "has_perms", has_perms)
    expected = actor.is_authenticated and (actor.is_superuser or grant)
    assert routes.target.cv_has_access(actor) is expected
    has_perms.assert_called_once_with((routes.viewset.permissions["view"],))
    assert routes.target().permission_required == routes.viewset.permissions["view"]


@pytest.mark.django_db
def test_empty_permission_mapping_recovers_on_same_viewset(permission_routes, django_user_model, monkeypatch):
    from django.apps import apps
    from django.contrib.auth.management import create_permissions
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType

    routes = permission_routes
    monkeypatch.setattr(routes.target, "cv_permission", "view")
    content_type = ContentType.objects.get_for_model(Publisher)
    Permission.objects.filter(content_type=content_type).delete()
    user = django_user_model.objects.create_user(username="permission_recovery")
    assert routes.viewset.permissions == {}
    assert routes.target.cv_has_access(user) is False
    with pytest.raises(AssertionError, match=r"permission view not found.*migrate.*restart"):
        _ = routes.target().permission_required

    create_permissions(apps.get_app_config(Publisher._meta.app_label), verbosity=0)
    user_viewset_permission(user, routes.viewset, "view")
    fresh_user = django_user_model.objects.get(pk=user.pk)
    assert routes.target.cv_has_access(fresh_user) is True
    assert routes.target().permission_required == f"{content_type.app_label}.view_publisher"


@pytest.mark.django_db
def test_populated_permission_mapping_keeps_existing_cache_policy(permission_routes):
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType

    viewset = permission_routes.viewset
    populated = viewset.permissions
    assert "view" in populated
    Permission.objects.filter(content_type=ContentType.objects.get_for_model(Publisher)).delete()
    assert viewset.permissions is populated
    assert "view" in viewset.permissions


@pytest.mark.django_db
def test_alternating_actors_and_viewsets_keep_access_local(permission_routes, django_user_model):
    allowed = django_user_model.objects.create_user(username="alternating_allowed")
    denied = django_user_model.objects.create_user(username="alternating_denied")
    user_viewset_permission(allowed, permission_routes.viewset, "view")
    name = f"declaredpermission{uuid.uuid4().hex}"
    try:
        declared = ViewSet(model=Publisher, name=name)

        class DeclaredList(ListViewPermissionRequired):
            cv_viewset = declared

        for user, target, expected in [
            (allowed, DeclaredList, True),
            (allowed, permission_routes.target, False),
            (denied, DeclaredList, False),
            (denied, permission_routes.target, False),
            (allowed, DeclaredList, True),
            (allowed, permission_routes.target, False),
        ]:
            assert target.cv_has_access(user) is expected
    finally:
        with _REGISTRY_LOCK:
            _REGISTRY.pop(name, None)


@pytest.mark.parametrize("declared", [False, True])
def test_resource_missing_key_diagnostic_is_preserved(permission_routes, declared):
    from tests.test1.test_resource_viewset import T5Item, check_error_ids

    name = f"resourcepermission{uuid.uuid4().hex}"
    try:
        viewset = ViewSet(
            model=T5Item, name=name, resource_permissions={"view": "app.view_s3file"} if declared else None
        )

        class ResourceList(ListViewPermissionRequired):
            cv_viewset = viewset

        assert ("viewset.E260" in check_error_ids(viewset)) is not declared
    finally:
        with _REGISTRY_LOCK:
            _REGISTRY.pop(name, None)


def test_undeclared_action_fixture_yields_one_e269(permission_routes):
    from crud_views.checks import check_ancestor_declarations

    ours = [m for m in check_ancestor_declarations() if m.id == "viewset.E269" and m.obj is permission_routes.viewset]
    assert len(ours) == 1
    assert ours[0].msg == "cv_permission 'undeclared_action' of view 'list' is not declared on model app.Publisher"
    assert 'add ("undeclared_action_publisher", "...") to Publisher.Meta.permissions' in ours[0].hint
