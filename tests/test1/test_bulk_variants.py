"""Bulk semantic styling, with independent raw-byte compatibility evidence."""

import json
import re
from pathlib import Path

import pytest
from django.utils.translation import override

from tests.lib.helper.icons import HOST_LIBRARY
from tests.test1.app.views_bulk import cv_bulk_publisher

pytestmark = pytest.mark.django_db

SNAPSHOT = Path(__file__).parent / "fixtures" / "bulk_toolbar_pre_variant.json"
SOURCE_PATHS = {"table": "/bulk-publisher/", "card": "/bulk-publisher/card/"}
MODES = ("label", "icon", "both")
ICON_CASES = ("available", "missing", "disabled", "host")
_BUTTON = re.compile(r"<button\b(?:[^>\"']|\"[^\"]*\"|'[^']*')*>.*?</button>\n", re.DOTALL)


def raw_bulk_controls(markup):
    """Return original button substrings, including the leaf's terminal newline."""
    return [match.group() for match in _BUTTON.finditer(markup) if 'data-cv-bulk-action="' in match.group()]


def _stock_response(client, settings, monkeypatch, source, mode, icons):
    settings.CRUD_VIEWS_BUTTON_CLASSES = {}
    settings.CRUD_VIEWS_LABEL_MODE_DEFAULTS = {"bulk": mode}
    settings.CRUD_VIEWS_STRICT = True
    settings.CRUD_VIEWS_ICON_LIBRARIES = HOST_LIBRARY
    settings.CRUD_VIEWS_ICONS = {"delete": None} if icons == "disabled" else {}
    icon = {"available": "delete", "missing": "", "disabled": "delete", "host": "ui:archive"}[icons]
    for key in ("archive", "archive_now", "rename", "bulk_delete"):
        monkeypatch.setattr(cv_bulk_publisher.get_view_class(key), "cv_icon_action", icon)
    with override("en"):
        response = client.get(SOURCE_PATHS[source])
    assert response.status_code == 200
    return response


@pytest.mark.parametrize("source", SOURCE_PATHS)
@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("icons", ICON_CASES)
def test_stock_toolbar_bytes(client_user_bulk_publisher_view, bulk_publishers, settings, monkeypatch, source, mode, icons):
    """Never refresh from bulk.html, normalize whitespace, or remove signed URL bytes.

    Future intentional URL/token/icon/label fixture changes must retain the old capture and
    provenance and add a separately identified capture from the unchanged form leaf with
    the new inputs. Record the old renderer revision, input change and capture revision.
    This phase's original snapshot stays immutable after capture.
    """
    response = _stock_response(client_user_bulk_publisher_view, settings, monkeypatch, source, mode, icons)
    buttons = response.context["view"].cv_bulk_buttons
    controls = raw_bulk_controls(response.content.decode("utf-8"))
    assert controls == buttons
    assert all(button.endswith("\n") for button in buttons)
    case = f"{source}/{mode}/{icons}"
    data = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    assert buttons == data["cases"][case]["buttons"]
    assert controls == data["cases"][case]["controls"]
