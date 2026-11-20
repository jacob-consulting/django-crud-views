"""Rendered table and card selection, without permission work on source pages."""

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from crud_views.lib.button_classes import get_button_class
from tests.test1.app.models import Publisher
from tests.test1.app.views_bulk import BulkPublisherListView, cv_bulk_publisher
from tests.test1.test_bulk_flow import max_form_depth, soup

pytestmark = pytest.mark.django_db


def test_table_toolbar_controls(client_user_bulk_publisher_view, bulk_publishers):
    response = client_user_bulk_publisher_view.get("/bulk-publisher/")
    assert response.status_code == 200
    page = soup(response)
    form = page.cssselect("form[data-cv-bulk]")[0]
    assert form.get("id") == "cv-bulk-selection"
    assert form.get("method") == "post"
    assert form.get("class") == get_button_class("bulk", "toolbar")
    assert form.cssselect('input[name="csrfmiddlewaretoken"]')
    first = form.cssselect('button[type="submit"]')[0]
    assert set(first.attrib) == {"type", "disabled", "hidden"}
    enhanced = form.cssselect("[data-cv-bulk-enhanced]")
    assert len(enhanced) == 1
    assert "hidden" in enhanced[0].attrib
    assert not any(cls.startswith("d-") for cls in enhanced[0].get("class", "").split())
    select_all = enhanced[0].cssselect("[data-cv-bulk-all]")
    assert len(select_all) == 1
    assert select_all[0].get("type") == "checkbox"
    assert select_all[0].get("name") is None
    assert select_all[0].get("class") == get_button_class("bulk", "checkbox")
    assert "Select this page" in enhanced[0].text_content()
    count = enhanced[0].cssselect("[data-cv-bulk-count]")[0]
    assert count.text_content() == "0"
    assert count.getparent().get("aria-live") == "polite"
    assert count.getparent().text_content().strip() == "0 selected"
    buttons = form.cssselect("[data-cv-bulk-action]")
    assert [button.get("data-cv-bulk-action") for button in buttons] == list(BulkPublisherListView.cv_bulk_actions)
    for button in buttons:
        assert button.get("type") == "submit"
        assert button.get("name") == "cv_bulk_stage"
        assert button.get("value") == "review"
        assert button.get("formaction")
        assert "disabled" not in button.attrib
        key = button.get("data-cv-bulk-action")
        destination = cv_bulk_publisher.get_view_class(key)
        assert button.text_content().strip() == destination.cv_get_action_short_label({})
    assert not form.cssselect("select")
    assert "Continue" not in form.text_content()
    attributes = {name for element in page.iter() for name in element.attrib if name.startswith("data-cv-bulk")}
    assert attributes == {
        "data-cv-bulk",
        "data-cv-bulk-item",
        "data-cv-bulk-all",
        "data-cv-bulk-count",
        "data-cv-bulk-action",
        "data-cv-bulk-enhanced",
    }


@pytest.mark.parametrize("mode", ["both", "icon", "label"])
def test_bulk_label_floor(client_user_bulk_publisher_view, settings, mode):
    settings.CRUD_VIEWS_LABEL_MODE_DEFAULTS = {"bulk": mode}
    settings.CRUD_VIEWS_STRICT = True
    page = soup(client_user_bulk_publisher_view.get("/bulk-publisher/"))
    delete = page.cssselect('[data-cv-bulk-action="bulk_delete"]')[0]
    archive = page.cssselect('[data-cv-bulk-action="archive"]')[0]
    assert bool(delete.cssselect("i, svg")) == (mode != "label")
    assert delete.get("class") == get_button_class("form", "submit", mode)
    assert delete.text_content().strip() == "Delete"
    if mode == "icon":
        assert delete.cssselect("span")[0].get("class") == get_button_class("form", "hidden-label")
        assert delete.get("title") == "Delete"
    else:
        assert delete.cssselect("span")[0].get("class") is None
    assert not archive.cssselect("i, svg")
    assert archive.text_content().strip() == "Archive"
    assert archive.cssselect("span")[0].get("class") is None
    assert archive.get("class") == get_button_class("form", "submit", "label")


def test_bulk_floor_is_independent_of_form(client_user_bulk_publisher_view, settings):
    settings.CRUD_VIEWS_LABEL_MODE_DEFAULTS = {"form": "icon"}
    settings.CRUD_VIEWS_STRICT = True
    page = soup(client_user_bulk_publisher_view.get("/bulk-publisher/"))
    delete = page.cssselect('[data-cv-bulk-action="bulk_delete"]')[0]
    assert delete.cssselect("i, svg")
    assert delete.cssselect("span")[0].get("class") is None
    assert delete.get("class") == get_button_class("form", "submit", "both")


@pytest.mark.parametrize("mode", ["icon", "both"])
def test_disabled_action_icon_uses_visible_label(client_user_bulk_publisher_view, settings, mode):
    settings.CRUD_VIEWS_ICONS = {"delete": None}
    settings.CRUD_VIEWS_LABEL_MODE_DEFAULTS = {"bulk": mode}
    settings.CRUD_VIEWS_STRICT = True
    response = client_user_bulk_publisher_view.get("/bulk-publisher/")
    assert response.status_code == 200
    button = soup(response).cssselect('[data-cv-bulk-action="bulk_delete"]')[0]
    assert not button.cssselect("i, svg")
    assert button.text_content().strip() == "Delete"
    assert button.cssselect("span")[0].get("class") is None
    assert button.get("class") == get_button_class("form", "submit", "label")


def test_table_checkboxes_and_structure(client_user_bulk_publisher_view, bulk_publishers):
    response = client_user_bulk_publisher_view.get("/bulk-publisher/")
    page = soup(response)
    boxes = page.cssselect("[data-cv-bulk-item]")
    assert len(boxes) == len(bulk_publishers)
    for box, record in zip(boxes, bulk_publishers, strict=True):
        assert box.get("class") == get_button_class("bulk", "checkbox")
        assert box.get("name") == "cv_bulk_ids"
        assert box.get("value") == str(record.pk)
        assert box.get("form") == "cv-bulk-selection"
        assert box.get("aria-label") == f"Select {record}"
        assert not box.xpath("ancestor::form")
    header = page.cssselect("table th")[0]
    assert header.text_content().strip() == "Select"
    assert not header.cssselect("input")
    assert not page.cssselect("form[data-cv-bulk] table")
    assert max_form_depth(response.content.decode()) == 1


def test_table_page_renders_actions_without_permission_work(
    client_user_bulk_publisher_view, bulk_publishers, monkeypatch
):
    client = client_user_bulk_publisher_view

    def forbidden(*args, **kwargs):
        pytest.fail("Source rendering called a destination permission or item hook")

    for key in BulkPublisherListView.cv_bulk_actions:
        destination = cv_bulk_publisher.get_view_class(key)
        monkeypatch.setattr(destination, "cv_has_access", classmethod(forbidden))
        monkeypatch.setattr(destination, "cv_bulk_has_permission", forbidden)
        monkeypatch.setattr(destination, "cv_bulk_check", forbidden)
    response = client.get("/bulk-publisher/")
    assert response.status_code == 200
    assert len(soup(response).cssselect("[data-cv-bulk-action]")) == 4
    with CaptureQueriesContext(connection) as bulk_queries:
        client.get("/bulk-publisher/")
    monkeypatch.setattr(BulkPublisherListView, "cv_bulk_actions", ())
    with CaptureQueriesContext(connection) as plain_queries:
        client.get("/bulk-publisher/")
    assert len(bulk_queries) == len(plain_queries)


def test_table_checkbox_label_escapes_record_name(client_user_bulk_publisher_view):
    Publisher.objects.create(name='<b>Bold</b> & "Co"')
    response = client_user_bulk_publisher_view.get("/bulk-publisher/")
    markup = response.content.decode()
    assert 'aria-label="Select &lt;b&gt;Bold&lt;/b&gt; &amp; &quot;Co&quot;"' in markup
    assert "<b>Bold</b>" not in markup


@pytest.mark.parametrize("value", ["custom-bulk-slot", None])
def test_toolbar_class_overrides(client_user_bulk_publisher_view, bulk_publishers, settings, value):
    slots = {
        "toolbar": "form[data-cv-bulk]",
        "controls": "[data-cv-bulk-enhanced] > div",
        "select-all": "[data-cv-bulk-enhanced] label",
        "checkbox": "[data-cv-bulk-all], [data-cv-bulk-item]",
        "actions": "form[data-cv-bulk] > div:last-child",
    }
    settings.CRUD_VIEWS_BUTTON_CLASSES = {f"bulk:{slot}": value for slot in slots}
    page = soup(client_user_bulk_publisher_view.get("/bulk-publisher/"))
    for selector in slots.values():
        elements = page.cssselect(selector)
        assert elements
        assert all(element.get("class", "") == (value or "") for element in elements)
