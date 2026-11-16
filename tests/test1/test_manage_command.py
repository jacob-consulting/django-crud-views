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

    vs = ViewSet(model=Publisher, name="core_inspect", context_buttons=[])
    type("InspectList", (ListView,), {"__module__": __name__, "cv_viewset": vs})
    # Use the actual registered class selector, without dispatching or registering a second view.
    monkeypatch.setitem(vs._views, "manage", ProjectManage)
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
