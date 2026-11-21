"""Bulk semantic styling, with independent raw-byte compatibility evidence."""

import json
import re
from pathlib import Path

import pytest
from django.template.loader import render_to_string
from django.utils.functional import lazy
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.translation import override
from lxml import html

from crud_views.lib import bulk
from tests.lib.helper.icons import HOST_LIBRARY
from tests.test1.app.views_bulk import BulkPublisherCardView, BulkPublisherListView, cv_bulk_publisher

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


def _archive_control(response, key="archive"):
    assert response.status_code == 200
    controls = raw_bulk_controls(response.content.decode("utf-8"))
    (control,) = [raw for raw in controls if html.fragment_fromstring(raw).get("data-cv-bulk-action") == key]
    return control, html.fragment_fromstring(control)


@pytest.mark.parametrize("source", SOURCE_PATHS)
@pytest.mark.parametrize("variant", ("primary", "secondary", "tertiary", "danger"))
def test_destination_variant_matrix(
    client_user_bulk_publisher_change, bulk_publishers, settings, monkeypatch, source, variant
):
    destination = cv_bulk_publisher.get_view_class("archive")
    monkeypatch.setattr(destination, "cv_action_variant", variant)
    settings.CRUD_VIEWS_BUTTON_CLASSES = {
        f"bulk:{name}": f"theme-bulk-{name}" for name in ("primary", "secondary", "tertiary", "danger")
    }
    _, button = _archive_control(client_user_bulk_publisher_change.get(SOURCE_PATHS[source]))
    assert button.get("class") == f"theme-bulk-{variant}"
    assert button.text_content().strip() == "Archive"
    assert (button.get("type"), button.get("name"), button.get("value")) == ("submit", "cv_bulk_stage", "review")
    review = client_user_bulk_publisher_change.post(
        button.get("formaction"),
        {button.get("name"): button.get("value"), "cv_bulk_ids": [bulk_publishers[0].pk]},
    )
    assert review.status_code == 200
    assert not review.context["form"].is_bound
    assert list(review.context["view"].cv_bulk_objects) == [bulk_publishers[0]]
    assert any(
        heading.text_content().strip() == "Archive selected publishers"
        for heading in html.fromstring(review.content).cssselect("h1, h2, h3, h4, h5, h6")
    )
    bulk_publishers[0].refresh_from_db()
    assert bulk_publishers[0].name == "Alpha"


@pytest.mark.parametrize("source", SOURCE_PATHS)
def test_inherited_secondary(client_user_bulk_publisher_view, settings, monkeypatch, source):
    destination = cv_bulk_publisher.get_view_class("archive")
    assert "cv_action_variant" not in destination.__dict__
    assert destination.cv_action_variant == "secondary"
    source_class = {"table": BulkPublisherListView, "card": BulkPublisherCardView}[source]
    monkeypatch.setattr(source_class, "cv_action_variant", "danger")
    settings.CRUD_VIEWS_BUTTON_CLASSES = {"bulk:secondary": "inherited-secondary", "bulk:danger": "source-danger"}
    _, button = _archive_control(client_user_bulk_publisher_view.get(SOURCE_PATHS[source]))
    assert button.get("class") == "inherited-secondary"


@pytest.mark.parametrize("source", SOURCE_PATHS)
@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("icons", ICON_CASES)
@pytest.mark.parametrize("override_class", ["mode-specific", "", None])
def test_effective_mode_precedence(
    client_user_bulk_publisher_view, settings, monkeypatch, source, mode, icons, override_class
):
    settings.CRUD_VIEWS_STRICT = True
    settings.CRUD_VIEWS_LABEL_MODE_DEFAULTS = {"bulk": mode}
    settings.CRUD_VIEWS_ICON_LIBRARIES = HOST_LIBRARY
    settings.CRUD_VIEWS_ICONS = {"delete": None} if icons == "disabled" else {}
    destination = cv_bulk_publisher.get_view_class("archive")
    monkeypatch.setattr(destination, "cv_action_variant", "danger")
    monkeypatch.setattr(
        destination,
        "cv_icon_action",
        {"available": "delete", "missing": "", "disabled": "delete", "host": "ui:archive"}[icons],
    )
    effective = "label" if icons in ("missing", "disabled") else mode
    settings.CRUD_VIEWS_BUTTON_CLASSES = {
        "bulk:danger": "base-danger",
        **{f"bulk:danger:{suffix}": f"wrong-{suffix}" for suffix in MODES},
        f"bulk:danger:{effective}": override_class,
    }
    _, button = _archive_control(client_user_bulk_publisher_view.get(SOURCE_PATHS[source]))
    expected = (override_class or "").split()
    if icons == "host" and effective != "label":
        expected.append("icon-archive")
    assert button.get("class").split() == expected
    assert bool(button.cssselect("i")) == (icons == "available" and effective != "label")
    assert button.get("title") == ("Archive" if effective == "icon" else None)
    assert button.get("data-cv-tooltip") == ("form" if effective == "icon" else None)
    (label,) = button.cssselect("span")
    assert label.text == "Archive"
    assert label.get("class") == ("visually-hidden" if effective == "icon" else None)


@pytest.mark.parametrize("source", SOURCE_PATHS)
def test_form_style_isolation(client_user_bulk_publisher_view, settings, source):
    settings.CRUD_VIEWS_BUTTON_CLASSES = {"form:submit": "project-form-submit"}
    _, button = _archive_control(client_user_bulk_publisher_view.get(SOURCE_PATHS[source]))
    assert button.get("class") == "btn btn-primary"


@pytest.mark.parametrize("source", SOURCE_PATHS)
@pytest.mark.parametrize("icons", ["available", "host"])
def test_shared_form_utilities(client_user_bulk_publisher_view, settings, monkeypatch, source, icons):
    settings.CRUD_VIEWS_LABEL_MODE_DEFAULTS = {"bulk": "icon"}
    settings.CRUD_VIEWS_ICON_LIBRARIES = HOST_LIBRARY
    settings.CRUD_VIEWS_BUTTON_CLASSES = {
        "form:submit": "unused-form-submit",
        "form:hidden-label": "theme-hidden",
        "form:icon-host": "theme-host {name_class}",
    }
    monkeypatch.setattr(
        cv_bulk_publisher.get_view_class("archive"), "cv_icon_action", "ui:archive" if icons == "host" else "delete"
    )
    _, button = _archive_control(client_user_bulk_publisher_view.get(SOURCE_PATHS[source]))
    assert button.get("class") == ("btn btn-primary theme-host icon-archive" if icons == "host" else "btn btn-primary")
    assert len(button.cssselect("i")) == (0 if icons == "host" else 1)
    assert button.cssselect("span.theme-hidden")[0].text == "Archive"
    assert (button.get("title"), button.get("data-cv-tooltip")) == ("Archive", "form")


@pytest.mark.parametrize("source", SOURCE_PATHS)
def test_review_controls_unchanged(client_user_bulk_publisher_change, bulk_publishers, settings, source):
    settings.CRUD_VIEWS_BUTTON_CLASSES = {
        "bulk:secondary": "theme-bulk",
        "form:submit": "theme-confirm",
        "form:cancel": "theme-cancel",
        "form:cancel-tag": "button",
    }
    _, button = _archive_control(client_user_bulk_publisher_change.get(SOURCE_PATHS[source]))
    assert button.get("class") == "theme-bulk"
    for obj, blocked in ((bulk_publishers[0], False), (bulk_publishers[2], True)):
        review = client_user_bulk_publisher_change.post(
            button.get("formaction"), {"cv_bulk_stage": "review", "cv_bulk_ids": [obj.pk]}
        )
        assert review.status_code == 200
        (form,) = html.fromstring(review.content).cssselect("form.cv-form")
        submits = form.cssselect('button[type="submit"]')
        if blocked:
            assert not submits
        else:
            (confirm,) = submits
            assert confirm.get("class") == "theme-confirm"
            assert confirm.text_content().strip() == "Confirm"
        (cancel,) = form.cssselect("[data-cv-cancel-url]")
        assert (cancel.tag, cancel.get("type"), cancel.get("class")) == ("button", "button", "theme-cancel")
        assert cancel.text_content().strip() == "Cancel"


@pytest.mark.parametrize("source", SOURCE_PATHS)
@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("text_kind", ["plain", "safe", "lazy"])
def test_short_labels_and_escaping(client_user_bulk_publisher_view, settings, monkeypatch, source, mode, text_kind):
    text = "<img src=x onerror=\"alert(1)\"> &amp; {{ dangerous }} '✓'"
    label = {"plain": lambda: text, "safe": lambda: mark_safe(text), "lazy": lambda: lazy(lambda: text, str)()}[
        text_kind
    ]()
    destination = cv_bulk_publisher.get_view_class("archive")
    monkeypatch.setattr(destination, "cv_get_action_short_label", classmethod(lambda cls, context: label))
    monkeypatch.setattr(destination, "cv_icon_action", "delete")
    settings.CRUD_VIEWS_LABEL_MODE_DEFAULTS = {"bulk": mode}
    source_class = {"table": BulkPublisherListView, "card": BulkPublisherCardView}[source]
    original_url = source_class.cv_get_link_url
    urls = {}

    def action_url(self, cls, key, obj=None):
        url = original_url(self, cls, key, obj) + "&caption=" + text
        urls[key] = url
        return {"plain": lambda: url, "safe": lambda: mark_safe(url), "lazy": lambda: lazy(lambda: url, str)()}[
            text_kind
        ]()

    monkeypatch.setattr(source_class, "cv_get_link_url", action_url)
    raw, button = _archive_control(client_user_bulk_publisher_view.get(SOURCE_PATHS[source]))
    assert button.cssselect("span")[0].text == text
    assert button.text_content() == (" " + text if mode == "both" else text)
    assert not button.cssselect("img, script")
    assert "onerror" not in button.attrib
    assert str(escape(text)) in raw
    assert str(escape(str(escape(text)))) not in raw
    assert f'formaction="{escape(urls["archive"])}"' in raw
    assert button.get("formaction") == urls["archive"]
    assert (button.get("type"), button.get("name"), button.get("value")) == ("submit", "cv_bulk_stage", "review")
    assert button.get("data-cv-bulk-action") == "archive"
    assert button.get("title") == (text if mode == "icon" else None)
    assert button.get("data-cv-tooltip") == ("form" if mode == "icon" else None)
    assert button.cssselect("span")[0].get("class") == ("visually-hidden" if mode == "icon" else None)


@pytest.mark.parametrize("source", SOURCE_PATHS)
def test_bulk_action_key_is_escaped(client_user_bulk_publisher_view, settings, monkeypatch, source):
    key = 'archive" data-injected="yes"><script>{{ literal }}</script>&'
    destination = cv_bulk_publisher.get_view_class("archive")
    monkeypatch.setitem(cv_bulk_publisher._views, key, destination)
    source_class = {"table": BulkPublisherListView, "card": BulkPublisherCardView}[source]
    monkeypatch.setattr(source_class, "cv_bulk_actions", (key,))
    monkeypatch.setattr(source_class, "cv_get_link_url", lambda self, cls, action, obj=None: "/bulk-publisher/archive/")
    raw, button = _archive_control(client_user_bulk_publisher_view.get(SOURCE_PATHS[source]), key)
    assert f'data-cv-bulk-action="{escape(key)}"' in raw
    assert button.get("data-cv-bulk-action") == key
    assert button.get("id") == "cv-bulk-" + key
    assert "data-injected" not in button.attrib
    assert not button.cssselect("script")
