import os
import subprocess
import sys

import pytest
from django.core.exceptions import AppRegistryNotReady

CORE_JS = [
    "crud_views/js/viewset.js",
    "crud_views/js/formset.js",
    "crud_views/js/list.filter.js",
    "crud_views/js/modal.js",
    "crud_views/js/toggle.js",
    "crud_views/js/tooltip.js",
]
CORE_CSS = ["crud_views/css/property.css", "crud_views/css/table.css", "crud_views/css/formset.css"]


def test_resolves_core_then_registry_without_externals(asset_registry):
    from crud_views.lib.pipeline import cv_sources

    asset_registry.register_assets(key="a", js=["a/one.js", "https://cdn.example.com/x.js"], css=["a/one.css"])
    assert list(cv_sources("js")) == [*CORE_JS, "a/one.js"]
    assert list(cv_sources("css")) == [*CORE_CSS, "a/one.css"]


def test_resolution_is_lazy(asset_registry):
    from crud_views.lib.pipeline import cv_sources

    sources = cv_sources("js")  # created before the bundle exists, like in settings.py
    asset_registry.register_assets(key="late", js=["late/x.js"])
    assert "late/x.js" in list(sources)
    assert len(sources) == 7
    assert sources[-1] == "late/x.js"


def test_before_after_and_dedupe(asset_registry):
    from crud_views.lib.pipeline import cv_sources

    asset_registry.register_assets(key="a", js=["a/one.js"])
    result = list(cv_sources("js", before=["js/jquery.js", "a/one.js"], after=["js/app.js", "js/jquery.js"]))
    assert result == ["js/jquery.js", "a/one.js", *CORE_JS, "js/app.js"]


def test_emit_false_bundles_included(asset_registry):
    from crud_views.lib.pipeline import cv_sources

    asset_registry.register_assets(key="hidden", js=["h/x.js"], emit=False)
    assert "h/x.js" in list(cv_sources("js"))


def test_keys_and_exclude(asset_registry):
    from crud_views.lib.pipeline import cv_sources

    asset_registry.register_assets(key="a", js=["a/one.js"])
    asset_registry.register_assets(key="b", js=["b/two.js"])
    assert list(cv_sources("js", keys=["b"])) == ["b/two.js"]
    assert list(cv_sources("js", exclude=["crud_views", "a"])) == ["b/two.js"]
    assert list(cv_sources("js", keys=["crud_views", "a"], exclude=["crud_views"])) == ["a/one.js"]


def test_keys_empty_list_selects_nothing(asset_registry):
    from crud_views.lib.pipeline import cv_sources

    assert list(cv_sources("js", keys=[], before=["js/jquery.js"])) == ["js/jquery.js"]


def test_bare_string_arguments_are_single_items(asset_registry):
    from crud_views.lib.pipeline import cv_sources

    asset_registry.register_assets(key="dtp", js=["dtp/x.js"])
    sources = cv_sources("js", keys="dtp", before="js/jquery.js", after="js/app.js")
    assert sources.keys == ("dtp",)
    assert list(sources) == ["js/jquery.js", "dtp/x.js", "js/app.js"]
    assert cv_sources("js", exclude="dtp").exclude == ("dtp",)


def test_add_and_radd_stay_lazy(asset_registry):
    from crud_views.lib.pipeline import LazySources, cv_sources

    combined = ["js/jquery.js"] + cv_sources("js", keys=["late"]) + ("js/app.js",)
    assert isinstance(combined, LazySources)
    asset_registry.register_assets(key="late", js=["late/x.js"])
    assert list(combined) == ["js/jquery.js", "late/x.js", "js/app.js"]


def test_adding_two_lazy_sources_is_unsupported():
    from crud_views.lib.pipeline import cv_sources

    first, second = cv_sources("js"), cv_sources("js")
    with pytest.raises(TypeError):
        first + second


def test_invalid_kind():
    from crud_views.lib.pipeline import cv_sources

    with pytest.raises(ValueError, match="'js' or 'css'"):
        cv_sources("svg")


def test_not_ready_raises_with_hint(monkeypatch):
    from django.apps import apps

    from crud_views.lib.pipeline import cv_sources

    sources = cv_sources("js")
    monkeypatch.setattr(apps, "ready", False)
    with pytest.raises(AppRegistryNotReady, match="before=/after="):
        list(sources)


def test_repr_does_not_resolve(monkeypatch):
    from django.apps import apps

    from crud_views.lib.pipeline import cv_sources

    sources = cv_sources("css", keys=["a"], before=["x.css"])
    monkeypatch.setattr(apps, "ready", False)
    assert repr(sources) == "<LazySources kind='css' keys=('a',) exclude=() before=1 after=0>"


def test_importable_without_django_settings():
    env = {k: v for k, v in os.environ.items() if k != "DJANGO_SETTINGS_MODULE"}
    code = (
        "from crud_views.lib.pipeline import cv_sources\n"
        "from django.conf import settings\n"
        "s = cv_sources('js', before=['js/jquery.js'])\n"
        "assert not settings.configured\n"
        "print(repr(s))\n"
    )
    result = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    assert "LazySources kind='js'" in result.stdout
