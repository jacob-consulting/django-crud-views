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
