"""Real management-command integration with process-global discovery isolation."""

import json
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
