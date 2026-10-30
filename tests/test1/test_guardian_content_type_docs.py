"""Run the published configured-content-type recipe with independent actors and rows."""

import sys
from types import ModuleType

import pytest
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.test import override_settings
from django.urls import clear_url_caches, include, path, reverse
from guardian.conf import settings as guardian_settings
from guardian.models import UserObjectPermission

from crud_views.lib import check as check_module
from crud_views.lib.viewset import _REGISTRY, _REGISTRY_LOCK
from tests.test1.app.models import Car, Vehicle
from tests.test1.test_delete_migration_docs import MIGRATION, _recipe

HEADING = "### Guardian configured content-type permissions"


@pytest.fixture
def published_guardian_recipe(db, monkeypatch):
    registry = dict(_REGISTRY)
    vocabulary = dict(check_module._VOCAB_CACHE)
    permissions = [(vs, vs._default_permissions) for vs in registry.values()]
    content_types = {alias: dict(rows) for alias, rows in ContentType.objects._cache.items()}
    package = ModuleType("myapp")
    package.__path__ = []
    models = ModuleType("myapp.models")
    models.Car, models.Vehicle = Car, Vehicle
    urls = ModuleType("myapp.guardian_recipe_urls")
    for module in (package, models, urls):
        monkeypatch.setitem(sys.modules, module.__name__, module)
    monkeypatch.setattr(
        guardian_settings, "GET_CONTENT_TYPE", "polymorphic.contrib.guardian.get_polymorphic_base_content_type"
    )
    ContentType.objects.clear_cache()

    def execute():
        assert HEADING in MIGRATION.read_text(), "Publish the configured-content-type migration before using it"
        namespace = {"__name__": "myapp.viewsets"}
        exec(compile(_recipe(HEADING)[0], str(MIGRATION), "exec"), namespace)
        urls.urlpatterns = [*namespace["cv_car"].urlpatterns, path("", include("tests.test1.project.urls"))]
        clear_url_caches()
        return namespace

    try:
        with override_settings(ROOT_URLCONF=urls.__name__):
            yield execute
    finally:
        clear_url_caches()
        with _REGISTRY_LOCK:
            _REGISTRY.clear()
            _REGISTRY.update(registry)
        check_module._VOCAB_CACHE.clear()
        check_module._VOCAB_CACHE.update(vocabulary)
        for viewset, cached in permissions:
            viewset._default_permissions = cached
        ContentType.objects.clear_cache()
        ContentType.objects._cache.update(content_types)


@pytest.mark.parametrize("repeat", range(2))
def test_documented_guardian_content_type_migration(published_guardian_recipe, client, repeat):
    recipe = published_guardian_recipe()
    viewset = recipe["cv_car"]
    user = User.objects.create_user(username=f"documented_car_reader_{repeat}")
    other = User.objects.create_user(username=f"documented_other_reader_{repeat}")
    granted = Car.objects.create(name="Granted car", doors=4)
    sibling = Car.objects.create(name="Ungranted car", doors=4)
    outside = Car.objects.create(name="Outside caller scope", doors=2)
    assert viewset.permissions["view"] == "app.view_vehicle"
    assert not viewset.get_objects_for_user(user, "view").exists()
    selected = recipe["grant_car_view"](user, granted.pk)
    assert isinstance(selected, Car) and selected.pk == granted.pk
    recipe["grant_car_view"](other, sibling.pk)
    recipe["grant_car_view"](user, outside.pk)
    grant = UserObjectPermission.objects.get(user=user, object_pk=str(granted.pk))
    assert grant.permission.codename == "view_vehicle"
    assert grant.content_type == ContentType.objects.get_for_model(Vehicle)
    scope = Car.objects.using("default").filter(doors=4)
    visible = recipe["visible_cars"](user, scope)
    assert visible.model is Car and visible.db == scope.db
    assert list(visible) == [granted] and isinstance(visible[0], Car)
    assert not recipe["visible_cars"](user, scope.none()).exists()
    client.force_login(user)
    url = reverse(viewset.get_router_name("list"))
    response = client.get(url)
    assert response.status_code == 200
    assert {obj.pk for obj in response.context["object_list"]} == {granted.pk, outside.pk}
    recipe["revoke_car_view"](user, granted)
    recipe["revoke_car_view"](user, outside)
    assert not UserObjectPermission.objects.filter(user=user).exists()
    assert not recipe["visible_cars"](user, scope).exists()
    assert list(client.get(url).context["object_list"]) == []
    assert Car.objects.filter(pk__in=[granted.pk, sibling.pk, outside.pk]).count() == 3


def test_documented_guardian_custom_permission_namespace(published_guardian_recipe):
    Permission.objects.create(
        content_type=ContentType.objects.get_for_model(Vehicle),
        codename="inspect_status_vehicle",
        name="Inspect status",
    )
    Permission.objects.create(
        content_type=ContentType.objects.get_for_model(Car), codename="child_only_car", name="Child only"
    )
    viewset = published_guardian_recipe()["cv_car"]
    assert viewset.permissions["inspect_status"] == "app.inspect_status_vehicle"
    assert "child_only" not in viewset.permissions
    user = User.objects.create_user(username="documented_custom_reader")
    with pytest.raises(ValueError) as error:
        viewset.get_objects_for_user(user, "child_only")
    assert str(error.value) == (
        "Invalid permission key 'child_only'. Valid keys: 'add', 'change', 'delete', 'inspect_status', 'view'."
    )
