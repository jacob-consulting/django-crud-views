"""Rendered table and card selection, without permission work on source pages."""

from urllib.parse import parse_qs, urlsplit

import pytest
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection
from django.template import Context, RequestContext, Template
from django.template.loader import get_template
from django.test.utils import CaptureQueriesContext
from django.test import Client
from django.utils.translation import override

from crud_views.lib.button_classes import get_button_class
from tests.test1.app.models import Publisher
from tests.test1.app.views_bulk import BulkPublisherCardView, BulkPublisherListView, cv_bulk_publisher
from tests.test1.test_bulk_flow import max_form_depth, soup

pytestmark = pytest.mark.django_db

ORIGINAL_CARD_CONTENT = """{% load i18n crud_views %}

{% include "crud_views/snippets/card_order.html" %}

<div class="row">
    {% for object in object_list %}
        <div class="{{ view.cv_card_container_class }}">
            {% cv_card object %}
        </div>
        {% empty %}
        <div class="col-12">
            <p class="text-muted">{% translate "No items found." %}</p>
        </div>
    {% endfor %}
</div>

{% cv_pagination %}
"""


@pytest.mark.parametrize("path", ["/bulk-publisher/", "/bulk-publisher/card/"])
def test_bulk_visibility_tracer(path, user_bulk_publisher_view, user_bulk_publisher_delete, bulk_publishers):
    reader, editor = Client(), Client()
    reader.force_login(user_bulk_publisher_view)
    editor.force_login(user_bulk_publisher_delete)
    denied = reader.get(path)
    assert denied.status_code == 200
    assert not soup(denied).cssselect("[data-cv-bulk], [data-cv-bulk-action], [data-cv-bulk-item]")
    admitted = editor.get(path)
    source = BulkPublisherCardView if "card" in path else BulkPublisherListView
    assert [button.get("data-cv-bulk-action") for button in soup(admitted).cssselect("[data-cv-bulk-action]")] == list(source.cv_bulk_actions)


class SilentGateError(Exception):
    silent_variable_failure = True


@pytest.mark.parametrize("source,path", [(BulkPublisherListView, "/bulk-publisher/"), (BulkPublisherCardView, "/bulk-publisher/card/")])
@pytest.mark.parametrize("rows", [0, 5])
@pytest.mark.parametrize("hook", ["cv_has_access", "cv_action_enabled"])
@pytest.mark.parametrize("error_class", [ObjectDoesNotExist, Publisher.DoesNotExist, SilentGateError, RuntimeError])
def test_bulk_rendered_gate_exceptions(source, path, rows, hook, error_class, client_user_bulk_publisher_change, monkeypatch):
    for index in range(rows):
        Publisher.objects.create(name=f"Publisher {index}")
    monkeypatch.setattr(source, "paginate_by", 10)
    monkeypatch.setattr(source, "cv_bulk_actions", ("archive",))
    destination = cv_bulk_publisher.get_view_class("archive")
    original_access = destination.cv_has_access
    error = error_class("destination gate failure")
    events = []

    def access(cls, user, obj):
        events.append("access")
        if hook == "cv_has_access":
            raise error
        return original_access(user, obj)

    def state(cls, user, obj):
        events.append("state")
        raise error

    def forbidden(*args, **kwargs):
        pytest.fail("Source rendering evaluated an item hook")

    monkeypatch.setattr(destination, "cv_has_access", classmethod(access))
    monkeypatch.setattr(destination, "cv_action_enabled", classmethod(state))
    monkeypatch.setattr(destination, "cv_bulk_has_permission", forbidden)
    monkeypatch.setattr(destination, "cv_bulk_check", forbidden)
    with pytest.raises(error_class) as caught:
        client_user_bulk_publisher_change.get(path)
    assert caught.value is error
    assert events == (["access"] if hook == "cv_has_access" else ["access", "state"])


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
    assert set(first.attrib) == {"type", "formmethod", "hidden"}
    assert first.get("formmethod") == "dialog"
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
        assert (
            button.text_content().strip()
            == {"archive": "Archive", "archive_now": "Archive now", "rename": "Archive", "bulk_delete": "Delete"}[key]
        )
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


def test_card_selection_and_form_structure(client_user_bulk_publisher_view, bulk_publishers):
    response = client_user_bulk_publisher_view.get("/bulk-publisher/card/")
    assert response.status_code == 200
    page = soup(response)
    assert len(page.cssselect("form#cv-card-order-form")) == 1
    assert len(page.cssselect("form#cv-bulk-selection")) == 1
    markup = response.content.decode()
    order_end = markup.index("</form>", markup.index('id="cv-card-order-form"'))
    assert markup.index('<form id="cv-bulk-selection"') > order_end
    assert max_form_depth(markup) == 1
    boxes = page.cssselect("[data-cv-bulk-item]")
    assert len(boxes) == 2
    for box, record in zip(boxes, bulk_publishers[:2], strict=True):
        assert box.get("type") == "checkbox"
        assert box.get("name") == "cv_bulk_ids"
        assert box.get("value") == str(record.pk)
        assert box.get("form") == "cv-bulk-selection"
        assert box.get("aria-label") == f"Select {record}"
        assert box.get("class") == get_button_class("bulk", "card-select")
        cell = box.getparent()
        assert cell.get("class") == get_button_class("bulk", "card-cell")
        assert cell.getparent().get("class") == BulkPublisherCardView.cv_card_container_class
        assert len(cell.cssselect("[data-cv-bulk-item]")) == 1
        assert box.getnext() is not None and "card" in box.getnext().get("class").split()
    form = page.cssselect("form[data-cv-bulk]")[0]
    assert len(form.cssselect("[data-cv-bulk-all]")) == 1
    assert form.cssselect("[data-cv-bulk-enhanced][hidden]")
    assert [button.get("data-cv-bulk-action") for button in form.cssselect("[data-cv-bulk-action]")] == [
        "archive",
        "archive_now",
    ]


def test_card_selection_survives_custom_template(client_user_bulk_publisher_view, bulk_publishers, monkeypatch):
    monkeypatch.setattr(BulkPublisherCardView, "cv_card_template", "app/bulk_card.html")
    response = client_user_bulk_publisher_view.get("/bulk-publisher/card/")
    boxes = soup(response).cssselect("[data-cv-bulk-item]")
    assert len(boxes) == 2
    for box, record in zip(boxes, bulk_publishers[:2], strict=True):
        assert len(box.getparent().cssselect("input")) == 1
        paragraph = box.getnext()
        assert paragraph.tag == "p"
        assert paragraph.text_content() == record.name


@pytest.mark.parametrize("value", ["custom-card-slot", None])
def test_card_class_overrides(client_user_bulk_publisher_view, bulk_publishers, settings, value):
    settings.CRUD_VIEWS_BUTTON_CLASSES = {"bulk:card-cell": value, "bulk:card-select": value}
    boxes = soup(client_user_bulk_publisher_view.get("/bulk-publisher/card/")).cssselect("[data-cv-bulk-item]")
    assert len(boxes) == 2
    for box in boxes:
        assert box.get("class", "") == (value or "")
        assert box.getparent().get("class", "") == (value or "")


@pytest.mark.parametrize("path", ["/publisher/card/", "/bulk-publisher/card/"])
def test_nonparticipant_card_content_is_byte_identical(
    client_user_bulk_publisher_view, bulk_publishers, monkeypatch, path
):
    monkeypatch.setattr(BulkPublisherCardView, "cv_bulk_actions", ())
    response = client_user_bulk_publisher_view.get(path)
    assert response.status_code == 200
    assert not soup(response).cssselect("[data-cv-bulk], [data-cv-bulk-item]")
    context = response.context_data.copy()
    old = Template(ORIGINAL_CARD_CONTENT).render(RequestContext(response.wsgi_request, context))
    new = get_template("crud_views/view_card.content.html").render(context, request=response.wsgi_request)
    assert new == old


def test_card_toolbar_carries_card_origin(client_user_bulk_publisher_view, bulk_publishers):
    page = soup(client_user_bulk_publisher_view.get("/bulk-publisher/card/"))
    buttons = page.cssselect("[data-cv-bulk-action]")
    assert len(buttons) == 2
    for button in buttons:
        assert parse_qs(urlsplit(button.get("formaction")).query)["cv_from"] == ["card"]


@pytest.mark.parametrize("path", ["/bulk-publisher/", "/bulk-publisher/card/"])
@pytest.mark.parametrize("key,mixed", [("archive_now", False), ("archive_now", True), ("archive", False)])
def test_shared_action_confirmation_from_both_sources(
    client_user_bulk_publisher_change, bulk_publishers, path, key, mixed
):
    client = client_user_bulk_publisher_change
    page = soup(client.get(path))
    buttons = page.cssselect(f'[data-cv-bulk-action="{key}"]')
    assert len(buttons) == 1
    ids = [bulk_publishers[0].pk]
    if mixed:
        ids.append(bulk_publishers[2].pk)
    response = client.post(buttons[0].get("formaction"), {"cv_bulk_stage": "review", "cv_bulk_ids": ids})
    bulk_publishers[0].refresh_from_db()
    if key == "archive_now" and not mixed:
        assert response.status_code == 302
        assert bulk_publishers[0].name == "Alpha (archived)"
    else:
        assert response.status_code == 200
        assert bulk_publishers[0].name == "Alpha"
        assert soup(response).cssselect("form.cv-form")
        assert not response.context["form"].is_bound
        if mixed:
            assert "Locked Gamma" in soup(response).cssselect('[role="alert"]')[0].text_content()


def test_empty_card_page_keeps_toolbar(client_user_bulk_publisher_view):
    page = soup(client_user_bulk_publisher_view.get("/bulk-publisher/card/"))
    assert len(page.cssselect("[data-cv-bulk]")) == 1
    assert not page.cssselect("[data-cv-bulk-item]")
    assert "No items found." in page.text_content()


def test_card_page_renders_actions_without_permission_work(
    client_user_bulk_publisher_view, bulk_publishers, monkeypatch
):
    calls = []

    def record_call(*args, **kwargs):
        calls.append((args, kwargs))
        return True

    for key in BulkPublisherCardView.cv_bulk_actions:
        destination = cv_bulk_publisher.get_view_class(key)
        monkeypatch.setattr(destination, "cv_has_access", classmethod(record_call))
        monkeypatch.setattr(destination, "cv_bulk_has_permission", record_call)
        monkeypatch.setattr(destination, "cv_bulk_check", record_call)
    client = client_user_bulk_publisher_view
    response = client.get("/bulk-publisher/card/")
    assert response.status_code == 200
    assert not response.wsgi_request.user.has_perm("app.change_publisher")
    page = soup(response)
    for key in ("archive", "archive_now"):
        assert len(page.cssselect(f'[data-cv-bulk-action="{key}"]')) == 1
    assert len(page.cssselect("[data-cv-bulk-item]")) == 2
    assert calls == []
    with CaptureQueriesContext(connection) as bulk_queries:
        client.get("/bulk-publisher/card/")
    monkeypatch.setattr(BulkPublisherCardView, "cv_bulk_actions", ())
    with CaptureQueriesContext(connection) as plain_queries:
        client.get("/bulk-publisher/card/")
    assert len(bulk_queries) == len(plain_queries)
    assert calls == []


def test_card_checkbox_label_escapes_record_name(client_user_bulk_publisher_view):
    Publisher.objects.create(name='<b>Bold</b> & "Co"')
    response = client_user_bulk_publisher_view.get("/bulk-publisher/card/")
    markup = response.content.decode()
    assert 'aria-label="Select &lt;b&gt;Bold&lt;/b&gt; &amp; &quot;Co&quot;"' in markup
    assert "<b>Bold</b>" not in markup


def test_card_checkbox_value_ignores_number_localization(client_user_bulk_publisher_view, settings):
    settings.USE_THOUSAND_SEPARATOR = True
    Publisher.objects.create(pk=12345, name="Alpha")
    with override("de"):
        assert Template("{{ pk }}").render(Context({"pk": 12345})) == "12.345"
        page = soup(client_user_bulk_publisher_view.get("/bulk-publisher/card/"))
        assert [box.get("value") for box in page.cssselect("[data-cv-bulk-item]")] == ["12345"]
