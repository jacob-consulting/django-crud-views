"""Export is opt-in; shared builders and legacy static helpers retain their contracts."""

import pytest
from django.core.checks import Error

from crud_views.lib.views import ListView
from crud_views.lib.views.manage import ManageView
from crud_views.lib.viewset import ViewSet
from tests.test1.app.models import Publisher
from tests.test1.test_manage_command import catalogue as catalogue
from tests.test1.test_manage_report import Hostile


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


def export_entries(manage, view):
    with manage.manage_export():
        return {entry["key"]: entry for section in manage._manage_view_sections(view) for entry in section["entries"]}


@pytest.mark.parametrize(
    "family",
    ["ContextButton", "ParentContextButton", "ChildContextButton", "SiblingContextButton", "FilterContextButton"],
)
def test_owned_button_projection_preserves_every_raw_field_in_both_locations(catalogue, family):
    from crud_views.lib.view import buttons

    cls = getattr(buttons, family)
    extra = (
        {"child_name": "absent"}
        if family == "ChildContextButton"
        else {"sibling_name": "absent"}
        if family == "SiblingContextButton"
        else {}
    )
    button = cls(
        key="custom",
        label_template="label/" + "l" * 300,
        label_template_code="label" * 80,
        template="template/" + "t" * 300,
        template_code="code" * 90,
        **extra,
    )
    vs, view = make_view(catalogue, cv_context_buttons=[button])
    vs.context_buttons = [button]
    expected = dict(button.__dict__)
    manage = ManageView()
    with manage.manage_export():
        row = manage.get_manage_presentation(vs, None)["sections"][0]["entries"][0]
    record = row["_export"]["value"]
    assert record.kind == "native", "Shipped buttons need bounded owned projections"
    assert record.value == expected and record.python_type.endswith("." + family)
    nested = export_entries(manage, view)["context_buttons"]["_export"]["value"]
    assert nested.value == [expected]
    assert [(m.path, m.python_type) for m in nested.normalizations] == [([0], record.python_type)]
    assert record.value["variant"] is None and record.value["label_mode"] is None


def test_parent_projection_retains_unresolved_raw_declarations(catalogue, monkeypatch):
    from crud_views.lib.viewset import ParentViewSet

    vs, _ = make_view(catalogue)
    parent = ParentViewSet(name="absent")
    vs.parent = parent
    monkeypatch.setattr(ParentViewSet, "viewset", property(lambda self: pytest.fail("Projection resolved parent")))
    with ManageView().manage_export() as manage:
        rows = {r["key"]: r for r in manage.get_manage_facts(vs, None)}
    record = rows["parent"]["_export"]["value"]
    assert record.kind == "native", "Parent declaration must survive missing registry entries"
    assert record.value == {
        "name": "absent",
        "attribute": None,
        "pk_name": None,
        "many_to_many_through_attribute": None,
    }
    assert record.python_type.endswith(".ParentViewSet")


def test_unchecked_other_values_and_descriptors_do_not_run_hooks(catalogue):
    class Descriptor:
        def __get__(self, instance, owner):
            pytest.fail("Descriptor executed")

    class Callable:
        def __call__(self):
            pytest.fail("Callable executed")

    _vs, view = make_view(
        catalogue,
        cv_unchecked=Hostile(),
        cv_callable=Callable(),
        cv_descriptor=Descriptor(),
        cv_check_ignore_attributes=["cv_unchecked", "cv_callable", "cv_descriptor"],
    )
    entries = export_entries(ManageView(), view)
    assert entries["unchecked"]["_export"]["value"].kind == "unsupported"
    assert "callable" not in entries and "descriptor" not in entries


def test_unsupported_fallback_values_never_execute_truthiness(catalogue):
    vs, view = make_view(catalogue, cv_extends_template=Hostile())
    assert export_entries(ManageView(), view)["extends_template"]["_export"]["value"].kind == "unsupported"
    view.cv_extends_template = None
    vs.extends = Hostile()
    assert export_entries(ManageView(), view)["extends_template"]["_export"]["value"].kind == "unsupported"
    with ManageView().manage_export() as manage:
        rows = {e["key"]: e for s in manage.get_manage_presentation(vs, None)["sections"] for e in s["entries"]}
    assert rows["extends"]["_export"]["value"].kind == "unsupported"


def test_custom_button_behavior_and_field_descriptors_stay_opaque(catalogue):
    from crud_views.lib.view.buttons import ContextButton

    class CustomButton(ContextButton):
        def get_context(self, context):
            pytest.fail("custom button executed")

        @property
        def label_template(self):
            pytest.fail("label descriptor executed")

    vs, _ = make_view(catalogue)
    vs.context_buttons = [CustomButton(key="custom")]
    with ManageView().manage_export() as manage:
        row = manage.get_manage_presentation(vs, None)["sections"][0]["entries"][0]
    assert row["_export"]["value"].kind == "unsupported"


@pytest.mark.django_db
def test_missing_parent_facts_survive_other_collection_errors(catalogue):
    import json

    from crud_views.lib.viewset import ParentViewSet
    from tests.test1.test_manage_command import invoke

    vs, _ = make_view(catalogue)
    vs.parent = ParentViewSet(name="absent")
    code, output = invoke(vs.name, "--as-json")
    report = json.loads(output)
    assert code == 1
    facts = {e["key"]: e for e in report["data"]["facts"]["data"]["entries"]}
    assert facts["parent"]["value"]["value"]["name"] == "absent"
    assert report["data"]["checks"]["data"]["messages"]
    assert report["data"]["hierarchy"]["data"]["route_error"]


@pytest.mark.django_db
def test_full_long_values_reach_json_and_text(catalogue):
    import json

    from tests.test1.test_manage_command import invoke

    long_value = "xyz" * 300
    vs, _ = make_view(
        catalogue,
        cv_custom_value=long_value,
        cv_custom_list=list(range(300)),
        cv_check_ignore_attributes=["cv_custom_value", "cv_custom_list"],
    )
    json_code, output = invoke(vs.name, "--as-json")
    report = json.loads(output)
    entries = {
        e["key"]: e
        for r in report["data"]["views"]["data"]["entries"]
        if r["key"] == "list"
        for s in r["sections"]
        for e in s["entries"]
    }
    assert entries["custom_value"]["value"]["value"] == long_value
    assert entries["custom_list"]["value"]["value"] == list(range(300))
    text_code, output = invoke(vs.name)
    assert json_code == text_code == 0 and long_value in output
    assert "value.value[299]: 299" in output


@pytest.mark.django_db
def test_checked_invalid_value_formatter_failure_is_checks_error(catalogue):
    import json

    from tests.test1.test_manage_command import invoke

    calls = []

    class InvalidIcon:
        def __repr__(self):
            calls.append("repr")
            raise RuntimeError("invalid icon diagnostic formatting")

        def __str__(self):
            calls.append("str")
            raise RuntimeError("invalid icon diagnostic formatting")

    vs, _ = make_view(catalogue, cv_icon_header=InvalidIcon())
    code, text = invoke(vs.name, "--as-json")
    report = json.loads(text)
    assert code == 2 and calls
    assert report["data"]["views"]["status"] == "ok"
    assert report["data"]["checks"]["status"] == "error"
    assert any(e["section"] == "checks" and e["code"] == "collection_failed" for e in report["errors"])
    entries = {
        e["key"]: e
        for row in report["data"]["views"]["data"]["entries"]
        if row["key"] == "list"
        for section in row["sections"]
        for e in section["entries"]
    }
    assert entries["icon_header"]["value"]["kind"] == "unsupported"
    assert "object at 0x" not in text


@pytest.mark.parametrize("value", [None, False, [], (), {}])
def test_declaration_state_is_independent_of_effective_source(catalogue, value):
    vs, view = make_view(catalogue, cv_list_actions_inline=value)
    vs.list_actions_inline = ["detail"]
    row = export_entries(ManageView(), view)["list_actions_inline"]
    assert row["is_default"] is False
    assert row["_export"]["source"].code == ("viewset" if value is None else "set")
    assert row["_export"]["source"].declaring_class == f"{view.__module__}.{view.__qualname__}"
    assert row["_export"]["value"].value == (["detail"] if value is None else [] if type(value) is tuple else value)


def test_all_provenance_branches_are_locale_independent(catalogue, monkeypatch):
    from django.utils.translation import override

    from crud_views.lib.settings import crud_views_settings
    from tests.test1.test_resource_manage import ManageItem

    class ProjectMixin:
        cv_home_key = None
        cv_custom_empty = ""
        cv_annotation_only: str

    vs = ViewSet(model=Publisher, name="source_model", extends="", context_buttons=[], verbose_name=None)
    view = type(
        "InheritedList", (ProjectMixin, ListView), {"__module__": __name__, "cv_viewset": vs, "cv_extends_template": ""}
    )
    resource = ViewSet(model=ManageItem, name="source_resource", context_buttons=[])
    monkeypatch.setattr(crud_views_settings, "extends", "project/global.html")
    manage = ManageView()
    languages = []
    for language in ("en", "de"):
        with override(language), manage.manage_export():
            facts = {r["key"]: r for r in manage.get_manage_facts(vs, None)}
            resources = {r["key"]: r for r in manage.get_manage_facts(resource, None)}
            presentation = {
                r["key"]: r for s in manage.get_manage_presentation(vs, None)["sections"] for r in s["entries"]
            }
            views = export_entries(manage, view)
            fixed = export_entries(manage, vs.get_all_views()["manage"])
            rows = [*facts.values(), *resources.values(), *presentation.values(), *views.values(), *fixed.values()]
            languages.append([(r["key"], r["is_default"], r["_export"]["source"].model_dump()) for r in rows])
    assert languages[0] == languages[1]
    assert facts["verbose_name"]["is_default"] is False
    assert facts["verbose_name"]["_export"]["source"].code == "model_meta"
    assert facts["prefix"]["is_default"] is True
    assert resources["verbose_name"]["_export"]["source"].code == "resource_meta"
    assert resources["pk_type"]["_export"]["source"].code == "resource_meta"
    assert views["home_key"]["_export"]["source"].code == "inherited"
    assert views["home_key"]["_export"]["value"].kind == "native"
    assert views["home_key"]["_export"]["value"].value is None
    assert views["annotation_only"]["_export"]["value"].kind == "not_declared"
    assert views["annotation_only"]["_export"]["source"].code == "not_declared"
    assert views["context_actions"]["is_default"] is True
    assert views["context_actions"]["_export"]["source"].code == "default"
    assert fixed["inaccessible_actions"]["_export"]["source"].code == "fixed"
    for row in (presentation["extends"], views["extends_template"]):
        assert row["is_default"] is False
        assert row["_export"]["declared_value"].value == ""
        assert row["_export"]["source"].code == "global_setting"
        assert row["_export"]["source"].setting == "CRUD_VIEWS_EXTENDS"
        assert row["_export"]["value"].value == "project/global.html"


def test_export_does_not_change_subsequent_page_dictionaries(catalogue):
    vs, _ = make_view(catalogue, cv_context_actions_inline=False)
    manage = ManageView()
    builders = (manage.get_manage_facts, manage.get_manage_presentation, manage.get_manage_views)
    before = [builder(vs, None) for builder in builders]
    with manage.manage_export():
        for builder in builders:
            builder(vs, None)
    assert before == [builder(vs, None) for builder in builders]
    assert "_manage_export_enabled" not in manage.__dict__
