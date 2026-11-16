"""Export is opt-in; shared builders and legacy static helpers retain their contracts."""

import pytest
from django.core.checks import Error

from crud_views.lib.views import ListView
from crud_views.lib.views.manage import ManageView
from crud_views.lib.viewset import ViewSet
from tests.test1.app.models import Publisher
from tests.test1.test_manage_command import catalogue as catalogue


def make_view(catalogue, **attrs):
    vs = ViewSet(model=Publisher, name="export_core", context_buttons=[])
    view = type("ExportList", (ListView,), {"__module__": __name__, "cv_viewset": vs, **attrs})
    return vs, view


def test_export_context_exists_and_restores_nested_success_and_error():
    manage = ManageView()
    assert callable(getattr(manage, "manage_export", None)), "Manage builders need an opt-in export context"
    assert "_manage_export_enabled" not in manage.__dict__
    with manage.manage_export():
        assert manage._manage_export_enabled is True
        with pytest.raises(RuntimeError), manage.manage_export():
            raise RuntimeError("inner")
        assert manage._manage_export_enabled is True
    assert "_manage_export_enabled" not in manage.__dict__
    manage._manage_export_enabled = False
    with pytest.raises(RuntimeError), manage.manage_export():
        raise RuntimeError("outer")
    assert manage._manage_export_enabled is False


def test_stock_metadata_precedes_display_and_retains_full_values(catalogue, monkeypatch):
    vs, view = make_view(catalogue, cv_cancel_keys=("long" * 200, "detail"))
    manage = ManageView()
    assert callable(getattr(manage, "manage_export", None)), "Export metadata must be available"
    ordinary = manage.get_manage_views(vs, None)

    def forbidden(value):
        pytest.fail("Export must not call the legacy display helper")

    monkeypatch.setattr(manage, "_manage_display", forbidden)
    with manage.manage_export():
        facts = manage.get_manage_facts(vs, None)
        presentation = manage.get_manage_presentation(vs, None)
        rows = manage.get_manage_views(vs, None)
    assert all("_export" in row for row in facts)
    assert all("_export" in row for section in presentation["sections"] for row in section["entries"])
    entries = {
        entry["key"]: entry
        for row in rows
        if row["key"] == "list"
        for section in row["sections"]
        for entry in section["entries"]
    }
    assert entries["cancel_keys"]["_export"]["value"].value == list(view.cv_cancel_keys)
    assert entries["cancel_keys"]["_export"]["source"].code == "set"
    assert all(
        "_export" not in entry for row in ordinary for section in row["sections"] for entry in section["entries"]
    )


def test_static_helpers_class_instance_and_subclass_compatibility(catalogue):
    vs, view = make_view(catalogue)
    missing = object()
    args = (view, "cv_cancel_key", None, {}, set(), missing)
    expected = ManageView._manage_view_entry(*args)
    assert ManageView()._manage_view_entry(*args) == expected
    messages = [Error("broken", id="test.E001")]
    assert ManageView._manage_check_messages(messages) == ManageView()._manage_check_messages(messages)

    class Custom(ManageView):
        @staticmethod
        def _manage_display(value):
            return "custom display"

        @staticmethod
        def _manage_view_entry(view, name, value, declarations, unknown, missing):
            row = ManageView._manage_view_entry(view, name, value, declarations, unknown, missing)
            return {**row, "custom": True}

        @staticmethod
        def _manage_check_messages(messages):
            return ManageView._manage_check_messages(messages)

    custom = Custom()
    assert custom._manage_field(vs, "name", vs.name)["value"] == "custom display"
    assert custom._manage_view_entry(*args)["custom"] is True
    assert custom._manage_check_messages(messages) == ManageView._manage_check_messages(messages)
    assert callable(getattr(custom, "manage_export", None))
    with custom.manage_export():
        rows = custom._manage_view_sections(view)
    assert all(entry["custom"] for section in rows for entry in section["entries"])
    assert all("_export" not in entry for section in rows for entry in section["entries"])


def test_export_checks_add_machine_severity_only_in_context(catalogue, monkeypatch):
    vs, _view = make_view(catalogue)
    from types import SimpleNamespace

    monkeypatch.setattr(ViewSet, "checks", lambda self: [SimpleNamespace(messages=lambda: [Error("broken")])])
    manage = ManageView()
    ordinary = manage.get_manage_checks(vs, None)
    assert "level" not in ordinary["messages"][0]
    assert callable(getattr(manage, "manage_export", None))
    with manage.manage_export():
        exported = manage.get_manage_checks(vs, None)
    assert exported["messages"][0]["level"] == 40
    assert exported["messages"][0]["severity_code"] == "error"


@pytest.mark.django_db
def test_no_actor_skips_actor_builder_and_retains_holders(catalogue, monkeypatch):
    vs, _view = make_view(catalogue)
    monkeypatch.setattr(ManageView, "get_manage_actor_row", lambda *args: pytest.fail("No implicit actor"))
    result = ManageView().get_manage_permissions(vs, None)
    assert result["actor"] is None
    assert result["columns"] and result["superusers"]["count"] == 0


def test_normalization_is_bounded_and_never_formats_unknown_instances():
    from crud_views.lib.manage_report import normalize_value

    class Opaque:
        def __repr__(self):
            pytest.fail("Arbitrary instances must not be formatted")

    assert normalize_value(Opaque()).kind == "unsupported"
    assert normalize_value(None).kind == "native"
    assert normalize_value(None, not_declared=True).kind == "not_declared"
    assert normalize_value(Publisher).kind == "class_path"
    assert normalize_value({1: "bad"}).kind == "unsupported"
    assert normalize_value(float("nan")).kind == "unsupported"
    cycle = []
    cycle.append(cycle)
    assert normalize_value(cycle).kind == "unsupported"
    value = normalize_value({"tuple": (True, "x" * 400, None)})
    assert value.value == {"tuple": [True, "x" * 400, None]}
    assert value.normalizations[0].path == ["tuple"]


def test_known_wire_fields_are_strict_and_statuses_are_consistent():
    from pydantic import ValidationError

    from crud_views.lib.manage_report import ActorSelection, PermissionCell, Section, ValueRecord

    with pytest.raises(ValidationError):
        PermissionCell(key="view", model="false", object_count=None)
    with pytest.raises(ValidationError):
        ActorSelection(state="selected", row=None)
    with pytest.raises(ValidationError):
        Section[ValueRecord](status="error", data=ValueRecord(kind="native"), errors=[0])
    with pytest.raises(ValidationError):
        ValueRecord(kind="unsupported", value="invented")
