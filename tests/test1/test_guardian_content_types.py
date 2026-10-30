"""Configured Guardian identity must drive defaults without widening caller scope or policy."""

import sys
import uuid
from types import ModuleType, SimpleNamespace

import pytest
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.test import override_settings
from django.urls import clear_url_caches, include, path, reverse
from guardian.conf import settings as guardian_settings
from guardian.shortcuts import assign_perm

from crud_views.lib import check as check_module
from crud_views.lib.viewset import _REGISTRY, _REGISTRY_LOCK
from crud_views_guardian.lib.views import GuardianDetailViewPermissionRequired, GuardianListViewPermissionRequired
from crud_views_guardian.lib.viewset import GuardianViewSet
from tests.test1.app.models import Car

BASE_CT = "polymorphic.contrib.guardian.get_polymorphic_base_content_type"
DEFAULT_CT = "guardian.ctypes.get_default_content_type"


@pytest.fixture
def ct_routes(db, monkeypatch):
    """Restore routes, settings, registry and permission/content-type caches after disposable grants."""
    registry = dict(_REGISTRY)
    vocabulary = dict(check_module._VOCAB_CACHE)
    permissions = [(vs, vs._default_permissions) for vs in registry.values()]
    content_types = {alias: dict(rows) for alias, rows in ContentType.objects._cache.items()}
    module = ModuleType(f"tests.test1._ct_urls_{uuid.uuid4().hex}")
    monkeypatch.setitem(sys.modules, module.__name__, module)
    monkeypatch.setattr(guardian_settings, "GET_CONTENT_TYPE", BASE_CT)
    patterns = []

    def build(model=Car, viewset_class=GuardianViewSet):
        viewset = viewset_class(model=model, name=f"ct{uuid.uuid4().hex}")

        class List(GuardianListViewPermissionRequired):
            cv_viewset = viewset

        class GlobalList(GuardianListViewPermissionRequired):
            cv_viewset = viewset
            cv_key = "global_list"
            cv_path = "global/"
            cv_guardian_accept_global_perms = True

        class Detail(GuardianDetailViewPermissionRequired):
            cv_viewset = viewset

        class GlobalDetail(GuardianDetailViewPermissionRequired):
            cv_viewset = viewset
            cv_key = "global_detail"
            cv_path = "global/"
            cv_guardian_accept_global_perms = True

        patterns.extend(viewset.urlpatterns)
        module.urlpatterns = [*patterns, path("", include("tests.test1.project.urls"))]
        clear_url_caches()
        return SimpleNamespace(viewset=viewset, List=List, GlobalList=GlobalList, Detail=Detail, GlobalDetail=GlobalDetail)

    ContentType.objects.clear_cache()
    try:
        with override_settings(ROOT_URLCONF=module.__name__):
            clear_url_caches()
            yield build
    finally:
        clear_url_caches()
        with _REGISTRY_LOCK:
            _REGISTRY.clear()
            _REGISTRY.update(registry)
        check_module._VOCAB_CACHE.clear()
        check_module._VOCAB_CACHE.update(vocabulary)
        for vs, cached in permissions:
            vs._default_permissions = cached
        ContentType.objects.clear_cache()
        ContentType.objects._cache.update(content_types)


def _url(routes, key, **kwargs):
    return reverse(routes.viewset.get_router_name(key), kwargs=kwargs)


def _pks(queryset):
    return sorted(obj.pk for obj in queryset)


@pytest.mark.parametrize("path_kind", ["helper", "request"])
def test_configured_base_content_type_registered_access(ct_routes, client, path_kind):
    granted = Car.objects.create(name="Granted Car", doors=4)
    sibling = Car.objects.create(name="Ungranted Car", doors=4)
    user = User.objects.create_user(username="ct_granted")
    routes = ct_routes()
    assign_perm("view_vehicle", user, granted)

    if path_kind == "helper":
        scope = Car.objects.using("default").filter(pk__in=[granted.pk, sibling.pk]).order_by("pk")
        result = routes.viewset.get_objects_for_user(user, "view", qs=scope)
        assert result.model is Car and result.db == scope.db
        assert _pks(result) == [granted.pk]
        assert not routes.viewset.get_objects_for_user(user, "view", qs=scope.filter(pk=sibling.pk)).exists()
        assert not routes.viewset.get_objects_for_user(user, "view", qs=scope.none()).exists()
    else:
        client.force_login(user)
        response = client.get(_url(routes, "list"))
        assert response.status_code == 200
        assert response.context["object_list"].model is Car
        assert _pks(response.context["object_list"]) == [granted.pk]
        assert "Granted Car" in response.content.decode()
        assert "Ungranted Car" not in response.content.decode()
    assert routes.viewset.permissions["view"] == "app.view_vehicle"
