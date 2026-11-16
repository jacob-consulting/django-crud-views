"""Real management-command integration with process-global discovery isolation."""

import json
import os
import subprocess
import sys
from contextlib import contextmanager
from io import StringIO
from types import ModuleType

import pytest
from django.conf import settings
from django.core.management import call_command, get_commands
from django.test import override_settings
from django.urls import clear_url_caches, get_resolver, path, resolve

from crud_views.lib import check
from crud_views.lib.views.manage import ManageView
from crud_views.lib.viewset import _REGISTRY, _REGISTRY_LOCK, ParentViewSet, ViewSet
from crud_views_guardian.lib.viewset import GuardianViewSet
from tests.test1.app.models import Publisher
from tests.test1.test_resource_manage import ManageItem

SECTIONS = (
    "facts",
    "presentation",
    "views",
    "routes",
    "hierarchy",
    "ancestor_policy",
    "permissions",
    "checks",
    "guardian",
)


@contextmanager
def isolated_catalogue(monkeypatch, urlconf=None):
    with _REGISTRY_LOCK:
        original = dict(_REGISTRY)
    vocabulary = dict(check._VOCAB_CACHE)
    module = urlconf or ModuleType("manage_command_urls")
    if urlconf is None:
        module.urlpatterns = []
    try:
        with monkeypatch.context() as patch, override_settings(ROOT_URLCONF=module):
            with _REGISTRY_LOCK:
                _REGISTRY.clear()
            clear_url_caches()
            yield module, patch
    finally:
        with _REGISTRY_LOCK:
            _REGISTRY.clear()
            _REGISTRY.update(original)
        check._VOCAB_CACHE.clear()
        check._VOCAB_CACHE.update(vocabulary)
        clear_url_caches()


@pytest.fixture
def catalogue(monkeypatch):
    with isolated_catalogue(monkeypatch) as context:
        yield context


def invoke(*args, **kwargs):
    assert "cv_manage_view" in get_commands(), "The catalogue command must be discoverable"
    stdout, stderr = StringIO(), StringIO()
    try:
        result = call_command("cv_manage_view", *args, stdout=stdout, stderr=stderr, **kwargs)
    except SystemExit as exc:
        code = exc.code
    else:
        assert result is None
        code = 0
    assert stderr.getvalue() == ""
    return code, stdout.getvalue()


def test_catalogue_command_is_discoverable():
    assert "cv_manage_view" in get_commands(), "The catalogue command must be discoverable"


def test_catalogue_sorted_kinds_views_and_no_collectors(catalogue, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Catalogue must not run diagnostics")

    for name in ("get_manage_facts", "get_manage_permissions", "get_manage_checks"):
        monkeypatch.setattr(ManageView, name, forbidden)
    guardian = GuardianViewSet(model=Publisher, name="z_guardian")
    core = ViewSet(model=Publisher, name="a_model")
    resource = ViewSet(model=ManageItem, name="b_resource")
    nested = ViewSet(model=ManageItem, name="c_nested", parent=ParentViewSet(name=guardian.name))
    code, output = invoke("--list", "--as-json", "--force-color")
    result = json.loads(output)
    assert code == 0 and "\x1b" not in output
    assert result["version"] == 1 and result["kind"] == "catalogue" and result["status"] == "complete"
    assert result["errors"] == []
    entries = result["data"]["entries"]
    assert [row["name"] for row in entries] == [v.name for v in (core, resource, nested, guardian)]
    assert [row["kind"] for row in entries] == ["model", "resource", "resource", "guardian"]
    for row, vs in zip(entries, (core, resource, nested, guardian), strict=True):
        assert row["views"] == list(vs.get_all_views())
        assert row["backing_class"] == f"{vs.model.__module__}.{vs.model.__qualname__}"
    assert entries[2]["parent"] == guardian.name


def test_catalogue_empty_completed_urlconf(catalogue):
    code, output = invoke("--list", "--as-json")
    assert code == 0
    assert json.loads(output)["data"] == {"entries": []}


def test_catalogue_included_urlconf_registers_on_import(catalogue, tmp_path):
    module, patch = catalogue
    child = "manage_command_child"
    patch.syspath_prepend(str(tmp_path))
    patch.delitem(sys.modules, child, raising=False)
    # Record absence for monkeypatch teardown even though the import itself inserts it.
    patch.setitem(sys.modules, child, None)
    del sys.modules[child]
    (tmp_path / (child + ".py")).write_text(
        "from crud_views.lib.viewset import ViewSet\n"
        "from tests.test1.app.models import Publisher\n"
        "vs = ViewSet(model=Publisher, name='imported_child')\n"
        "urlpatterns = vs.urlpatterns\n"
    )
    from django.urls.resolvers import RoutePattern, URLResolver

    module.urlpatterns = [URLResolver(RoutePattern("child/"), child)]
    assert "imported_child" not in _REGISTRY
    code, output = invoke("--list", "--as-json")
    assert code == 0
    assert [row["name"] for row in json.loads(output)["data"]["entries"]] == ["imported_child"]
    assert "imported_child" in _REGISTRY


def test_catalogue_failed_discovery_is_not_empty(monkeypatch):
    with isolated_catalogue(monkeypatch, "missing_manage_command_urls"):
        code, output = invoke("--list", "--as-json")
    result = json.loads(output)
    assert code == 2 and result["status"] == "failed" and result["data"] is None
    assert result["errors"][0]["code"] == "collection_failed"


@pytest.mark.parametrize("raise_error", [False, True])
def test_catalogue_isolation_restores_same_worker(monkeypatch, raise_error):
    root = settings.ROOT_URLCONF
    patterns = get_resolver().url_patterns
    original, vocabulary = dict(_REGISTRY), dict(check._VOCAB_CACHE)
    try:
        with isolated_catalogue(monkeypatch) as (module, patch):
            ViewSet(model=Publisher, name="temporary_catalogue")
            check._VOCAB_CACHE.clear()
            module.urlpatterns = [path("temporary/", lambda request: None, name="temporary")]
            patch.setitem(sys.modules, "temporary_catalogue_module", module)
            assert resolve("/temporary/").url_name == "temporary"
            if raise_error:
                raise RuntimeError("fixture teardown")
    except RuntimeError:
        assert raise_error
    assert dict(_REGISTRY) == original and vocabulary == check._VOCAB_CACHE
    assert root == settings.ROOT_URLCONF and get_resolver().url_patterns == patterns
    assert "temporary_catalogue_module" not in sys.modules


@pytest.mark.django_db
def test_core_inspection_uses_configured_builders_without_actor(catalogue, monkeypatch):
    from crud_views.lib.views import ListView

    calls = []

    class ProjectManage(ManageView):
        def get_manage_facts(self, viewset, user):
            assert user is None and not hasattr(self, "request")
            calls.append(viewset.name)
            return super().get_manage_facts(viewset, user)

        def get_manage_actor_row(self, viewset, user):
            pytest.fail("No actor was selected")

    monkeypatch.setattr(sys.modules[__name__], "ConfiguredProjectManage", ProjectManage, raising=False)
    vs = ViewSet(
        model=Publisher,
        name="core_inspect",
        context_buttons=[],
        manage_view_class=__name__ + ".ConfiguredProjectManage",
    )
    type("InspectList", (ListView,), {"__module__": __name__, "cv_viewset": vs})
    assert issubclass(vs.get_all_views()["manage"], ProjectManage)
    code, output = invoke(vs.name, "--as-json")
    report = json.loads(output)
    assert report["kind"] == "inspection", "A selected ViewSet must produce an inspection"
    assert report["status"] == "complete", report["errors"]
    assert code in (0, 1) and calls == [vs.name]
    data = report["data"]
    assert data["identity"]["name"] == vs.name
    for key in ("facts", "presentation", "views", "routes", "hierarchy", "ancestor_policy", "permissions", "checks"):
        assert data[key]["status"] == "ok", key
        assert data[key]["data"]["scope"] == "viewset"
    assert data["guardian"] == {"status": "not_applicable", "data": None, "errors": []}
    assert data["permissions"]["data"]["actor"] == {"state": "not_selected", "row": None}
    assert data["facts"]["data"]["entries"]
    assert data["presentation"]["data"]["sections"]
    assert data["views"]["data"]["entries"]


def test_schema_is_complete_and_does_not_discover(catalogue, monkeypatch):
    from crud_views.management.commands import cv_manage_view

    monkeypatch.setattr(cv_manage_view, "_load_catalogue", lambda: pytest.fail("Schema must not discover"))
    code, output = invoke("--schema", "--force-color")
    assert code == 0
    schema = json.loads(output)
    assert "\x1b" not in output and "oneOf" in schema
    assert {"CatalogueResult", "InspectionResult", "PermissionsData", "ValueRecord"} <= schema["$defs"].keys()


@pytest.mark.django_db
@pytest.mark.parametrize("legacy_helper", [False, True])
def test_custom_metadata_unavailability_preserves_independent_sections(catalogue, monkeypatch, legacy_helper):
    class ProjectManage(ManageView):
        def get_manage_facts(self, viewset, user):
            rows = super().get_manage_facts(viewset, user)
            if not legacy_helper:
                rows[0]["is_default"] = "false"
            return rows

        @staticmethod
        def _manage_view_entry(view, name, value, declarations, unknown, missing):
            # Published legacy signature still works; it cannot promise complete export values.
            return ManageView._manage_view_entry(view, name, value, declarations, unknown, missing)

    monkeypatch.setattr(sys.modules[__name__], "ConfiguredProjectManage", ProjectManage, raising=False)
    vs = ViewSet(model=Publisher, name="custom_partial", manage_view_class=__name__ + ".ConfiguredProjectManage")
    code, output = invoke(vs.name, "--as-json")
    report = json.loads(output)
    assert code == 2 and report["status"] == "partial"
    assert report["data"]["views"]["status"] == "error"
    assert report["data"]["facts"]["status"] == ("ok" if legacy_helper else "error")
    assert report["data"]["permissions"]["status"] == "ok"
    for name in ("facts", "views"):
        for index in report["data"][name]["errors"]:
            assert report["errors"][index]["section"] == name
    from crud_views.lib.manage_report import Report

    assert Report.validate_python(report).status == "partial"


@pytest.mark.django_db
def test_selected_view_keeps_all_viewset_wide_evidence(catalogue):
    from crud_views.lib.views import DetailView, ListView

    vs = ViewSet(model=Publisher, name="selected_scope", context_buttons=[])
    type("SelectedList", (ListView,), {"__module__": __name__, "cv_viewset": vs})
    # An unrelated view has a real scoped error: selecting list must not hide it.
    type("UnrelatedDetail", (DetailView,), {"__module__": __name__, "cv_viewset": vs, "cv_icon_header": 12})
    full_code, output = invoke(vs.name, "--as-json")
    full = json.loads(output)
    selected_code, output = invoke(vs.name, "list", "--as-json")
    selected = json.loads(output)
    assert full_code == selected_code == 1
    for name in ("facts", "presentation", "hierarchy", "ancestor_policy", "permissions", "checks", "guardian"):
        assert selected["data"][name] == full["data"][name]
    assert selected["data"]["checks"]["data"]["messages"]
    for name in ("views", "routes"):
        data = selected["data"][name]["data"]
        assert data["scope"] == "selected_view" and data["selected_view"] == "list"
        assert [r["key"] for r in data["entries"]] == ["list"]
        assert data["entries"] == [r for r in full["data"][name]["data"]["entries"] if r["key"] == "list"]


def test_unregistered_list_selection_never_aliases_to_card(catalogue, monkeypatch):
    from crud_views.lib.views import ListView

    vs = ViewSet(model=Publisher, name="only_card", context_buttons=[])
    card = type("OnlyCard", (ListView,), {"__module__": __name__, "cv_viewset": vs, "cv_key": "card"})
    assert vs.get_view_class("list") is card
    monkeypatch.setattr(ManageView, "get_manage_permissions", lambda *args: pytest.fail("Invalid selection collected"))
    code, output = invoke(vs.name, "list", "--as-json")
    result = json.loads(output)
    assert code == 2 and result["status"] == "failed"
    assert result["errors"][0]["code"] == "unknown_view"


@pytest.mark.django_db
@pytest.mark.parametrize("configured_by", ["viewset", "setting"])
@pytest.mark.parametrize("legacy", [False, True])
def test_configured_override_metadata_and_export_restoration(catalogue, monkeypatch, configured_by, legacy):
    from crud_views.lib.settings import crud_views_settings

    instances = []

    class ProjectManage(ManageView):
        def get_manage_facts(self, viewset, user):
            instances.append(self)
            assert self._manage_export_enabled
            rows = super().get_manage_facts(viewset, user)
            if legacy:
                rows[0] = {"key": "name", "value": "legacy shortened display", "source": "set", "is_default": False}
            else:
                rows[0]["custom_additive_field"] = "allowed"
            return rows

    monkeypatch.setattr(sys.modules[__name__], "ConfiguredMetadataManage", ProjectManage, raising=False)
    path = __name__ + ".ConfiguredMetadataManage"
    if configured_by == "setting":
        monkeypatch.setattr(crud_views_settings, "manage_view_class", path)
    vs = ViewSet(
        model=Publisher,
        name="override_metadata",
        context_buttons=[],
        **({"manage_view_class": path} if configured_by == "viewset" else {}),
    )
    registered = dict(vs.get_all_views())
    registry = dict(_REGISTRY)
    code, output = invoke(vs.name, "--as-json")
    result = json.loads(output)
    assert code == (2 if legacy else 0)
    assert result["data"]["facts"]["status"] == ("error" if legacy else "ok")
    assert all(result["data"][name]["status"] == "ok" for name in ("presentation", "views", "checks", "permissions"))
    if legacy:
        assert [(e["section"], e["code"]) for e in result["errors"]] == [("facts", "output_validation_failed")]
    assert len(instances) == 1 and type(instances[0]) is registered["manage"]
    assert "_manage_export_enabled" not in instances[0].__dict__
    assert dict(vs.get_all_views()) == registered and dict(_REGISTRY) == registry


@pytest.mark.django_db
def test_custom_requirements_and_requirement_errors_remain_data(catalogue):
    from django.core.exceptions import ImproperlyConfigured

    from crud_views.lib.views import DetailView, ListView

    vs = ViewSet(model=Publisher, name="requirement_data", context_buttons=[])

    class CustomList(ListView):
        cv_viewset = vs

        @classmethod
        def cv_get_requirement(cls):
            return {"kind": "custom", "value": "project rule", "ancestor_applies": False}

    class BrokenDetail(DetailView):
        cv_viewset = vs

        @classmethod
        def cv_get_requirement(cls):
            raise ImproperlyConfigured("invalid requirement metadata")

    code, output = invoke(vs.name, "--as-json")
    report = json.loads(output)
    assert code in (0, 1) and report["data"]["views"]["status"] == "ok"
    rows = {r["key"]: r for r in report["data"]["views"]["data"]["entries"]}
    assert rows["list"]["requirement"] == {"kind": "custom", "value": "project rule", "ancestor_applies": False}
    assert rows["detail"]["requirement_metadata_error"]
    assert rows["detail"]["permission"] is None


@pytest.mark.django_db
@pytest.mark.parametrize("actor_kind", ["none", "username", "pk", "collision", "inactive"])
def test_actor_selection_is_explicit_and_username_first(catalogue, monkeypatch, django_user_model, actor_kind):
    from crud_views.management.commands import cv_manage_view

    vs = ViewSet(model=Publisher, name="actor_selection", context_buttons=[])
    actor = django_user_model.objects.create_user(username="selected actor", is_active=actor_kind != "inactive")
    selector = str(actor.pk) if actor_kind in {"pk", "collision"} else actor.username
    if actor_kind == "collision":
        actor = django_user_model.objects.create_user(username=selector)
    if actor_kind == "none":
        monkeypatch.setattr(cv_manage_view, "resolve_trace_user", lambda *a: pytest.fail("Implicit actor lookup"))
        monkeypatch.setattr(ManageView, "get_manage_actor_row", lambda *a: pytest.fail("Implicit actor evaluation"))
    code, output = invoke(vs.name, "--as-json", *([] if actor_kind == "none" else ["--user", selector]))
    report = json.loads(output)
    assert code == 0 and report["status"] == "complete", report["errors"]
    selected = report["data"]["permissions"]["data"]["actor"]
    if actor_kind == "none":
        assert selected == {"state": "not_selected", "row": None}
    else:
        assert selected["state"] == "selected"
        assert selected["row"]["id"] == actor.pk and selected["row"]["label"] == actor.username
        assert all(not cell["model"] for cell in selected["row"]["cells"])


@pytest.mark.django_db
def test_unknown_actor_fails_before_collectors(catalogue, monkeypatch):
    vs = ViewSet(model=Publisher, name="unknown_actor")
    for method in ("get_manage_facts", "get_manage_permissions", "get_manage_checks"):
        monkeypatch.setattr(ManageView, method, lambda *a: pytest.fail("Invalid actor collected diagnostics"))
    code, output = invoke(vs.name, "--user", "missing actor", "--as-json")
    report = json.loads(output)
    assert code == 2 and report["status"] == "failed" and report["data"] is None
    assert [error["code"] for error in report["errors"]] == ["unknown_user"]


@pytest.mark.django_db
@pytest.mark.parametrize("shown", [False, True])
def test_holder_visibility_overflow_and_effective_actor(catalogue, monkeypatch, django_user_model, shown):
    from django.contrib.auth.models import Group, Permission

    from crud_views.lib.settings import crud_views_settings

    monkeypatch.setattr(crud_views_settings, "manage_show_users", shown)
    vs = ViewSet(model=Publisher, name="holder_visibility", context_buttons=[])
    permission = Permission.objects.get(content_type__app_label="app", codename="view_publisher")
    group = Group.objects.create(name="direct group")
    group.permissions.add(permission)
    actor = django_user_model.objects.create_user(username="explicit group actor")
    actor.groups.add(group)
    holders = []
    for index in range(23):
        holder = django_user_model.objects.create_user(username=f"private holder {index:02}")
        holder.user_permissions.add(permission)
        holders.append(holder)
    root = django_user_model.objects.create_user(username="private root", is_superuser=True)
    django_user_model.objects.create_user(username="inactive root", is_superuser=True, is_active=False)
    code, output = invoke(vs.name, "--user", actor.username, "--as-json")
    report = json.loads(output)
    assert code == 0, report["errors"]
    data = report["data"]["permissions"]["data"]
    assert data["actor"]["row"]["label"] == actor.username
    assert next(c for c in data["actor"]["row"]["cells"] if c["key"] == "view")["model"] is True
    assert data["groups"][0]["id"] == group.pk and data["groups"][0]["member_count"] == 1
    assert data["holder_visibility"] == ("shown" if shown else "hidden")
    assert data["superusers"] == {"count": 1, "names": [root.username] if shown else None, "meaning": "global_grants"}
    if shown:
        assert [r["id"] for r in data["users"]] == [holder.pk for holder in holders]
        assert actor.pk not in [r["id"] for r in data["users"]]
    else:
        assert data["users"] is None
        assert all(holder.username not in output for holder in holders) and root.username not in output
    text_code, text = invoke(vs.name, "--user", actor.username)
    assert text_code == code and actor.username in text
    assert (holders[-1].username in text) is shown
    assert (root.username in text) is shown


@pytest.mark.django_db
def test_shown_empty_holders_are_arrays(catalogue, monkeypatch):
    from crud_views.lib.settings import crud_views_settings

    monkeypatch.setattr(crud_views_settings, "manage_show_users", True)
    vs = ViewSet(model=Publisher, name="empty_holders", context_buttons=[])
    code, output = invoke(vs.name, "--as-json")
    assert code == 0
    data = json.loads(output)["data"]["permissions"]["data"]
    assert data["users"] == data["groups"] == data["superusers"]["names"] == []


@pytest.mark.django_db
@pytest.mark.parametrize("mode", ["no", "yes", "debug_only"])
@pytest.mark.parametrize("debug", [False, True])
@pytest.mark.parametrize("actor_kind", ["none", "denied", "inactive"])
def test_manage_mode_does_not_authorize_command(
    catalogue, monkeypatch, settings, django_user_model, mode, debug, actor_kind
):
    from crud_views.lib.settings import crud_views_settings

    monkeypatch.setattr(crud_views_settings, "manage_views_enabled", mode)
    settings.DEBUG = debug
    vs = ViewSet(model=Publisher, name="mode_independent", context_buttons=[])
    actor = django_user_model.objects.create_user(username="nondeveloper", is_active=actor_kind != "inactive")
    assert not actor.groups.exists()
    for method in ("_cv_manage_allowed", "has_permission", "dispatch"):
        monkeypatch.setattr(ManageView, method, lambda *a: pytest.fail("Command must not evaluate page admission"))
    code, output = invoke(vs.name, "--as-json", *([] if actor_kind == "none" else ["--user", actor.username]))
    assert code == 0 and json.loads(output)["status"] == "complete"


@pytest.mark.django_db
@pytest.mark.parametrize("identity", ["uuid", "bad_id", "bad_label"])
def test_holder_identity_uuid_projection_and_strict_rejection(catalogue, monkeypatch, identity):
    from uuid import UUID

    from crud_views.lib.settings import crud_views_settings

    monkeypatch.setattr(crud_views_settings, "manage_show_users", True)
    vs = ViewSet(model=Publisher, name="holder_identity", context_buttons=[])
    original = ManageView.get_manage_permissions
    pk = UUID("6ca87b8f-d1a7-42bf-81d0-041de47911fa")

    class Unformattable:
        def __str__(self):
            pytest.fail("Malformed identity must not be formatted")

    def permissions(self, viewset, user):
        raw = original(self, viewset, user)
        raw["users"] = [
            {
                "id": Unformattable() if identity == "bad_id" else pk,
                "label": Unformattable() if identity == "bad_label" else "UUID holder",
                "member_count": None,
                "cells": [],
            }
        ]
        return raw

    monkeypatch.setattr(ManageView, "get_manage_permissions", permissions)
    code, output = invoke(vs.name, "--as-json")
    report = json.loads(output)
    if identity == "uuid":
        assert code == 0 and report["data"]["permissions"]["data"]["users"][0]["id"] == str(pk)
    else:
        assert code == 2 and report["data"]["permissions"]["status"] == "error"
        assert report["errors"][0]["code"] == "output_validation_failed"


@pytest.mark.django_db
@pytest.mark.parametrize("model_name", ["Publisher", "Shelf"])
@pytest.mark.parametrize("actor_kind", ["none", "group", "superuser", "inactive"])
@pytest.mark.parametrize("shown", [False, True])
def test_guardian_command_preserves_direct_and_effective_grants(
    catalogue, monkeypatch, django_user_model, model_name, actor_kind, shown
):
    from django.contrib.auth.models import Group
    from guardian.shortcuts import assign_perm

    from crud_views.lib.settings import crud_views_settings
    from crud_views_guardian.lib.views import GuardianListViewPermissionRequired
    from tests.test1.app import models
    from tests.test1.test_manage_guardian import cell, model_grant

    monkeypatch.setattr(crud_views_settings, "manage_show_users", shown)
    model = getattr(models, model_name)
    vs = GuardianViewSet(model=model, name="guardian_grants", context_buttons=[])
    type("GrantedList", (GuardianListViewPermissionRequired,), {"__module__": __name__, "cv_viewset": vs})
    first, second = [model.objects.create(name=name) for name in ("first", "second")]
    actor = django_user_model.objects.create_user(
        username="inspected", is_active=actor_kind != "inactive", is_superuser=actor_kind == "superuser"
    )
    group = Group.objects.create(name="grant group")
    holder = django_user_model.objects.create_user(username="direct holder")
    actor.groups.add(group)
    model_grant(group, vs)
    assign_perm(vs.permissions["view"], group, first)
    assign_perm(vs.permissions["view"], actor, first)  # duplicate through group must count once
    assign_perm(vs.permissions["change"], holder, second)
    args = [] if actor_kind == "none" else ["--user", actor.username]
    code, output = invoke(vs.name, "--as-json", *args)
    report = json.loads(output)
    assert code == 0 and report["status"] == "complete", report["errors"]
    data = report["data"]
    matrix = data["permissions"]["data"]
    assert matrix["superusers"]["meaning"] == "global_grants_not_strict_object_helper"
    assert matrix["superusers"]["count"] == int(actor_kind == "superuser")
    assert data["guardian"]["data"]["get_objects_for_user"] == {
        "policy": "strict",
        "accept_global_perms": False,
        "use_groups": True,
    }
    assert cell(matrix["groups"][0]) == {"key": "view", "model": True, "object_count": 1}
    assert matrix["groups"][0]["member_count"] == 1
    if shown:
        users = {row["id"]: row for row in matrix["users"]}
        assert cell(users[actor.pk]) == {"key": "view", "model": False, "object_count": 1}
        assert cell(users[holder.pk], "change") == {"key": "change", "model": False, "object_count": 1}
    else:
        assert matrix["users"] is None and matrix["superusers"]["names"] is None
        assert holder.username not in output
    if actor_kind == "none":
        assert matrix["actor"] == {"state": "not_selected", "row": None}
    else:
        assert cell(matrix["actor"]["row"]) == {
            "key": "view",
            "model": actor_kind != "inactive",
            "object_count": {"group": 1, "superuser": 2, "inactive": 0}[actor_kind],
        }
    selected_code, output = invoke(vs.name, "list", "--as-json", *args)
    selected = json.loads(output)["data"]
    assert (
        selected_code == 0
        and selected["permissions"] == data["permissions"]
        and selected["guardian"] == data["guardian"]
    )
    assert [row["key"] for row in selected["views"]["data"]["entries"]] == ["list"]


def assert_section_failures(report, failed):
    from crud_views.lib.manage_report import Report

    assert Report.validate_python(report).status == "partial"
    assert {name for name in SECTIONS if report["data"][name]["status"] == "error"} == set(failed)
    references = []
    for name in SECTIONS:
        section = report["data"][name]
        if name in failed:
            assert section["data"] is None and section["errors"]
            for index in section["errors"]:
                assert report["errors"][index]["section"] == name
                references.append(index)
        else:
            assert section["status"] in {"ok", "not_applicable"} and not section["errors"]
    assert sorted(references) == list(range(len(report["errors"])))


@pytest.mark.django_db
@pytest.mark.parametrize("section", SECTIONS)
def test_malformed_top_level_payload_only_fails_its_adapter(catalogue, monkeypatch, section):
    from crud_views.management.commands import cv_manage_view

    vs = GuardianViewSet(model=Publisher, name="bad_payload", context_buttons=[])
    original = cv_manage_view.adapt_section

    def adapt(name, raw, **kwargs):
        # Normal shared work completes before this single top-level payload is corrupted.
        return original(name, None if name == section else raw, **kwargs)

    monkeypatch.setattr(cv_manage_view, "adapt_section", adapt)
    code, output = invoke(vs.name, "--as-json")
    report = json.loads(output)
    assert code == 2
    assert_section_failures(report, [section])
    assert report["errors"][0]["code"] == "output_validation_failed"


@pytest.mark.django_db
def test_identity_survives_when_every_applicable_collector_fails(catalogue, monkeypatch):
    vs = ViewSet(model=Publisher, name="identity_survives")

    def fail(*args):
        raise RuntimeError("collector unavailable")

    for name in SECTIONS[:-1]:
        monkeypatch.setattr(ManageView, "get_manage_" + name, fail)
    code, output = invoke(vs.name, "--as-json")
    report = json.loads(output)
    assert code == 2 and report["status"] == "partial"
    assert report["data"]["identity"]["name"] == vs.name
    assert_section_failures(report, SECTIONS[:-1])


@pytest.mark.django_db
@pytest.mark.parametrize(
    "owner,failed",
    [
        ("get_manage_routes", {"presentation", "views", "routes", "hierarchy"}),
        ("_guard_manage_auth", {"views", "permissions"}),
    ],
)
def test_shared_owner_failures_follow_reached_dependencies(catalogue, monkeypatch, owner, failed):
    from crud_views.lib.view.buttons import ContextButton
    from crud_views.lib.views import ListViewPermissionRequired
    from tests.test1.app.models import Book

    parent = ViewSet(model=Publisher, name="dependency_parent", context_buttons=[])
    vs = ViewSet(
        model=Book,
        name="dependency_child",
        parent=ParentViewSet(name=parent.name, attribute="publisher"),
        context_buttons=[ContextButton(key="list", key_target="list")],
    )
    type("DependencyList", (ListViewPermissionRequired,), {"__module__": __name__, "cv_viewset": vs})
    reached = []

    def fail(self, viewset, user):
        reached.append(viewset.name)
        raise RuntimeError("shared owner unavailable")

    monkeypatch.setattr(ManageView, owner, fail)
    code, output = invoke(vs.name, "--as-json")
    assert code == 2
    assert_section_failures(json.loads(output), failed)
    assert len(reached) == len(failed)
    if owner == "get_manage_routes":
        assert parent.name in reached


@pytest.mark.django_db
def test_caught_route_unavailability_is_successful_data(catalogue, monkeypatch):
    from django.core.exceptions import ImproperlyConfigured

    vs = ViewSet(model=Publisher, name="unavailable_routes", context_buttons=[])

    def fail(self):
        raise ImproperlyConfigured("route configuration")

    monkeypatch.setattr(ViewSet, "urlpatterns", property(fail))
    code, output = invoke(vs.name, "--as-json")
    report = json.loads(output)
    assert code in (0, 1) and report["status"] == "complete"
    assert report["data"]["routes"]["status"] == "ok"
    assert all(row["route_error"] and row["route"] is None for row in report["data"]["routes"]["data"]["entries"])


@pytest.mark.django_db
@pytest.mark.parametrize(
    "level,silenced,broken,expected",
    [
        (30, False, False, 0),
        (40, True, False, 0),
        (40, False, False, 1),
        (50, False, False, 1),
        (41, False, False, 1),
        (50, False, True, 2),
    ],
)
def test_exit_precedence_uses_unsilenced_numeric_findings(catalogue, monkeypatch, level, silenced, broken, expected):
    from types import SimpleNamespace

    from django.core.checks import CheckMessage

    vs = ViewSet(model=Publisher, name="numeric_findings", context_buttons=[])
    message = CheckMessage(level, "finding", id="project.E001")
    monkeypatch.setattr(
        ViewSet,
        "checks",
        lambda self: iter([SimpleNamespace(messages=lambda: [message, message]), SimpleNamespace(messages=lambda: [])]),
    )
    if broken:

        def fail(*args):
            raise RuntimeError("facts unavailable")

        monkeypatch.setattr(ManageView, "get_manage_facts", fail)
    with override_settings(SILENCED_SYSTEM_CHECKS=[message.id] if silenced else []):
        code, output = invoke(vs.name, "--as-json")
    report = json.loads(output)
    assert code == expected
    checks = report["data"]["checks"]["data"]
    assert checks["count"] == 2 and len(checks["messages"]) == (0 if silenced else 2)
    assert report["status"] == ("partial" if broken else "complete")


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("caller_atomic", [False, True])
def test_sql_failure_respects_caller_transaction_ownership(catalogue, monkeypatch, caller_atomic):
    from contextlib import nullcontext

    from django.db import connection, transaction
    from django.db.transaction import TransactionManagementError

    assert connection.vendor == "sqlite", "This fixture records SQLite evidence only"
    assert connection.get_autocommit() and not connection.in_atomic_block
    vs = ViewSet(model=Publisher, name="sql_failure", context_buttons=[])
    reads = []
    original_checks = ManageView.get_manage_checks

    def permissions(*args):
        assert connection.in_atomic_block is caller_atomic
        # Model-save/custom-collector style error marking, without a command-owned transaction.
        with transaction.mark_for_rollback_on_error(), connection.cursor() as cursor:
            cursor.execute("SELECT missing_cv_manage_column FROM django_content_type")

    def checks(self, viewset, user):
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM django_content_type")
            reads.append(cursor.fetchone()[0])
        return original_checks(self, viewset, user)

    monkeypatch.setattr(ManageView, "get_manage_permissions", permissions)
    monkeypatch.setattr(ManageView, "get_manage_checks", checks)
    with transaction.atomic() if caller_atomic else nullcontext():
        code, output = invoke(vs.name, "--as-json")
        report = json.loads(output)
        assert code == 2
        assert_section_failures(report, ["permissions", "checks"] if caller_atomic else ["permissions"])
        assert report["errors"][0]["exception_class"] == "OperationalError"
        if caller_atomic:
            assert connection.needs_rollback
            assert report["errors"][1]["exception_class"] == "TransactionManagementError"
            with pytest.raises(TransactionManagementError), connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        else:
            assert reads and not connection.needs_rollback
    assert connection.get_autocommit() and not connection.in_atomic_block
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        assert cursor.fetchone() == (1,)


@pytest.mark.django_db
@pytest.mark.parametrize("termination", [KeyboardInterrupt, SystemExit])
def test_process_termination_propagates_without_report(catalogue, monkeypatch, termination):
    vs = ViewSet(model=Publisher, name="termination", context_buttons=[])

    def fail(*args):
        raise termination(7)

    monkeypatch.setattr(ManageView, "get_manage_facts", fail)
    output = StringIO()
    with pytest.raises(termination):
        call_command("cv_manage_view", vs.name, "--as-json", stdout=output)
    assert output.getvalue() == ""


@pytest.mark.parametrize(
    "args",
    [
        [],
        ["--list", "--schema"],
        ["--list", "x"],
        ["--schema", "x", "list"],
        ["--list", "--user", "x"],
        ["--schema", "--user", "x"],
    ],
)
def test_recognized_argument_conflicts_have_one_failed_document(catalogue, args):
    code, output = invoke(*args, "--as-json")
    result = json.loads(output)
    assert code == 2 and result["status"] == "failed" and result["data"] is None
    assert result["errors"][0]["code"] == "invalid_arguments"


@pytest.mark.parametrize(
    "viewset,view,expected", [("absent", None, "unknown_viewset"), ("known", "absent", "unknown_view")]
)
def test_unknown_selectors_fail_before_collection(catalogue, monkeypatch, viewset, view, expected):
    ViewSet(model=Publisher, name="known")
    monkeypatch.setattr(ManageView, "get_manage_facts", lambda *a: pytest.fail("Invalid selector collected"))
    code, output = invoke(viewset, *([view] if view else []), "--as-json")
    assert code == 2 and json.loads(output)["errors"][0]["code"] == expected


@pytest.mark.django_db
def test_assembly_failure_is_minimal_and_preserves_selection(catalogue, monkeypatch):
    from crud_views.management.commands import cv_manage_view

    vs = ViewSet(model=Publisher, name="assembly_failure", context_buttons=[])
    monkeypatch.setattr(cv_manage_view, "InspectionData", lambda **kw: (_ for _ in ()).throw(RuntimeError("assembly")))
    code, output = invoke(vs.name, "manage", "--as-json")
    result = json.loads(output)
    assert code == 2 and result["data"] is None and result["status"] == "failed"
    assert result["selection"] == {"viewset": vs.name, "view": "manage", "user": None}
    assert len(result["errors"]) == 1 and result["errors"][0]["code"] == "output_validation_failed"


@pytest.mark.parametrize("kind", ["invalid_identity", "assembly_exception"])
def test_catalogue_assembly_failures_are_validation_errors(catalogue, monkeypatch, kind):
    from crud_views.management.commands import cv_manage_view
    from crud_views.lib.manage_report import Report

    ViewSet(model=Publisher, name="invalid_catalogue")
    if kind == "invalid_identity":
        monkeypatch.setattr(cv_manage_view, "_identity", lambda entry: {"name": 12})
    else:

        def fail(**kwargs):
            raise RuntimeError("catalogue assembly failed")

        monkeypatch.setattr(cv_manage_view, "CatalogueData", fail)
    code, output = invoke("--list", "--as-json")
    report = Report.validate_json(output)
    assert code == 2 and report.status == "failed" and report.data is None
    assert len(report.errors) == 1 and report.errors[0].code == "output_validation_failed"


@pytest.mark.django_db
def test_unrelated_failing_global_check_cannot_preempt_report(catalogue):
    from django.core.checks import Error, register
    from django.core.checks.registry import registry

    calls = []

    def unrelated(**kwargs):
        calls.append(True)
        return [Error("Unrelated global failure", id="project.E999")]

    registered = registry.registered_checks.copy()
    try:
        register(unrelated)
        vs = ViewSet(model=Publisher, name="scoped_checks", context_buttons=[])
        code, output = invoke(vs.name, "--as-json")
        assert code == 0 and json.loads(output)["status"] == "complete"
        assert calls == []
        assert unrelated()[0].level == 40
    finally:
        registry.registered_checks = registered


@pytest.mark.django_db
def test_validation_errors_exclude_raw_inputs_and_context(catalogue, monkeypatch):
    vs = ViewSet(model=Publisher, name="private_validation", context_buttons=[])
    original = ManageView.get_manage_checks

    def malformed(self, viewset, user):
        data = original(self, viewset, user)
        data["count"] = {"private_input": "must never be serialized"}
        return data

    monkeypatch.setattr(ManageView, "get_manage_checks", malformed)
    code, output = invoke(vs.name, "--as-json")
    assert code == 2
    report = json.loads(output)
    assert_section_failures(report, ["checks"])
    assert report["errors"][0]["location"] == ["count"]
    assert report["errors"][0]["exception_class"] == "ValidationError"
    assert "private_input" not in output and "must never be serialized" not in output
    assert "Traceback" not in output and "input_value" not in output and '"ctx"' not in output


MANAGE_PROCESS = """
import os, sys
from types import ModuleType
from tests.test1.conftest import pytest_configure
pytest_configure()
from django.conf import settings
from django.core.management import call_command
from crud_views.lib.viewset import ViewSet
from crud_views.lib.views import ListView
from crud_views.lib.views.manage import ManageView
from crud_views.management.commands.cv_manage_view import Command
from tests.test1.app.models import Publisher
settings.DATABASES['default']['NAME'] = os.environ['CV_MANAGE_TEST_DATABASE']
urls = ModuleType('manage_process_urls')
urls.urlpatterns = []
settings.ROOT_URLCONF = urls
vs = ViewSet(model=Publisher, name='process', context_buttons=[])
class ProcessList(ListView):
    cv_viewset = vs
    cv_icon_header = 12 if os.environ.get('CV_MANAGE_FINDING') else None
if os.environ.get('CV_MANAGE_FAILURE'):
    def fail(*args):
        raise RuntimeError('collector failed')
    ManageView.get_manage_permissions = fail
if sys.argv[1:] == ['--prepare']:
    call_command('migrate', run_syncdb=True, verbosity=0)
else:
    Command().run_from_argv(['manage.py', 'cv_manage_view', *sys.argv[1:]])
"""


@pytest.fixture(scope="module")
def manage_process_env(tmp_path_factory):
    env = {
        **os.environ,
        "CV_MANAGE_TEST_DATABASE": str(tmp_path_factory.mktemp("manage-process") / "db.sqlite3"),
        "TERM": "xterm",
        "DJANGO_COLORS": "light",
    }
    result = subprocess.run(
        [sys.executable, "-c", MANAGE_PROCESS, "--prepare"], env=env, capture_output=True, text=True, timeout=30
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return env


def manage_process(env, *args, tty=False):
    argv = [sys.executable, "-c", MANAGE_PROCESS, *args]
    if not tty:
        return subprocess.run(argv, env=env, capture_output=True, text=True, timeout=30)
    import errno
    import pty
    from concurrent.futures import ThreadPoolExecutor

    master, slave = pty.openpty()

    def read_terminal():
        chunks = []
        while True:
            try:
                data = os.read(master, 65536)
            except OSError as exc:
                if exc.errno == errno.EIO:
                    break
                raise
            if not data:
                break
            chunks.append(data)
        return b"".join(chunks).decode().replace("\r\n", "\n")

    try:
        with subprocess.Popen(argv, env=env, stdout=slave, stderr=subprocess.PIPE, text=True) as process:
            os.close(slave)
            slave = None
            with ThreadPoolExecutor(max_workers=1) as pool:
                output = pool.submit(read_terminal)
                try:
                    _, stderr = process.communicate(timeout=30)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.communicate()
                    raise
                return subprocess.CompletedProcess(argv, process.returncode, output.result(timeout=5), stderr)
    finally:
        os.close(master)
        if slave is not None:
            os.close(slave)


@pytest.mark.parametrize("finding,failed,expected", [(False, False, 0), (True, False, 1), (True, True, 2)])
def test_real_process_exit_and_single_document(manage_process_env, finding, failed, expected):
    env = {
        **manage_process_env,
        "CV_MANAGE_FINDING": "1" if finding else "",
        "CV_MANAGE_FAILURE": "1" if failed else "",
    }
    result = manage_process(env, "process", "--as-json")
    assert result.returncode == expected and result.stderr == ""
    report = json.loads(result.stdout)  # Rejects a second stdout document.
    assert report["status"] == ("partial" if failed else "complete")


@pytest.mark.parametrize(
    "args,code,structured",
    [
        (["--help"], 0, False),
        (["--unknown-option"], 2, False),
        (["a", "b", "c"], 2, False),
        (["--list", "--no-color", "--force-color"], 1, False),
        (["--as-json"], 2, True),
        (["--list", "--schema", "--as-json"], 2, True),
    ],
)
def test_real_framework_and_command_usage_boundaries(manage_process_env, args, code, structured):
    result = manage_process(manage_process_env, *args)
    assert result.returncode == code
    if structured:
        assert result.stderr == "" and json.loads(result.stdout)["errors"][0]["code"] == "invalid_arguments"
    elif code:
        assert result.stdout == "" and result.stderr and "Traceback" not in result.stderr
    else:
        assert "Inspect registered ViewSet" in result.stdout and "--schema" in result.stdout
        assert result.stderr == ""


def test_django_startup_failure_remains_outside_structured_output(manage_process_env):
    result = subprocess.run(
        [sys.executable, "-m", "django", "cv_manage_view", "--as-json"],
        env={**manage_process_env, "DJANGO_SETTINGS_MODULE": "missing_cv_startup_settings"},
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode != 0 and result.stdout == ""
    assert "missing_cv_startup_settings" in result.stderr


@pytest.mark.parametrize("mode", ["text", "json", "schema"])
@pytest.mark.parametrize(
    "tty,flag,colored",
    [
        (False, None, False),
        (False, "--force-color", True),
        (True, None, True),
        (True, "--no-color", False),
    ],
)
def test_real_pipe_and_pty_follow_django_color_options(manage_process_env, mode, tty, flag, colored):
    import re

    args = ["--schema"] if mode == "schema" else ["process", *(["--as-json"] if mode == "json" else [])]
    result = manage_process(manage_process_env, *args, *([flag] if flag else []), tty=tty)
    assert result.returncode == 0 and result.stderr == ""
    ansi = re.compile(r"\x1b\[[0-9;]*m")
    assert bool(ansi.search(result.stdout)) is (colored and mode == "text")
    baseline = manage_process(manage_process_env, *args, "--no-color")
    assert ansi.sub("", result.stdout) == baseline.stdout
    if mode != "text":
        json.loads(result.stdout)


def report_leaves(value, prefix=""):
    """All leaf paths, including empty/null values, form the parity oracle."""
    if isinstance(value, dict) and value:
        for key, child in value.items():
            yield from report_leaves(child, f"{prefix}.{key}" if prefix else key)
    elif isinstance(value, list) and value:
        for index, child in enumerate(value):
            yield from report_leaves(child, f"{prefix}[{index}]")
    else:
        yield prefix, value


@pytest.mark.django_db
@pytest.mark.parametrize("provider", ["model", "guardian", "resource"])
@pytest.mark.parametrize("partial", [False, True])
def test_rich_text_retains_every_validated_fact_and_page_values(
    catalogue, monkeypatch, django_user_model, provider, partial
):
    from django.core.management.color import no_style

    from crud_views.lib.manage_report import Report
    from crud_views.lib.views import ListView
    from crud_views.management.commands import cv_manage_view
    from tests.test1.app.models import Book

    parent = ViewSet(model=Publisher, name="text_parent", context_buttons=[])
    factory = GuardianViewSet if provider == "guardian" else ViewSet
    model = ManageItem if provider == "resource" else Book
    vs = factory(
        model=model,
        name="rich_text",
        context_buttons=[],
        parent=ParentViewSet(name=parent.name, **({} if provider == "resource" else {"attribute": "publisher"})),
    )
    type("RichTextList", (ListView,), {"__module__": __name__, "cv_viewset": vs, "cv_extends": ""})
    actor = django_user_model.objects.create_user(username="actor café 雪")
    long_value = "full-value-" * 80
    dynamic = "key\n\t\x1b[31m\x07\r\u202e"
    raw_value = {dynamic: [None, False, 'quoted \\" café 雪', long_value, list(range(240))]}
    original = ManageView.get_manage_facts

    def facts(self, viewset, user):
        return [*original(self, viewset, user), self._manage_field(viewset, dynamic, raw_value)]

    monkeypatch.setattr(ManageView, "get_manage_facts", facts)
    if partial:

        def fail(*args):
            raise RuntimeError("error " + dynamic)

        monkeypatch.setattr(ManageView, "get_manage_checks", fail)
    code, output = invoke(vs.name, "list", "--user", actor.username, "--as-json", "--force-color")
    data = json.loads(output)
    assert code == (2 if partial else 0), data["errors"]
    assert "\x1b" not in output and "café" not in output  # ASCII JSON retains Unicode through escapes.
    report = Report.validate_python(data)
    manage = vs.get_all_views()["manage"]()
    page_facts = manage.get_manage_facts(vs, actor)
    exported_facts = data["data"]["facts"]["data"]["entries"]
    assert [row["key"] for row in page_facts] == [row["key"] for row in exported_facts]
    assert [row["is_default"] for row in page_facts] == [row["is_default"] for row in exported_facts]
    assert len(page_facts[-1]["value"]) == 201 and long_value not in page_facts[-1]["value"]
    assert exported_facts[-1]["value"]["value"] == raw_value
    assert data["data"]["routes"]["data"]["entries"] == [
        row for row in manage.get_manage_routes(vs, actor) if row["key"] == "list"
    ]
    assert data["data"]["hierarchy"]["data"] == {"scope": "viewset", **manage.get_manage_hierarchy(vs, actor)}
    page_permissions = manage.get_manage_permissions(vs, actor)
    matrix = data["data"]["permissions"]["data"]
    assert matrix["columns"] == page_permissions["columns"]
    assert matrix["actor"]["row"] == page_permissions["actor"]
    assert matrix["groups"] == page_permissions["groups"]
    assert matrix["superusers"]["count"] == page_permissions["superusers"]["count"]
    # Rendering consumes this validated result alone; no additional queries/collection.
    for name in SECTIONS[:-1]:
        monkeypatch.setattr(ManageView, "get_manage_" + name, lambda *a: pytest.fail("Renderer recollected facts"))
    text = cv_manage_view._format_text(report, no_style())
    for key, value in report_leaves(data):
        assert f"{cv_manage_view._text(key)}: {cv_manage_view._text(value)}" in text
    assert long_value in text and "actor café 雪" in text
    assert all(char.isprintable() or char == "\n" for char in text)
    for escaped in (r"\n", r"\t", r"\u001b", r"\u0007", r"\r", r"\u202e"):
        assert escaped in text
    assert "Facts (ViewSet-wide)" in text and "Permissions (ViewSet-wide)" in text
    assert "Views (selected view: list)" in text and "Routes (selected view: list)" in text
    assert "direct grants" in text and "effective grants" in text and "hidden" in text
    if provider == "resource":
        assert "Resource grants are global" in text and "no per-item grants" in text
    if provider == "guardian":
        assert "Guardian object counts" in text and "strict object helper" in text


@pytest.mark.django_db
def test_english_german_machine_projection_and_exit_are_stable(catalogue, monkeypatch):
    from types import SimpleNamespace

    from django.core.checks import Error
    from django.utils.translation import override

    from crud_views_guardian.lib.views import GuardianListViewPermissionRequired

    vs = GuardianViewSet(model=Publisher, name="locale_stable", context_buttons=[])
    type("LocaleList", (GuardianListViewPermissionRequired,), {"__module__": __name__, "cv_viewset": vs})
    monkeypatch.setattr(
        ViewSet, "checks", lambda self: iter([SimpleNamespace(messages=lambda: [Error("finding", id="project.E001")])])
    )
    results, texts = [], []
    machine_keys = {
        "code",
        "status",
        "scope",
        "kind",
        "key",
        "name",
        "version",
        "level",
        "severity_code",
        "state",
        "holder_visibility",
        "meaning",
        "effective_policy",
        "policy",
        "selected_view",
        "declaring_class",
        "setting",
        "is_default",
        "python_type",
        "class_path",
        "grant_kind",
    }

    def machine(value):
        if isinstance(value, dict):
            return {key: child if key in machine_keys else machine(child) for key, child in value.items()}
        if isinstance(value, list):
            return [machine(child) for child in value]
        return None

    for language in ("en", "de", "en"):
        with override(language):
            code, output = invoke(vs.name, "list", "--as-json")
            text_code, text = invoke(vs.name, "list", "--no-color")
        assert code == text_code == 1
        report = json.loads(output)
        assert set(report) == {"version", "kind", "status", "selection", "data", "errors"}
        results.append(machine(report))
        texts.append(text)
    assert results[0] == results[1] == results[2]
    assert texts[0] == texts[2] and texts[0] != texts[1]
