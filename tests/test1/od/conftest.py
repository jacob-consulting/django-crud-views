import pytest

from crud_views_object_detail.lib import conf
from crud_views_object_detail.lib.conf import CrudViewsObjectDetailSettings
from crud_views_object_detail.templatetags import crud_views_object_detail as tags


@pytest.fixture(autouse=True)
def _fresh_singleton(monkeypatch):
    """Both conf.py and the templatetags module hold their own bound reference to the
    settings singleton (the latter via `from ... import crud_views_object_detail_settings`),
    and cached_property values persist across tests. Reset both before each test so
    @override_settings actually takes effect through the templatetags module."""
    monkeypatch.setattr(conf, "crud_views_object_detail_settings", CrudViewsObjectDetailSettings())
    monkeypatch.setattr(tags, "crud_views_object_detail_settings", CrudViewsObjectDetailSettings())
