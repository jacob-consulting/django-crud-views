"""Configured Guardian identity must drive defaults without widening caller scope or policy."""

import sys
import uuid
from collections import OrderedDict
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock

import pytest
from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType
from django.test import override_settings
from django.urls import clear_url_caches, include, path, reverse
from guardian.conf import settings as guardian_settings
from guardian.exceptions import MixedContentTypeError
from guardian.models import GroupObjectPermission, UserObjectPermission
from guardian.shortcuts import assign_perm

from crud_views.lib import check as check_module
from crud_views.lib.viewset import _REGISTRY, _REGISTRY_LOCK, ViewSet
from crud_views_guardian.lib.views import GuardianDetailViewPermissionRequired, GuardianListViewPermissionRequired
from crud_views_guardian.lib.viewset import GuardianViewSet
from tests.test1.app.models import Car, Publisher, PublisherProxy, Vehicle

BASE_CT = "polymorphic.contrib.guardian.get_polymorphic_base_content_type"
DEFAULT_CT = "guardian.ctypes.get_default_content_type"
ALLOW_INACTIVE = "django.contrib.auth.backends.AllowAllUsersModelBackend"


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
        return SimpleNamespace(
            viewset=viewset, List=List, GlobalList=GlobalList, Detail=Detail, GlobalDetail=GlobalDetail
        )

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


@pytest.mark.parametrize("actor", ["object", "group", "global", "superuser", "ungranted"])
@pytest.mark.parametrize("active", [True, False])
def test_configured_content_type_actor_policy(ct_routes, client, actor, active):
    class ScopedViewSet(GuardianViewSet):
        def get_queryset(self, view):
            return super().get_queryset(view).using("default").filter(doors=4).order_by("pk")

    granted = Car.objects.create(name="Inside granted", doors=4)
    sibling = Car.objects.create(name="Inside ungranted", doors=4)
    outside = Car.objects.create(name="Outside caller filter", doors=2)
    user = User.objects.create_user(username="ct_actor", is_superuser=actor == "superuser", is_active=active)
    routes = ct_routes(viewset_class=ScopedViewSet)
    if actor == "object":
        for car in (granted, outside):
            assign_perm("view_vehicle", user, car)
    elif actor == "group":
        group = Group.objects.create(name="ct_readers")
        user.groups.add(group)
        for car in (granted, outside):
            assign_perm("view_vehicle", group, car)
    elif actor == "global":
        user.user_permissions.add(Permission.objects.get(content_type__model="vehicle", codename="view_vehicle"))
    user = User.objects.get(pk=user.pk)
    scope = Car.objects.using("default").filter(doors=4).order_by("pk")
    strict = [granted.pk, sibling.pk] if actor == "superuser" else [granted.pk] if actor in {"object", "group"} else []
    strict = sorted(strict) if active else []
    result = routes.viewset.get_objects_for_user(user, "view", qs=scope)
    assert result.model is Car and result.db == scope.db
    assert _pks(result) == strict
    assert not routes.viewset.get_objects_for_user(user, "view", qs=scope.none()).exists()
    assert _pks(routes.viewset.get_objects_for_user(user, "view", qs=scope.filter(pk=sibling.pk))) == (
        [sibling.pk] if active and actor == "superuser" else []
    )

    with override_settings(AUTHENTICATION_BACKENDS=[ALLOW_INACTIVE, "guardian.backends.ObjectPermissionBackend"]):
        client.force_login(user, backend=ALLOW_INACTIVE)
        for key, accepting in (("list", False), ("global_list", True)):
            response = client.get(_url(routes, key))
            assert response.wsgi_request.user.is_authenticated
            assert response.wsgi_request.user.is_active is active
            assert response.status_code == (200 if active else 403)
            if active:
                expected = sorted([granted.pk, sibling.pk]) if accepting and actor == "global" else strict
                assert _pks(response.context["object_list"]) == expected
                assert "Outside caller filter" not in response.content.decode()
        for key, view, accepting in (
            ("detail", routes.Detail, False),
            ("global_detail", routes.GlobalDetail, True),
        ):
            for car in (granted, sibling):
                allowed = active and (actor == "superuser" or (accepting and actor == "global") or car.pk in strict)
                assert view.cv_has_access(user, car) is allowed
                assert client.get(_url(routes, key, pk=car.pk)).status_code == (200 if allowed else 403)


def test_configured_content_type_manage_policy(ct_routes, client, monkeypatch):
    from crud_views.lib.settings import crud_views_settings

    routes = ct_routes()
    monkeypatch.setattr(crud_views_settings, "manage_views_enabled", "yes")
    response = client.get(_url(routes, "manage"))
    assert response.status_code == 200
    helper = {"policy": "strict", "accept_global_perms": False, "use_groups": True}
    assert response.context["guardian_config"]["get_objects_for_user"] == helper
    for key, accepting in (("list", False), ("detail", False), ("global_list", True), ("global_detail", True)):
        policy = response.context["views"][key]["guardian_policy"]
        assert policy["global_fallback_applicable"] is True
        assert policy["cv_guardian_accept_global_perms"] is accepting
    response.context["guardian_config"]["get_objects_for_user"]["accept_global_perms"] = True
    again = client.get(_url(routes, "manage"))
    assert again.context["guardian_config"]["get_objects_for_user"] == helper


@pytest.mark.parametrize("recipient", ["user", "group"])
def test_configured_content_type_standard_grant_round_trip(ct_routes, client, recipient):
    routes = ct_routes()
    car = Car.objects.create(name="Inferred base grant", doors=4)
    user = User.objects.create_user(username="ct_round_trip")
    grantee = user
    table = UserObjectPermission
    if recipient == "group":
        grantee = Group.objects.create(name="ct_round_trip_readers")
        user.groups.add(grantee)
        table = GroupObjectPermission
    assert not routes.viewset.get_objects_for_user(user, "view").exists()
    routes.viewset.assign_perm("view", grantee, car)
    grant = table.objects.get()
    assert grant.permission.codename == "view_vehicle"
    assert grant.content_type == ContentType.objects.get_for_model(Vehicle)
    assert grant.object_pk == str(car.pk)
    assert _pks(routes.viewset.get_objects_for_user(user, "view")) == [car.pk]
    client.force_login(user)
    assert client.get(_url(routes, "detail", pk=car.pk)).status_code == 200
    routes.viewset.remove_perm("view", grantee, car)
    assert not table.objects.exists()
    assert not routes.viewset.get_objects_for_user(user, "view").exists()
    assert client.get(_url(routes, "detail", pk=car.pk)).status_code == 403


@pytest.mark.parametrize(
    ("codename", "key"),
    [
        ("réviser_vehicle", "réviser"),
        ("inspect_vehicle_status", "inspect_vehicle_status"),
        ("inspect_vehicle_status_vehicle", "inspect_vehicle_status"),
        ("view_vehicle_vehicle", "view_vehicle"),
    ],
)
def test_configured_content_type_custom_permissions(ct_routes, client, codename, key):
    base_ct = ContentType.objects.get_for_model(Vehicle)
    permission = Permission.objects.create(content_type=base_ct, codename=codename, name="Base custom grant")
    child_ct = ContentType.objects.get_for_model(Car)
    Permission.objects.create(content_type=child_ct, codename="child_only_car", name="Child only")
    Permission.objects.create(content_type=child_ct, codename="réviser_car", name="Child custom grant")
    routes = ct_routes()
    expected = {"add": "app.add_vehicle", "change": "app.change_vehicle", "delete": "app.delete_vehicle"}
    expected.update({"view": "app.view_vehicle", key: f"app.{codename}"})
    assert isinstance(routes.viewset.permissions, OrderedDict)
    assert routes.viewset.permissions == expected
    assert "child_only" not in routes.viewset.permissions
    assert "app.réviser_car" not in routes.viewset.permissions.values()
    granted = Car.objects.create(name="Custom granted", doors=4)
    sibling = Car.objects.create(name="Custom ungranted", doors=4)
    user = User.objects.create_user(username="ct_custom")
    routes.List.cv_permission = routes.Detail.cv_permission = key
    assert not routes.viewset.get_objects_for_user(user, key).exists()
    routes.viewset.assign_perm(key, user, granted)
    grant = UserObjectPermission.objects.get(user=user)
    assert grant.permission_id == permission.pk and grant.content_type_id == base_ct.pk
    assert grant.object_pk == str(granted.pk)
    assert _pks(routes.viewset.get_objects_for_user(user, key)) == [granted.pk]
    client.force_login(user)
    assert _pks(client.get(_url(routes, "list")).context["object_list"]) == [granted.pk]
    assert client.get(_url(routes, "detail", pk=granted.pk)).status_code == 200
    assert client.get(_url(routes, "detail", pk=sibling.pk)).status_code == 403
    routes.viewset.remove_perm(key, user, granted)
    assert not UserObjectPermission.objects.filter(user=user).exists()
    assert not routes.viewset.get_objects_for_user(user, key).exists()
    assert client.get(_url(routes, "detail", pk=granted.pk)).status_code == 403


@pytest.mark.parametrize(("key", "codename"), [("réviser ", "réviser_vehicle"), ("view", "change_vehicle")])
def test_configured_content_type_explicit_mapping(ct_routes, client, monkeypatch, key, codename):
    import guardian.shortcuts

    permission, _ = Permission.objects.get_or_create(
        content_type=ContentType.objects.get_for_model(Vehicle), codename=codename, defaults={"name": "Exact mapping"}
    )
    value = f"app.{codename}"
    configured = OrderedDict([(key, value)])

    class ExplicitViewSet(GuardianViewSet):
        @property
        def permissions(self):
            return configured

    routes = ct_routes(viewset_class=ExplicitViewSet)
    assert GuardianViewSet.permissions is ViewSet.permissions
    assert routes.viewset.permissions is configured
    granted = Car.objects.create(name="Explicit granted", doors=4)
    Car.objects.create(name="Explicit ungranted", doors=4)
    user = User.objects.create_user(username="ct_explicit")
    spies = {}
    for helper in ("assign_perm", "remove_perm", "get_objects_for_user"):
        spies[helper] = Mock(wraps=getattr(guardian.shortcuts, helper))
        monkeypatch.setattr(guardian.shortcuts, helper, spies[helper])
    routes.viewset.assign_perm(key, user, granted)
    assert UserObjectPermission.objects.get(user=user).permission_id == permission.pk
    assert _pks(routes.viewset.get_objects_for_user(user, key)) == [granted.pk]
    routes.List.cv_permission = routes.Detail.cv_permission = key
    client.force_login(user)
    assert _pks(client.get(_url(routes, "list")).context["object_list"]) == [granted.pk]
    assert client.get(_url(routes, "detail", pk=granted.pk)).status_code == 200
    routes.viewset.remove_perm(key, user, granted)
    assert not UserObjectPermission.objects.filter(user=user).exists()
    assert not routes.viewset.get_objects_for_user(user, key).exists()
    assert spies["assign_perm"].call_args.args[0] is value
    assert spies["remove_perm"].call_args.args[0] is value
    assert all(call.args[1] is value for call in spies["get_objects_for_user"].call_args_list)
    assert routes.viewset._default_permissions is None


@pytest.mark.parametrize("path_kind", ["helper", "request"])
def test_configured_content_type_explicit_mapping_mismatch(ct_routes, client, path_kind):
    configured = OrderedDict([("view", "app.view_car")])

    class ExplicitViewSet(GuardianViewSet):
        @property
        def permissions(self):
            return configured

    routes = ct_routes(viewset_class=ExplicitViewSet)
    car = Car.objects.create(name="Mismatched explicit grant", doors=4)
    user = User.objects.create_user(username="ct_mismatch")
    assign_perm("view_vehicle", user, car)
    client.force_login(user)
    with pytest.raises(MixedContentTypeError, match="Content type for given perms and klass differs"):
        if path_kind == "helper":
            routes.viewset.get_objects_for_user(user, "view")
        else:
            client.get(_url(routes, "list"))
    assert routes.viewset.permissions is configured


@pytest.mark.parametrize("helper", ["assign_perm", "remove_perm", "get_objects_for_user"])
@pytest.mark.parametrize("active", [True, False])
@pytest.mark.parametrize("invalid", ["", "View", "view ", "v\u0456ew", "child_only", None, [], {}])
def test_configured_content_type_invalid_keys(ct_routes, monkeypatch, helper, active, invalid):
    import guardian.shortcuts

    routes = ct_routes()
    car = Car.objects.create(name="Existing permission", doors=4)
    user = User.objects.create_user(username="ct_invalid", is_active=active, is_superuser=not active)
    group = Group.objects.create(name="ct_existing")
    routes.viewset.assign_perm("view", user, car)
    routes.viewset.assign_perm("view", group, car)
    before = (list(UserObjectPermission.objects.values()), list(GroupObjectPermission.objects.values()))
    shortcut = Mock(wraps=getattr(guardian.shortcuts, helper))
    monkeypatch.setattr(guardian.shortcuts, helper, shortcut)
    scope = Mock()
    scope.none.side_effect = AssertionError("queryset accessed before key validation")
    with pytest.raises(ValueError) as error:
        if helper == "get_objects_for_user":
            routes.viewset.get_objects_for_user(user, invalid, qs=scope)
        else:
            getattr(routes.viewset, helper)(invalid, user, car)
    assert str(error.value) == (f"Invalid permission key {invalid!r}. Valid keys: 'add', 'change', 'delete', 'view'.")
    shortcut.assert_not_called()
    assert (list(UserObjectPermission.objects.values()), list(GroupObjectPermission.objects.values())) == before


@pytest.mark.parametrize("invalid", ["réviser", "Réviser ", "re\u0301viser ", "rév\u0456ser ", "réviser  "])
@pytest.mark.parametrize("helper", ["assign_perm", "remove_perm", "get_objects_for_user"])
def test_configured_content_type_explicit_keys_are_exact(ct_routes, helper, invalid):
    class ExplicitViewSet(GuardianViewSet):
        @property
        def permissions(self):
            return OrderedDict([("réviser ", "app.view_vehicle")])

    viewset = ct_routes(viewset_class=ExplicitViewSet).viewset
    car = Car.objects.create(name="Exact configured key", doors=4)
    user = User.objects.create_user(username="ct_exact", is_active=False)
    with pytest.raises(ValueError, match="Valid keys: 'réviser '"):
        if helper == "get_objects_for_user":
            viewset.get_objects_for_user(user, invalid)
        else:
            getattr(viewset, helper)(invalid, user, car)
    assert not UserObjectPermission.objects.filter(user=user).exists()


@pytest.mark.parametrize("model", [Publisher, PublisherProxy, Car])
def test_configured_content_type_default_controls(ct_routes, client, monkeypatch, model):
    monkeypatch.setattr(guardian_settings, "GET_CONTENT_TYPE", DEFAULT_CT)
    routes = ct_routes(model=model)
    granted = model.objects.create(name="Default granted")
    model.objects.create(name="Default ungranted")
    user = User.objects.create_user(username="ct_default")
    value = "app.view_car" if model is Car else "app.view_publisher"
    assert routes.viewset.permissions["view"] == value
    assign_perm(value, user, granted)
    result = routes.viewset.get_objects_for_user(user, "view")
    assert result.model is model and result.db == "default"
    assert _pks(result) == [granted.pk] and isinstance(result[0], model)
    client.force_login(user)
    assert _pks(client.get(_url(routes, "list")).context["object_list"]) == [granted.pk]
    assert client.get(_url(routes, "detail", pk=granted.pk)).status_code == 200


def test_configured_content_type_does_not_change_core_discovery(ct_routes):
    guardian = ct_routes().viewset
    core = ViewSet(model=Car, name=f"ctcore{uuid.uuid4().hex}")
    assert guardian.permissions["view"] == "app.view_vehicle"
    assert core.permissions["view"] == "app.view_car"


@pytest.mark.django_db(databases=["default", "shard"])
def test_configured_content_type_supplied_database_alias(ct_routes):
    """An active-superuser fast path retains a real nondefault queryset, not a central-auth topology claim."""
    viewset = ct_routes().viewset
    Car.objects.create(name="Default only", doors=4)
    included = Car.objects.using("shard").create(name="Shard included", doors=4)
    Car.objects.using("shard").create(name="Shard excluded", doors=2)
    user = User.objects.create_user(username="ct_alias", is_superuser=True)
    scope = Car.objects.using("shard").filter(doors=4)
    result = viewset.get_objects_for_user(user, "view", qs=scope)
    assert result.model is Car and result.db == "shard"
    assert list(result) == [included]
    assert result[0].name == "Shard included" and result[0]._state.db == "shard"
    empty = viewset.get_objects_for_user(user, "view", qs=scope.none())
    assert empty.model is Car and empty.db == "shard" and not empty.exists()


@pytest.mark.parametrize("scenario", ["empty", "nonempty", "settings_change"])
def test_configured_content_type_cache_contract(ct_routes, monkeypatch, django_assert_num_queries, scenario):
    viewset = ct_routes().viewset
    base_ct = ContentType.objects.get_for_model(Vehicle)
    if scenario == "empty":
        Permission.objects.filter(content_type=base_ct).delete()
        assert viewset.permissions == OrderedDict()
        assert viewset._default_permissions is None
        Permission.objects.create(content_type=base_ct, codename="late_vehicle", name="Late permission")
        assert viewset.permissions == OrderedDict([("late", "app.late_vehicle")])
    cached = viewset.permissions
    assert cached is viewset._default_permissions
    if scenario in {"empty", "nonempty"}:
        Permission.objects.create(content_type=base_ct, codename="later_vehicle", name="Later permission")
        with django_assert_num_queries(0):
            assert viewset.permissions is cached
        assert "later" not in cached
        assert ct_routes().viewset.permissions["later"] == "app.later_vehicle"
    else:
        assert cached["view"] == "app.view_vehicle"
        monkeypatch.setattr(guardian_settings, "GET_CONTENT_TYPE", DEFAULT_CT)
        with django_assert_num_queries(0):
            assert viewset.permissions is cached
        assert ct_routes().viewset.permissions["view"] == "app.view_car"
