"""Execute the actual published model, view and URL mapping recipe in an isolated app."""

import re
import sys
from collections import OrderedDict
from importlib.machinery import ModuleSpec
from pathlib import Path
from types import ModuleType

from django.conf import settings
from django.test import override_settings
from django.test.utils import isolate_apps
from django.urls import clear_url_caches, resolve, reverse

from crud_views.lib import check as check_module
from crud_views.lib import viewset as viewset_module
from crud_views_object_detail.lib import ObjectDetailMixin
from crud_views_object_detail.lib.resolvers import resolve_all
from crud_views_polymorphic.lib import PolymorphicDetailViewPermissionRequired

REFERENCE = Path(__file__).resolve().parents[2] / "docs/reference/polymorphic_view.md"


def _recipe_block(name):
    blocks = re.findall(
        rf"<!-- polymorphic-mapping-recipe: {name} -->\n```python\n(.*?)\n```",
        REFERENCE.read_text(encoding="utf-8"),
        re.S,
    )
    assert len(blocks) == 1, f"Expected one published {name} block, found {len(blocks)}"
    return compile(blocks[0], str(REFERENCE), "exec")


def test_documented_model_mapping_recipe(monkeypatch, tmp_path):
    package_name = "polymorphic_recipe"
    package = ModuleType(package_name)
    package.__path__ = [str(tmp_path)]
    package.__file__ = str(tmp_path / "__init__.py")
    package.__spec__ = ModuleSpec(package_name, loader=None, is_package=True)
    monkeypatch.setitem(sys.modules, package_name, package)
    modules = {}
    for name in ("models", "views", "urls"):
        module = ModuleType(f"{package_name}.{name}")
        module.__package__ = package_name
        module.__file__ = str(tmp_path / f"{name}.py")
        module.__spec__ = ModuleSpec(module.__name__, loader=None)
        monkeypatch.setitem(sys.modules, module.__name__, module)
        modules[name] = module

    # Fresh registry/cache objects prevent the recipe's generic vehicle name colliding with the test app.
    monkeypatch.setattr(viewset_module, "_REGISTRY", OrderedDict())
    monkeypatch.setattr(check_module, "_VOCAB_CACHE", {})
    try:
        with (
            override_settings(INSTALLED_APPS=[*settings.INSTALLED_APPS, package_name]),
            isolate_apps(package_name),
            override_settings(ROOT_URLCONF=modules["urls"].__name__),
        ):
            for name in ("models", "views", "urls"):
                exec(_recipe_block(name), vars(modules[name]))
            clear_url_caches()
            models, views = modules["models"], modules["views"]
            assert models.Car._meta.get_field("doors").model is models.Car
            assert models.Truck._meta.get_field("payload_tons").model is models.Truck
            detail = views.VehicleDetailView
            assert detail.__bases__ == (ObjectDetailMixin, PolymorphicDetailViewPermissionRequired)
            assert detail.cv_permission == "view"
            assert list(detail.cv_property_display) == [models.Car, models.Truck]
            assert views.cv_vehicle.get_view_class("detail") is detail
            url = reverse(views.cv_vehicle.get_router_name("detail"), kwargs={"pk": 7})
            assert url == "/vehicle/7/detail/"
            assert resolve(url).func.view_class is detail
            errors = [m for check in detail.checks() for m in check.messages()]
            assert not [m for m in errors if m.id.startswith(("viewset.E24", "viewset.W24"))]

            for obj, expected in [
                (models.Car(name="Roadster", doors=2), {"Vehicle": [("name", "Roadster")], "Car": [("doors", 2)]}),
                (
                    models.Truck(name="Hauler", payload_tons=8.5),
                    {"Vehicle": [("name", "Hauler")], "Truck": [("payload_tons", 8.5)]},
                ),
            ]:
                view = detail()
                view.object = obj
                groups = resolve_all(obj, view.get_property_display(), view=view)
                assert {group.title: [(p.path, p.value) for p in group.properties] for group in groups} == expected
    finally:
        clear_url_caches()
