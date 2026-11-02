"""Heading icon projection through real modal markup and the shared registry."""

from pathlib import Path
from unittest.mock import Mock

import pytest
from django.template import Context, Engine
from django.test import override_settings

from crud_views.lib.settings import crud_views_settings
from crud_views.lib.view import CrudView


HOST_LIBRARY = {"host": {"renderer": "font", "placement": "host", "class": "icon-{name}"}}


def render_modal(icon="host:edit", title="Edit <title>"):
    source = Path("src/crud_views/templates/crud_views/modal/content.html").read_text()
    engine = Engine(
        loaders=[("django.template.loaders.locmem.Loader", {"modal.html": source, "body.html": "Body"})],
        libraries={"crud_views": "crud_views.templatetags.crud_views", "i18n": "django.templatetags.i18n"},
    )
    view = Mock(spec=CrudView)
    view.do_not_call_in_templates = True
    view.cv_get_header_icon.return_value = icon
    view.cv_header = title
    view.cv_content_template = "body.html"
    result = engine.get_template("modal.html").render(Context({"view": view}))
    view.cv_get_header_icon.assert_called_once_with()
    return result


def test_modal_host_icon_is_on_title(monkeypatch):
    monkeypatch.setattr(crud_views_settings, "header_level", 2)
    with override_settings(
        CRUD_VIEWS_ICON_LIBRARIES=HOST_LIBRARY,
        CRUD_VIEWS_BUTTON_CLASSES={"heading:size-5": "title-small"},
    ):
        result = render_modal()
    assert '<h2 class="title-small modal-title icon-edit"> Edit &lt;title&gt;</h2>' in result
    assert "<i " not in result


def test_modal_element_icon_preserves_default_bytes(monkeypatch):
    monkeypatch.setattr(crud_views_settings, "header_level", None)
    assert (
        '<h5 class="modal-title"><i class="fa-regular fa-eye" aria-hidden="true"></i> Edit &lt;title&gt;</h5>'
        in render_modal("detail")
    )


@pytest.mark.parametrize("disabled", [None, ""])
@pytest.mark.parametrize("level,classes", [(None, "modal-title"), (2, "h5 modal-title")])
def test_modal_disabled_host_retains_title(monkeypatch, disabled, level, classes):
    monkeypatch.setattr(crud_views_settings, "header_level", level)
    with override_settings(
        CRUD_VIEWS_ICON_LIBRARIES=HOST_LIBRARY,
        CRUD_VIEWS_BUTTON_CLASSES={"heading:icon-host": disabled},
    ):
        result = render_modal()
    assert f'class="{classes}"> Edit &lt;title&gt;</h' in result
    assert "<i " not in result
