"""Object-detail tabs participate in the public asset registry lifecycle."""

import pytest
from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
from django.template import Context, Template
from django.test import override_settings

from crud_views.lib.assets import get_registered

KEY = "crud_views_object_detail"
SCRIPT = "crud_views_object_detail/js/tabs.js"


def render_scripts():
    return Template("{% load crud_views %}{% cv_js %}").render(Context({}))


def test_presentation_assets_installed_extension_emits_once():
    html = render_scripts()
    assert html.count(f'src="/static/{SCRIPT}"') == 1
    assert html.index("crud_views/js/viewset.js") < html.index(SCRIPT)


def test_presentation_assets_repeat_ready_and_reset(asset_registry):
    config = apps.get_app_config("cvod")
    config.ready()
    config.ready()
    assert render_scripts().count(SCRIPT) == 1
    asset_registry._REGISTRY.clear()
    config.ready()
    assert render_scripts().count(SCRIPT) == 1


def test_presentation_assets_app_registry_repopulation(asset_registry, settings):
    with override_settings(INSTALLED_APPS=list(settings.INSTALLED_APPS)):
        assert render_scripts().count(SCRIPT) == 1
    with override_settings(INSTALLED_APPS=list(settings.INSTALLED_APPS)):
        assert render_scripts().count(SCRIPT) == 1


@pytest.mark.parametrize(
    "bundle",
    [
        {"js": ["other.js"]},
        {"js": [SCRIPT], "css": ["extra.css"]},
        {"js": [SCRIPT], "emit": False},
    ],
)
def test_presentation_assets_conflicting_bundle_is_not_swallowed(asset_registry, bundle):
    asset_registry.register_assets(KEY, **bundle)
    with pytest.raises(ImproperlyConfigured, match="already registered"):
        apps.get_app_config("cvod").ready()
    assert len(get_registered()) == 1


def test_presentation_assets_public_duplicate_validation_unchanged(asset_registry):
    apps.get_app_config("cvod").ready()
    with pytest.raises(ImproperlyConfigured, match="already registered"):
        asset_registry.register_assets(KEY, js=[SCRIPT])
