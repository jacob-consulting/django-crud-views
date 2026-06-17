"""ContextButton template / template_code fields and the settings default."""

from crud_views.lib.settings import crud_views_settings
from crud_views.lib.view.buttons import ContextButton, FilterContextButton


def test_settings_default_template():
    assert crud_views_settings.context_button_template == "crud_views/tags/context_action.html"


def test_settings_template_override(monkeypatch):
    from django.conf import settings as dj_settings

    monkeypatch.setattr(dj_settings, "CRUD_VIEWS_CONTEXT_BUTTON_TEMPLATE", "x/y.html", raising=False)
    # property reads Django settings live
    assert crud_views_settings.context_button_template == "x/y.html"


def test_inject_template_default():
    data = {}
    ContextButton(key="edit", key_target="update")._inject_template(data)
    assert data == {"cv_template": "crud_views/tags/context_action.html"}


def test_inject_template_file():
    data = {}
    ContextButton(key="edit", key_target="update", template="app/edit.html")._inject_template(data)
    assert data == {"cv_template": "app/edit.html"}


def test_inject_template_code_wins():
    data = {}
    ContextButton(
        key="edit", key_target="update", template="app/edit.html", template_code="<a>{{ cv_url }}</a>"
    )._inject_template(data)
    assert data == {"cv_template_code": "<a>{{ cv_url }}</a>"}


def test_filter_button_default_template():
    assert FilterContextButton().template == "crud_views/tags/context_action_filter.html"
