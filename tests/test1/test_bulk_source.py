"""Rendered table and card selection through destination entry gates."""

from urllib.parse import parse_qs, urlsplit

import pytest
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection
from django.template import Context, RequestContext, Template
from django.template.loader import get_template
from django.test import Client
from django.test.utils import CaptureQueriesContext
from django.utils.translation import override

from crud_views.lib.button_classes import get_button_class
from tests.test1.app.models import Publisher
from tests.test1.app.views_bulk import BulkPublisherCardView, BulkPublisherListView, cv_bulk_publisher
from tests.test1.test_bulk_flow import max_form_depth, soup

pytestmark = pytest.mark.django_db

SOURCE_CASES = [(BulkPublisherListView, "/bulk-publisher/"), (BulkPublisherCardView, "/bulk-publisher/card/")]


def action_keys(response):
    return [button.get("data-cv-bulk-action") for button in soup(response).cssselect("[data-cv-bulk-action]")]


@pytest.mark.parametrize("source,path", SOURCE_CASES)
def test_bulk_partial_permission_denial(source, path, client_user_bulk_publisher_change, bulk_publishers, monkeypatch):
    keys = ("bulk_delete", "archive_now", "archive")
    monkeypatch.setattr(source, "cv_bulk_actions", keys)
    events = spy_bulk_gates(monkeypatch, keys)
    response = client_user_bulk_publisher_change.get(path)
    assert action_keys(response) == ["archive_now", "archive"]
    assert not soup(response).cssselect("#cv-bulk-bulk_delete, [formaction*='bulk-delete']")
    assert [(key, stage) for key, stage, *_ in events] == [
        ("bulk_delete", "access"),
        ("archive_now", "access"),
        ("archive_now", "state"),
        ("archive", "access"),
        ("archive", "state"),
    ]
    assert source.cv_bulk_actions == keys


@pytest.mark.parametrize("source,path", SOURCE_CASES)
@pytest.mark.parametrize("state_hook", ["cv_action_enabled", "_cv_action_enabled_for_rendering"])
def test_bulk_state_disabled_is_omitted(
    source, path, state_hook, client_user_bulk_publisher_delete, bulk_publishers, monkeypatch
):
    monkeypatch.setattr(source, "cv_bulk_actions", ("archive", "bulk_delete"))
    destination = cv_bulk_publisher.get_view_class("bulk_delete")
    monkeypatch.setattr(destination, state_hook, classmethod(lambda cls, *args: False))
    response = client_user_bulk_publisher_delete.get(path)
    assert action_keys(response) == ["archive"]
    assert not soup(response).cssselect("#cv-bulk-bulk_delete, [formaction*='bulk-delete']")
    assert not soup(response).cssselect("[data-cv-bulk-action][disabled]")


@pytest.mark.parametrize("source,path", SOURCE_CASES)
def test_bulk_custom_access_is_authoritative(
    source, path, client_user_bulk_publisher_view, bulk_publishers, monkeypatch
):
    monkeypatch.setattr(source, "cv_bulk_actions", ("archive",))
    destination = cv_bulk_publisher.get_view_class("archive")
    monkeypatch.setattr(destination, "cv_has_access", classmethod(lambda cls, user, obj: True))
    response = client_user_bulk_publisher_view.get(path)
    assert not response.wsgi_request.user.has_perm("app.change_publisher")
    assert action_keys(response) == ["archive"]
    assert soup(response).cssselect("[data-cv-bulk-item]")


@pytest.mark.parametrize("source,path", SOURCE_CASES)
@pytest.mark.parametrize("rows", [0, 3])
@pytest.mark.parametrize("denial", ["permission", "state"])
def test_bulk_all_denied_equals_empty_response(source, path, rows, denial, request, monkeypatch):
    actor = "client_user_bulk_publisher_view" if denial == "permission" else "client_user_bulk_publisher_delete"
    client = request.getfixturevalue(actor)
    for index in range(rows):
        Publisher.objects.create(name=f"Publisher {index}")
    keys = source.cv_bulk_actions
    if denial == "state":
        for key in keys:
            monkeypatch.setattr(
                cv_bulk_publisher.get_view_class(key), "cv_action_enabled", classmethod(lambda cls, user, obj: False)
            )
    # cv_config imports get_token locally; inclusion tags also copy the parent's CSRF token.
    monkeypatch.setattr("django.middleware.csrf.get_token", lambda request: "A" * 64)
    monkeypatch.setattr("django.template.context_processors.get_token", lambda request: "A" * 64)
    denied = client.get(path)
    assert denied.status_code == 200
    assert not soup(denied).cssselect("[data-cv-bulk], [data-cv-bulk-action], [data-cv-bulk-item], .cv-bulk-cell")
    if "table" in denied.context_data:
        assert "cv_bulk_select" not in denied.context_data["table"].columns
    monkeypatch.setattr(source, "cv_bulk_actions", ())
    empty = client.get(path)
    assert empty.status_code == 200
    assert denied.content == empty.content


@pytest.mark.parametrize("source,path", SOURCE_CASES)
def test_bulk_empty_page_keeps_admitted_toolbar(source, path, client_user_bulk_publisher_delete):
    response = client_user_bulk_publisher_delete.get(path)
    assert response.status_code == 200
    assert action_keys(response) == list(source.cv_bulk_actions)
    assert soup(response).cssselect("[data-cv-bulk]")
    assert not soup(response).cssselect("[data-cv-bulk-item]")


@pytest.mark.parametrize("source,path", SOURCE_CASES)
@pytest.mark.parametrize("first_consumer", ["context", "buttons"])
def test_bulk_consumers_share_one_result(
    source, path, first_consumer, client_user_bulk_publisher_delete, bulk_publishers, monkeypatch
):
    keys = source.cv_bulk_actions
    events = spy_bulk_gates(monkeypatch, keys)
    response = client_user_bulk_publisher_delete.get(path)
    rendered = response.context_data["view"]
    if first_consumer == "buttons":
        events.clear()
        view = source()
        view.setup(response.wsgi_request)
        view.object_list = view.get_queryset()
        buttons = view.cv_bulk_buttons
    else:
        view = rendered
        buttons = view.cv_bulk_buttons
    expected_events = list(events)
    for _ in range(2):
        assert view.cv_bulk_buttons is buttons
        context = view.get_context_data()
        assert context["view"] is view
        if source is BulkPublisherListView:
            assert view.get_table_kwargs()["extra_columns"][0][0] == "cv_bulk_select"
    assert events == expected_events
    assert len(events) == len(keys) * 2
    assert view._cv_effective_bulk_actions == keys
    assert source.cv_bulk_actions == keys


@pytest.mark.parametrize("source,path", SOURCE_CASES)
def test_bulk_actor_requests_are_isolated(
    source, path, user_bulk_publisher_view, user_bulk_publisher_delete, bulk_publishers, monkeypatch
):
    reader, editor = Client(), Client()
    reader.force_login(user_bulk_publisher_view)
    editor.force_login(user_bulk_publisher_delete)
    keys = source.cv_bulk_actions
    events = spy_bulk_gates(monkeypatch, keys)
    views = []
    for client, admitted in ((editor, True), (reader, False), (editor, True)):
        events.clear()
        response = client.get(path)
        views.append(response.context_data["view"])
        assert action_keys(response) == (list(keys) if admitted else [])
        assert [(key, stage) for key, stage, *_ in events] == [
            (key, stage) for key in keys for stage in (("access", "state") if admitted else ("access",))
        ]
        assert source.cv_bulk_actions == keys
    assert len({id(view) for view in views}) == 3


def test_bulk_empty_configuration_needs_no_request(monkeypatch):
    monkeypatch.setattr(BulkPublisherListView, "cv_bulk_actions", ())
    monkeypatch.setattr(
        cv_bulk_publisher.get_view_class("archive"),
        "cv_has_access",
        classmethod(lambda *args: pytest.fail("Empty configuration evaluated access")),
    )
    view = BulkPublisherListView()
    assert view.get_table_kwargs() == {"view": view}
    assert view.cv_bulk_buttons == []
    assert view._cv_effective_bulk_actions == ()
    assert not hasattr(view, "request")


@pytest.mark.parametrize("source,path", SOURCE_CASES)
def test_bulk_checks_keep_declared_denied_destinations(source, path, client_user_bulk_publisher_view, monkeypatch):
    keys = source.cv_bulk_actions
    monkeypatch.setattr(source, "paginate_by", 10)
    for key in keys:
        monkeypatch.setattr(cv_bulk_publisher.get_view_class(key), "cv_bulk_max", 1)
    events = spy_bulk_gates(monkeypatch, keys)
    response = client_user_bulk_publisher_view.get(path)
    assert action_keys(response) == []
    before = list(events)
    warnings = [message for check in source.checks() for message in check.messages() if message.id == "viewset.W274"]
    assert len(warnings) == len(keys)
    assert events == before
    assert source.cv_bulk_actions == keys


@pytest.mark.parametrize("source,path", SOURCE_CASES)
@pytest.mark.parametrize("admitted", [False, True])
def test_bulk_custom_template_effective_guard(source, path, admitted, request, bulk_publishers, settings, monkeypatch):
    client = request.getfixturevalue(
        "client_user_bulk_publisher_delete" if admitted else "client_user_bulk_publisher_view"
    )
    name = "app/effective_bulk_content.html"
    template = (
        "{% load crud_views django_tables2 %}{% if view.cv_bulk_buttons %}"
        "{% include 'crud_views/snippets/bulk_toolbar.html' %}{% endif %}TARGET"
    )
    if source is BulkPublisherListView:
        template = template.replace("TARGET", "{% render_table table %}")
    else:
        template = template.replace(
            "TARGET",
            "{% for object in object_list %}{% if view.cv_bulk_buttons %}<div data-custom-cell>"
            '<input name="cv_bulk_ids" data-cv-bulk-item></div>{% endif %}{% cv_card object %}{% endfor %}',
        )
    config = settings.TEMPLATES[0]
    settings.TEMPLATES = [
        {
            **config,
            "APP_DIRS": False,
            "OPTIONS": {
                **config.get("OPTIONS", {}),
                "loaders": [
                    ("django.template.loaders.locmem.Loader", {name: template}),
                    "django.template.loaders.filesystem.Loader",
                    "django.template.loaders.app_directories.Loader",
                ],
            },
        }
    ]
    monkeypatch.setattr(source, "cv_content_template", name)
    monkeypatch.setattr("django.middleware.csrf.get_token", lambda request: "A" * 64)
    monkeypatch.setattr("django.template.context_processors.get_token", lambda request: "A" * 64)
    keys = source.cv_bulk_actions
    events = spy_bulk_gates(monkeypatch, keys)
    labels = []
    originals = [
        (cv_bulk_publisher.get_view_class(key), cv_bulk_publisher.get_view_class(key).cv_get_action_short_label)
        for key in keys
    ]
    for destination, original in originals:

        def label(cls, context, original=original, destination=destination):
            labels.append(destination)
            return original(context)

        monkeypatch.setattr(destination, "cv_get_action_short_label", classmethod(label))
    response = client.get(path)
    assert response.status_code == 200
    assert action_keys(response) == (list(keys) if admitted else [])
    assert bool(soup(response).cssselect("[data-cv-bulk-item]")) is admitted
    assert bool(soup(response).cssselect("[data-custom-cell]")) is (admitted and source is BulkPublisherCardView)
    view = response.context_data["view"]
    before = list(events)
    buttons = view.cv_bulk_buttons
    rendered = get_template(name).render(response.context_data, request=response.wsgi_request)
    assert rendered
    assert view.cv_bulk_buttons is buttons
    assert events == before
    assert labels == ([cv_bulk_publisher.get_view_class(key) for key in keys] if admitted else [])
    assert not any("effective" in key for key in response.context_data)
    if not admitted:
        monkeypatch.setattr(source, "cv_bulk_actions", ())
        empty = client.get(path)
        assert response.content == empty.content
        assert events == before


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
    assert [button.get("data-cv-bulk-action") for button in soup(admitted).cssselect("[data-cv-bulk-action]")] == list(
        source.cv_bulk_actions
    )


class SilentGateError(Exception):
    silent_variable_failure = True


def spy_bulk_gates(monkeypatch, keys):
    """Bind all inherited originals before patching any of their parent classes."""
    originals = [
        (
            key,
            cv_bulk_publisher.get_view_class(key),
            cv_bulk_publisher.get_view_class(key).cv_has_access,
            cv_bulk_publisher.get_view_class(key)._cv_action_enabled_for_rendering,
        )
        for key in keys
    ]
    events = []

    def forbidden(*args, **kwargs):
        pytest.fail("Source rendering evaluated an item hook")

    for key, destination, original_access, original_state in originals:

        def access(cls, user, obj, key=key, original=original_access, destination=destination):
            assert cls is destination and obj is None
            events.append((key, "access", user, obj))
            return original(user, obj)

        def state(cls, user, obj, source, key=key, original=original_state, destination=destination):
            assert cls is destination and obj is None
            events.append((key, "state", user, source))
            return original(user, obj, source)

        monkeypatch.setattr(destination, "cv_has_access", classmethod(access))
        monkeypatch.setattr(destination, "_cv_action_enabled_for_rendering", classmethod(state))
        monkeypatch.setattr(destination, "cv_bulk_has_permission", forbidden)
        monkeypatch.setattr(destination, "cv_bulk_check", forbidden)
    return events


@pytest.mark.parametrize(
    "source,path,actor",
    [
        (BulkPublisherListView, "/bulk-publisher/", "client_user_bulk_publisher_delete"),
        (BulkPublisherCardView, "/bulk-publisher/card/", "client_user_bulk_publisher_change"),
    ],
)
def test_source_destination_gate_cost(source, path, actor, request, bulk_publishers, monkeypatch):
    client = request.getfixturevalue(actor)
    keys = source.cv_bulk_actions
    events = spy_bulk_gates(monkeypatch, keys)

    def assert_events(response):
        assert [(key, stage) for key, stage, *_ in events] == [
            (key, stage) for key in keys for stage in ("access", "state")
        ]
        assert all(user == response.wsgi_request.user for _, _, user, _ in events)
        assert all(obj is response.context_data["view"] for _, stage, _, obj in events if stage == "state")

    response = client.get(path)
    assert response.status_code == 200
    assert len(soup(response).cssselect("[data-cv-bulk-action]")) == len(keys)
    assert_events(response)
    events.clear()
    with CaptureQueriesContext(connection) as bulk_queries:
        response = client.get(path)
    assert_events(response)
    events.clear()
    monkeypatch.setattr(source, "cv_bulk_actions", ())
    with CaptureQueriesContext(connection) as plain_queries:
        client.get(path)
    assert not events
    assert len(bulk_queries) == len(plain_queries)


@pytest.mark.parametrize(
    "source,path", [(BulkPublisherListView, "/bulk-publisher/"), (BulkPublisherCardView, "/bulk-publisher/card/")]
)
@pytest.mark.parametrize("rows", [0, 5])
@pytest.mark.parametrize("hook", ["cv_has_access", "cv_action_enabled"])
@pytest.mark.parametrize("error_class", [ObjectDoesNotExist, Publisher.DoesNotExist, SilentGateError, RuntimeError])
def test_bulk_rendered_gate_exceptions(
    source, path, rows, hook, error_class, client_user_bulk_publisher_change, monkeypatch
):
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


def test_table_toolbar_controls(client_user_bulk_publisher_delete, bulk_publishers):
    response = client_user_bulk_publisher_delete.get("/bulk-publisher/")
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
def test_bulk_label_floor(client_user_bulk_publisher_delete, settings, mode):
    settings.CRUD_VIEWS_LABEL_MODE_DEFAULTS = {"bulk": mode}
    settings.CRUD_VIEWS_STRICT = True
    page = soup(client_user_bulk_publisher_delete.get("/bulk-publisher/"))
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


def test_bulk_floor_is_independent_of_form(client_user_bulk_publisher_delete, settings):
    settings.CRUD_VIEWS_LABEL_MODE_DEFAULTS = {"form": "icon"}
    settings.CRUD_VIEWS_STRICT = True
    page = soup(client_user_bulk_publisher_delete.get("/bulk-publisher/"))
    delete = page.cssselect('[data-cv-bulk-action="bulk_delete"]')[0]
    assert delete.cssselect("i, svg")
    assert delete.cssselect("span")[0].get("class") is None
    assert delete.get("class") == get_button_class("form", "submit", "both")


@pytest.mark.parametrize("mode", ["icon", "both"])
def test_disabled_action_icon_uses_visible_label(client_user_bulk_publisher_delete, settings, mode):
    settings.CRUD_VIEWS_ICONS = {"delete": None}
    settings.CRUD_VIEWS_LABEL_MODE_DEFAULTS = {"bulk": mode}
    settings.CRUD_VIEWS_STRICT = True
    response = client_user_bulk_publisher_delete.get("/bulk-publisher/")
    assert response.status_code == 200
    button = soup(response).cssselect('[data-cv-bulk-action="bulk_delete"]')[0]
    assert not button.cssselect("i, svg")
    assert button.text_content().strip() == "Delete"
    assert button.cssselect("span")[0].get("class") is None
    assert button.get("class") == get_button_class("form", "submit", "label")


def test_table_checkboxes_and_structure(client_user_bulk_publisher_delete, bulk_publishers):
    response = client_user_bulk_publisher_delete.get("/bulk-publisher/")
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


def test_table_checkbox_label_escapes_record_name(client_user_bulk_publisher_delete):
    Publisher.objects.create(name='<b>Bold</b> & "Co"')
    response = client_user_bulk_publisher_delete.get("/bulk-publisher/")
    markup = response.content.decode()
    assert 'aria-label="Select &lt;b&gt;Bold&lt;/b&gt; &amp; &quot;Co&quot;"' in markup
    assert "<b>Bold</b>" not in markup


@pytest.mark.parametrize("value", ["custom-bulk-slot", None])
def test_toolbar_class_overrides(client_user_bulk_publisher_delete, bulk_publishers, settings, value):
    slots = {
        "toolbar": "form[data-cv-bulk]",
        "controls": "[data-cv-bulk-enhanced] > div",
        "select-all": "[data-cv-bulk-enhanced] label",
        "checkbox": "[data-cv-bulk-all], [data-cv-bulk-item]",
        "actions": "form[data-cv-bulk] > div:last-child",
    }
    settings.CRUD_VIEWS_BUTTON_CLASSES = {f"bulk:{slot}": value for slot in slots}
    page = soup(client_user_bulk_publisher_delete.get("/bulk-publisher/"))
    for selector in slots.values():
        elements = page.cssselect(selector)
        assert elements
        assert all(element.get("class", "") == (value or "") for element in elements)


def test_card_selection_and_form_structure(client_user_bulk_publisher_change, bulk_publishers):
    response = client_user_bulk_publisher_change.get("/bulk-publisher/card/")
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


def test_card_selection_survives_custom_template(client_user_bulk_publisher_change, bulk_publishers, monkeypatch):
    monkeypatch.setattr(BulkPublisherCardView, "cv_card_template", "app/bulk_card.html")
    response = client_user_bulk_publisher_change.get("/bulk-publisher/card/")
    boxes = soup(response).cssselect("[data-cv-bulk-item]")
    assert len(boxes) == 2
    for box, record in zip(boxes, bulk_publishers[:2], strict=True):
        assert len(box.getparent().cssselect("input")) == 1
        paragraph = box.getnext()
        assert paragraph.tag == "p"
        assert paragraph.text_content() == record.name


@pytest.mark.parametrize("value", ["custom-card-slot", None])
def test_card_class_overrides(client_user_bulk_publisher_change, bulk_publishers, settings, value):
    settings.CRUD_VIEWS_BUTTON_CLASSES = {"bulk:card-cell": value, "bulk:card-select": value}
    boxes = soup(client_user_bulk_publisher_change.get("/bulk-publisher/card/")).cssselect("[data-cv-bulk-item]")
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


def test_card_toolbar_carries_card_origin(client_user_bulk_publisher_change, bulk_publishers):
    page = soup(client_user_bulk_publisher_change.get("/bulk-publisher/card/"))
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


def test_empty_card_page_keeps_toolbar(client_user_bulk_publisher_change):
    page = soup(client_user_bulk_publisher_change.get("/bulk-publisher/card/"))
    assert len(page.cssselect("[data-cv-bulk]")) == 1
    assert not page.cssselect("[data-cv-bulk-item]")
    assert "No items found." in page.text_content()


def test_card_checkbox_label_escapes_record_name(client_user_bulk_publisher_change):
    Publisher.objects.create(name='<b>Bold</b> & "Co"')
    response = client_user_bulk_publisher_change.get("/bulk-publisher/card/")
    markup = response.content.decode()
    assert 'aria-label="Select &lt;b&gt;Bold&lt;/b&gt; &amp; &quot;Co&quot;"' in markup
    assert "<b>Bold</b>" not in markup


def test_card_checkbox_value_ignores_number_localization(client_user_bulk_publisher_change, settings):
    settings.USE_THOUSAND_SEPARATOR = True
    Publisher.objects.create(pk=12345, name="Alpha")
    with override("de"):
        assert Template("{{ pk }}").render(Context({"pk": 12345})) == "12.345"
        page = soup(client_user_bulk_publisher_change.get("/bulk-publisher/card/"))
        assert [box.get("value") for box in page.cssselect("[data-cv-bulk-item]")] == ["12345"]
