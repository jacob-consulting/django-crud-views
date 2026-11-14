"""Static configuration facts for normally constructed, registered ViewSets."""

import inspect
from uuid import uuid4

import pytest
from pydantic import model_validator

from crud_views.lib import check
from crud_views.lib.settings import crud_views_settings
from crud_views.lib.views import DetailView, ListView
from crud_views.lib.views.manage import ManageView
from crud_views.lib.viewset import _REGISTRY, _REGISTRY_LOCK, ViewSet
from crud_views_guardian.lib.viewset import GuardianViewSet
from tests.test1.app.models import Author


@pytest.fixture(autouse=True)
def restore_registry():
    with _REGISTRY_LOCK:
        registry = dict(_REGISTRY)
    vocabulary = dict(check._VOCAB_CACHE)
    yield
    with _REGISTRY_LOCK:
        _REGISTRY.clear()
        _REGISTRY.update(registry)
    check._VOCAB_CACHE.clear()
    check._VOCAB_CACHE.update(vocabulary)


def make_viewset(cls=ViewSet, **kwargs):
    return cls(model=Author, name="provenance_" + uuid4().hex, **kwargs)


def register(viewset, base=ListView, key="list", **attrs):
    return type(
        "ProjectView",
        (base,),
        {"__module__": __name__, "cv_viewset": viewset, "cv_key": key, "cv_path": key, **attrs},
    )


def rows(viewset, key="list"):
    view = next(item for item in ManageView().get_manage_views(viewset, None) if item["key"] == key)
    return {entry["key"]: entry for section in view["sections"] for entry in section["entries"]}


def test_registered_generated_actions_remain_default():
    viewset = make_viewset()
    view = register(viewset)
    assert "manage" in view.cv_context_actions
    entry = rows(viewset).get("context_actions", {})
    assert entry.get("is_default") is True, "Registration-generated actions are library defaults"
    assert entry["value"] == repr(view.cv_context_actions)


@pytest.mark.parametrize("mode", ["yes", "no"])
@pytest.mark.parametrize("declared", [False, True])
def test_registered_base_actions_and_repeated_registration(monkeypatch, mode, declared):
    monkeypatch.setattr(crud_views_settings, "manage_views_enabled", mode)
    first = make_viewset()
    base = register(first, **({"cv_context_actions": ["detail"]} if declared else {}))
    second = make_viewset()
    register(second, base=base)
    first.register_view_class("alias", base)
    assert rows(first)["context_actions"]["is_default"] is (not declared)
    assert rows(second)["context_actions"]["is_default"] is (not declared)


def test_unregistered_mixin_declarations_and_package_prefix(monkeypatch):
    class ProjectMixin:
        cv_home_key = None
        cv_context_actions = []

    library = type("ThemeView", (DetailView,), {"__module__": "crud_views_theme.views", "cv_cancel_key": "foo"})
    combined = type("Combined", (ProjectMixin, library), {"__module__": __name__})
    viewset = make_viewset()
    register(viewset, base=combined)
    data = rows(viewset)
    assert data["home_key"]["is_default"] is False
    assert data["context_actions"]["is_default"] is False
    assert data["cancel_key"]["is_default"] is True


@pytest.mark.parametrize("icon,expected,source", [(None, "'building-store'", "from ViewSet"), ("", "''", "set")])
def test_explicit_none_and_empty_have_independent_source(icon, expected, source):
    viewset = make_viewset(icon_header="building-store")
    register(viewset, cv_icon_header=icon)
    entry = rows(viewset)["icon_header"]
    assert entry["is_default"] is False
    assert entry["value"] == expected
    assert entry["source"] == source


@pytest.mark.parametrize(
    "view_value,viewset_value,source",
    [(None, "", "global setting"), ("", "project/base.html", "from ViewSet"), ("", "", "global setting")],
)
def test_empty_extends_matches_native_resolution(view_value, viewset_value, source):
    viewset = make_viewset(extends=viewset_value)
    view = register(viewset, cv_extends_template=view_value)
    entry = rows(viewset)["extends_template"]
    assert entry["value"] == repr(view().cv_get_extends_template())
    assert entry["source"] == source
    assert entry["is_default"] is False
    if view_value == "":
        assert entry["declared_value"] == "''"


@pytest.mark.parametrize("viewset_class", [ViewSet, GuardianViewSet])
@pytest.mark.parametrize("layer", ["setting", "viewset"])
def test_manage_fixed_hide_policy(viewset_class, layer, monkeypatch):
    monkeypatch.setattr(crud_views_settings, "inaccessible_actions", "disable")
    vs = make_viewset(viewset_class, **({"inaccessible_actions": "disable"} if layer == "viewset" else {}))
    view = vs.get_all_views()["manage"]
    entry = rows(vs, "manage")["inaccessible_actions"]
    assert entry["value"] == repr(view.cv_get_inaccessible_actions()) == "'hide'"
    assert entry["source"] == "ManageView.cv_get_inaccessible_actions"


def test_manage_config_does_not_execute_custom_hide_policy():
    class ProjectManage(ManageView):
        @classmethod
        def cv_get_inaccessible_actions(cls):
            pytest.fail("Static configuration must not execute project hooks")

    vs = make_viewset()
    view = register(vs, base=ProjectManage, key="custom-manage")
    assert ManageView()._manage_view_sections(view)


class BeforeGuardian(GuardianViewSet):
    @model_validator(mode="before")
    @classmethod
    def fill_icon(cls, data):
        return {"icon_header": "injected", **data}


@pytest.mark.parametrize("cls", [ViewSet, GuardianViewSet, BeforeGuardian])
@pytest.mark.parametrize("explicit", [False, True])
def test_constructor_snapshot_precedes_validators_and_stays_private(cls, explicit):
    kwargs = {"icon_header": None, "ancestor_policy": {}, "context_buttons": []}
    if explicit:
        kwargs.update(prefix=None, pk=None)
    viewset = make_viewset(cls, **kwargs)
    expected = frozenset({"model", "name", *kwargs})
    assert getattr(viewset, "_manage_constructor_fields", None) == expected
    assert isinstance(viewset._manage_constructor_fields, frozenset)
    assert viewset.prefix == viewset.name and viewset.pk is not None
    assert "_manage_constructor_fields" not in viewset.model_dump()
    assert "_manage_constructor_fields" not in inspect.signature(cls).parameters
    assert {"model", "name", "prefix"} <= inspect.signature(cls).parameters.keys()


def test_before_validator_generated_input_is_not_a_constructor_declaration():
    viewset = make_viewset(BeforeGuardian)
    assert viewset.icon_header == "injected"
    assert "icon_header" not in viewset._manage_constructor_fields


def test_complete_static_inventory_and_fixed_sections():
    class Explosive:
        def __get__(self, instance, owner=None):
            raise AssertionError("Descriptors must not run")

    class Inventory(ListView):
        cv_annotation_only: str
        cv_custom_class = Author
        cv_bad_spelling = "<script>bad</script>"
        cv_allowed = "fine"
        cv_check_ignore_attributes = {"cv_allowed"}
        cv_descriptor = Explosive()
        cv_header_template = Explosive()
        cv_custom_property = property(lambda self: 1)
        cv_custom_method = staticmethod(lambda: 1)
        cv_long = list(range(100))

    viewset = make_viewset()
    register(viewset, base=Inventory)
    prepared = next(item for item in ManageView().get_manage_views(viewset, None) if item["key"] == "list")
    assert [section["key"] for section in prepared["sections"]] == ["navigation", "templates", "icons", "other"]
    assert [entry["key"] for entry in prepared["sections"][0]["entries"]] == [
        "context_actions",
        "list_actions",
        "home_key",
        "success_key",
        "success_keys",
        "cancel_key",
        "cancel_keys",
        "list_action_method",
        "backend_only",
    ]
    data = rows(viewset)
    assert data["annotation_only"]["value"] == "not declared"
    assert data["annotation_only"]["is_default"] is True
    assert data["custom_class"]["value"] == "tests.test1.app.models.Author"
    assert data["custom_class"]["unknown"] is False  # W280 deliberately excludes classes
    assert data["bad_spelling"]["unknown"] is True
    assert data["allowed"]["unknown"] is False
    assert data["long"]["value"] == repr(Inventory.cv_long)[:200] + "…"
    assert not {"viewset", "descriptor", "header_template", "custom_property", "custom_method"} & data.keys()
    assert {"context_buttons", "modal", "pk", "object", "key", "path"} <= data.keys()
    assert {
        "header_template_code",
        "paragraph_template_code",
        "action_label_template_code",
        "action_short_label_template_code",
        "filter_header_template",
        "message_template_error_code",
    } <= {entry["key"] for entry in prepared["sections"][1]["entries"]}
    all_keys = [entry["key"] for section in prepared["sections"] for entry in section["entries"]]
    assert len(all_keys) == len(set(all_keys))
    other = prepared["sections"][-1]
    assert [entry["key"] for entry in other["entries"]] == sorted(entry["key"] for entry in other["entries"])
    for section in prepared["sections"]:
        assert section["default_count"] == sum(entry["is_default"] for entry in section["entries"])


@pytest.mark.parametrize("value", [None, [], (), {}, False])
def test_fallback_values_preserve_explicit_empty_and_false(value):
    viewset = make_viewset(list_actions_inline=["detail"])
    register(viewset, cv_list_actions_inline=value)
    entry = rows(viewset)["list_actions_inline"]
    assert entry["value"] == repr(["detail"] if value is None else value)
    assert entry["is_default"] is False
    assert entry["source"] == ("from ViewSet" if value is None else "set")


def test_settings_fallback_and_class_path_are_complete(monkeypatch):
    monkeypatch.setattr(crud_views_settings, "context_actions_inline", ["detail"])
    value = type("Long" + "Name" * 70, (), {"__module__": "project.classes"})
    viewset = make_viewset()
    register(viewset, cv_custom_class=value, cv_context_actions_inline=None)
    data = rows(viewset)
    assert data["custom_class"]["value"] == f"{value.__module__}.{value.__qualname__}"
    assert len(data["custom_class"]["value"]) > 200
    assert data["context_actions_inline"]["source"] == "global setting"
    assert data["context_actions_inline"]["value"] == "['detail']"
    assert data["context_actions_inline"]["is_default"] is False


def test_declaring_values_does_not_reorder_rows():
    viewset = make_viewset()
    view = register(viewset)
    before = rows(viewset)
    view.cv_modal = True
    view.cv_home_key = "detail"
    view.cv_icon_header = "book"
    after = rows(viewset)
    assert list(before) == list(after)
    assert "modal" in before, "Noncurated data attributes must be present in Other"
    assert before["modal"]["is_default"] is True
    assert after["modal"]["is_default"] is False


def test_annotation_discovery_is_class_local():
    class Base:
        cv_annotation: str

    class Child(Base):
        pass

    assert check._own_cv_annotations(Base) == {"cv_annotation"}
    assert check._own_cv_annotations(Child) == set()
