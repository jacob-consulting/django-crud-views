"""Command exports leave configured builders, page budgets and batching unchanged."""

import json
import sys

import pytest
from django.contrib.auth.models import Group, Permission

from crud_views.lib.settings import crud_views_settings
from crud_views.lib.views import ListView
from crud_views.lib.views.manage import ManageView
from crud_views.lib.viewset import ViewSet
from crud_views_guardian.lib.views import GuardianManageView
from crud_views_guardian.lib.viewset import GuardianViewSet
from tests.test1.app.models import Publisher
from tests.test1.test_manage_cards import developer as developer
from tests.test1.test_manage_cards import test_holder_queries_are_batched as assert_holder_batching
from tests.test1.test_manage_command import catalogue as catalogue
from tests.test1.test_manage_command import invoke
from tests.test1.test_resource_manage import ManageItem
from tests.test1.test_resource_manage import test_resource_manage_model_query_preservation as assert_page_budget

pytestmark = pytest.mark.django_db


def page_builders(manage, viewset, actor):
    """Request-free public builders, with the exact legacy container/row keys."""
    names = ["facts", "presentation", "views", "routes", "hierarchy", "ancestor_policy", "permissions", "checks"]
    if isinstance(viewset, GuardianViewSet):
        names.append("guardian")
    result = {name: getattr(manage, "get_manage_" + name)(viewset, actor) for name in names}
    field_keys = {"key", "value", "source", "is_default"}
    for row in result["facts"]:
        assert set(row) == field_keys | ({"icon"} if row["key"] == "icon_header" else set())
    presentation = result["presentation"]
    assert set(presentation) == {"sections", "default_count", "set_count"}
    for section in presentation["sections"]:
        assert set(section) == {"key", "label", "entries", "default_count"}
        for row in section["entries"]:
            assert set(row) == field_keys | ({"empty_buttons"} if row["key"] == "context_buttons" else set())
    for row in result["views"]:
        assert set(row) == {
            "key",
            "route_name",
            "route",
            "route_error",
            "requirement",
            "permission",
            "parent_requirement",
            "requirement_metadata_error",
            "guardian_policy",
            "class_path",
            "sections",
        } | ({"parent_only_requirement"} if isinstance(viewset, GuardianViewSet) else set())
        assert set(row["requirement"]) == {"kind", "value", "ancestor_applies"}
        if row["guardian_policy"] is not None:
            assert set(row["guardian_policy"]) == {"applicable", "accept_global_perms", "effective_policy", "tooltip"}
        for section in row["sections"]:
            assert set(section) == {"key", "label", "entries", "default_count"}
            for entry in section["entries"]:
                assert set(entry) == field_keys | {"unknown"}
    for row in result["routes"]:
        assert set(row) == {"key", "name", "route", "route_error"}
    assert set(result["hierarchy"]) == {"parents", "children", "route_error"}
    assert set(result["ancestor_policy"]) == {"as_ancestor", "requests"}
    assert set(result["ancestor_policy"]["as_ancestor"]) == {"provider", "effective_provider", "accept_global_perms"}
    matrix = result["permissions"]
    assert set(matrix) == {"columns", "actor", "groups", "users", "users_overflow", "show_users", "superusers"}
    assert set(matrix["superusers"]) == {"count", "names"}
    for column in matrix["columns"]:
        assert set(column) == {"key", "permission", "codename"}
    for row in [matrix["actor"], *matrix["groups"], *matrix["users"], *matrix["users_overflow"]]:
        assert set(row) == {"id", "label", "member_count", "cells"}
        for cell in row["cells"]:
            assert set(cell) == {"key", "model", "object_count"}
    assert set(result["checks"]) == {"count", "messages"}
    for message in result["checks"]["messages"]:
        assert set(message) == {"id", "severity", "message", "hint"}
    if "guardian" in result:
        assert set(result["guardian"]) == {"get_objects_for_user"}
        assert set(result["guardian"]["get_objects_for_user"]) == {"policy", "accept_global_perms", "use_groups"}
    return result


@pytest.mark.parametrize("provider", ["model", "guardian", "resource"])
@pytest.mark.parametrize("mode", ["success", "collector_error", "legacy_helper"])
@pytest.mark.parametrize("shown", [False, True])
def test_configured_command_then_same_instance_and_class_keep_page_contracts(
    catalogue, monkeypatch, django_user_model, provider, mode, shown
):
    instances = []
    base = GuardianManageView if provider == "guardian" else ManageView

    class ProjectManage(base):
        def get_manage_facts(self, viewset, user):
            if getattr(self, "_manage_export_enabled", False):
                assert not hasattr(self, "request")
                instances.append(self)
                if mode == "collector_error":
                    raise RuntimeError("export-only failure")
            return [
                *super().get_manage_facts(viewset, user),
                self._manage_field(viewset, "project_fact", "project value"),
            ]

    if mode == "legacy_helper":
        # The old six-argument public helper still dispatches; its missing export
        # metadata causes explicit views unavailability, never a page rewrite.
        def legacy(view, name, value, declarations, unknown, missing):
            return ManageView._manage_view_entry(view, name, value, declarations, unknown, missing)

        ProjectManage._manage_view_entry = staticmethod(legacy)
    monkeypatch.setattr(sys.modules[__name__], "ConfiguredPreservationManage", ProjectManage, raising=False)
    monkeypatch.setattr(crud_views_settings, "manage_show_users", shown)
    factory = GuardianViewSet if provider == "guardian" else ViewSet
    vs = factory(
        model=ManageItem if provider == "resource" else Publisher,
        name="preservation",
        context_buttons=[],
        manage_view_class=__name__ + ".ConfiguredPreservationManage",
        **({"resource_permissions": {"view": "app.view_publisher"}} if provider == "resource" else {}),
    )
    type("PreservationList", (ListView,), {"__module__": __name__, "cv_viewset": vs})
    actor = django_user_model.objects.create_user(username="preservation actor")
    permission = Permission.objects.get(content_type__app_label="app", codename="view_publisher")
    group = Group.objects.create(name="preservation group")
    group.permissions.add(permission)
    actor.groups.add(group)
    actor.user_permissions.add(permission)
    registered_class = vs.get_all_views()["manage"]
    original_instance = registered_class()
    before = page_builders(original_instance, vs, actor)
    assert len(before["permissions"]["groups"]) == 1
    assert len(before["permissions"]["users"]) == int(shown)
    assert before["facts"][-1]["value"] == "'project value'", "Pages retain their repr display contract"
    for _ in range(2):
        code, output = invoke(vs.name, "--user", actor.username, "--as-json")
        report = json.loads(output)
        assert code == (0 if mode == "success" else 2), report["errors"]
        assert report["status"] == ("complete" if mode == "success" else "partial")
        if mode != "collector_error":
            assert report["data"]["facts"]["data"]["entries"][-1]["value"]["value"] == "project value"
        assert vs.get_all_views()["manage"] is registered_class
        exported_instance = instances[-1]
        assert type(exported_instance) is registered_class
        assert "_manage_export_enabled" not in exported_instance.__dict__
        assert page_builders(exported_instance, vs, actor) == before
        assert page_builders(original_instance, vs, actor) == before
        assert page_builders(registered_class(), vs, actor) == before
    assert len(instances) == 2


@pytest.mark.parametrize("fixture", ["cv_author", "cv_guardian_author"])
@pytest.mark.parametrize("failed", [False, True])
def test_exact_cold_page_budgets_after_command(request, fixture, failed, client, django_user_model, monkeypatch):
    vs = request.getfixturevalue(fixture)
    with monkeypatch.context() as patch:
        if failed:

            def broken(*args):
                raise RuntimeError("export failure before ordinary page")

            patch.setattr(ManageView, "get_manage_facts", broken)
        code, output = invoke(vs.name, "--as-json")
        report = json.loads(output)
        assert code == (2 if failed else 1), report["errors"]
        assert report["status"] == ("partial" if failed else "complete")
    # Execute the unchanged baseline, including all exact per-table assertions,
    # cold ContentType/Guardian caches and restored __pydantic_private__ cache.
    assert_page_budget(request, fixture, client, django_user_model, monkeypatch)


@pytest.mark.parametrize("holder_count", [1, 21])
@pytest.mark.parametrize("column_count", [1, 4])
def test_holder_batching_after_command(
    cv_author, developer, monkeypatch, django_user_model, holder_count, column_count
):
    code, output = invoke(cv_author.name, "--as-json")
    report = json.loads(output)
    # The shared Author fixture intentionally has unsilenced label checks.
    assert code == 1 and report["status"] == "complete", report["errors"]
    assert_holder_batching(cv_author, developer, monkeypatch, django_user_model, holder_count, column_count)
