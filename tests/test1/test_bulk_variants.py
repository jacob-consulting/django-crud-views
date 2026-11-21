"""Bulk semantic styling, with independent raw-byte compatibility evidence."""

import json
import re
from pathlib import Path

import pytest
from django.template.loader import render_to_string
from django.utils.translation import override
from lxml import html

from crud_views.lib import bulk
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
def test_stock_toolbar_bytes(
    client_user_bulk_publisher_view, bulk_publishers, settings, monkeypatch, source, mode, icons
):
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


def test_table_variant_native_review(client_user_bulk_publisher_change, bulk_publishers, settings, monkeypatch):
    destination = cv_bulk_publisher.get_view_class("archive")
    monkeypatch.setattr(destination, "cv_action_variant", "danger")
    settings.CRUD_VIEWS_BUTTON_CLASSES = {"bulk:danger": "theme-bulk-danger"}
    response = client_user_bulk_publisher_change.get(SOURCE_PATHS["table"])
    assert response.status_code == 200
    controls = [html.fragment_fromstring(control) for control in raw_bulk_controls(response.content.decode("utf-8"))]
    (button,) = [control for control in controls if control.get("data-cv-bulk-action") == "archive"]
    assert button.get("class") == "theme-bulk-danger"
    assert button.get("type") == "submit"
    assert (button.get("name"), button.get("value")) == ("cv_bulk_stage", "review")
    selected = bulk_publishers[:2]
    review = client_user_bulk_publisher_change.post(
        button.get("formaction"),
        {button.get("name"): button.get("value"), "cv_bulk_ids": [obj.pk for obj in selected]},
    )
    assert review.status_code == 200
    assert not review.context["form"].is_bound
    assert list(review.context["view"].cv_bulk_objects) == selected
    assert "Archive selected publishers" in review.content.decode("utf-8")
    for obj, name in zip(bulk_publishers, ("Alpha", "Beta", "Locked Gamma"), strict=True):
        obj.refresh_from_db()
        assert obj.name == name


@pytest.mark.parametrize("source", SOURCE_PATHS)
@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("icons", ICON_CASES)
def test_stock_toolbar_matches_form_leaf(
    client_user_bulk_publisher_view, bulk_publishers, settings, monkeypatch, source, mode, icons
):
    """The unchanged form leaf independently renders each actual normalized payload."""
    payloads = []
    normalize = bulk.cv_button_data

    def capture(raw, location):
        data = normalize(raw, location)
        payloads.append(dict(data))
        return data

    monkeypatch.setattr(bulk, "cv_button_data", capture)
    response = _stock_response(client_user_bulk_publisher_view, settings, monkeypatch, source, mode, icons)
    controls = raw_bulk_controls(response.content.decode("utf-8"))
    assert len(payloads) == len(controls)
    with override("en"):
        for data, control in zip(payloads, controls, strict=True):
            expected = render_to_string("crud_views/tags/button/form.html", data)
            assert control == expected
            data["cv_variant"] = "secondary"
            assert render_to_string("crud_views/tags/button/bulk.html", data) == expected
