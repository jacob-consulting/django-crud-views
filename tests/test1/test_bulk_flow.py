"""The table selection, review and execution contract for bulk actions."""

import pytest
from django.contrib.auth.models import Permission
from django.contrib.messages import get_messages
from lxml import html

from tests.test1.app.models import Publisher

pytestmark = pytest.mark.django_db


def soup(response):
    return html.fromstring(response.content)


def test_table_review_execute_flow(client_user_publisher_view, user_publisher_view):
    user_publisher_view.user_permissions.add(Permission.objects.get(codename="change_publisher"))
    records = [Publisher.objects.create(name=name) for name in ("Alpha", "Beta")]
    client = client_user_publisher_view
    response = client.get("/bulk-publisher/")
    assert response.status_code == 200
    page = soup(response)
    toolbar = page.cssselect("form#cv-bulk-selection")[0]
    assert toolbar.get("method") == "post"
    assert toolbar.cssselect('input[name="csrfmiddlewaretoken"]')
    button = toolbar.cssselect('button[data-cv-bulk-action="archive"]')[0]
    assert button.get("type") == "submit"
    assert button.get("name") == "cv_bulk_stage"
    assert button.get("value") == "review"
    assert button.get("formaction").startswith("/bulk-publisher/archive/?")
    from crud_views.lib.button_classes import get_button_class
    from crud_views.lib.view.label_mode import default_label_mode

    assert button.get("class") == get_button_class("form", "submit", default_label_mode("form"))
    checkboxes = page.cssselect('input[name="cv_bulk_ids"]')
    assert [box.get("value") for box in checkboxes] == [str(obj.pk) for obj in records]
    assert all(box.get("form") == "cv-bulk-selection" for box in checkboxes)
    heading = page.cssselect("table thead th")[0]
    assert heading.text_content().strip() == "Select"
    assert not heading.cssselect("input")

    destination = button.get("formaction")
    response = client.post(destination, {"cv_bulk_stage": "review", "cv_bulk_ids": [obj.pk for obj in records]})
    assert response.status_code == 200
    assert not response.context["form"].is_bound
    page = soup(response)
    assert "Archive selected publishers" in page.text_content()
    form = page.cssselect("form.cv-form")[0]
    assert form.get("action") == destination
    assert form.cssselect('input[name="cv_bulk_stage"]')[0].get("value") == "execute"
    assert [field.get("value") for field in form.cssselect('input[name="cv_bulk_ids"]')] == [
        str(obj.pk) for obj in records
    ]
    assert "Confirm" in form.text_content()
    assert "Cancel" in form.text_content()
    for obj in records:
        assert obj.name in form.text_content()
        assert not [link for link in form.cssselect("a") if link.text_content() == obj.name]
    assert list(Publisher.objects.order_by("pk").values_list("name", flat=True)) == ["Alpha", "Beta"]

    response = client.post(destination, {"cv_bulk_stage": "execute", "cv_bulk_ids": [obj.pk for obj in records]})
    assert response.status_code == 302
    assert response.url == "/bulk-publisher/"
    assert list(Publisher.objects.order_by("pk").values_list("name", flat=True)) == [
        "Alpha (archived)",
        "Beta (archived)",
    ]
    assert [str(message) for message in get_messages(response.wsgi_request)] == ["2 records processed."]


def test_destination_admission_precedes_item_hooks(client_user_bulk_publisher_view, bulk_publishers, monkeypatch):
    from unittest.mock import Mock

    from tests.test1.app.views_bulk import BulkPublisherArchiveView

    permission = Mock(side_effect=AssertionError("permission hook must not run"))
    check = Mock(side_effect=AssertionError("business hook must not run"))
    monkeypatch.setattr(BulkPublisherArchiveView, "cv_bulk_has_permission", permission)
    monkeypatch.setattr(BulkPublisherArchiveView, "cv_bulk_check", check)
    response = client_user_bulk_publisher_view.post(
        "/bulk-publisher/archive/", {"cv_bulk_stage": "review", "cv_bulk_ids": [bulk_publishers[0].pk]}
    )
    assert response.status_code == 403
    permission.assert_not_called()
    check.assert_not_called()
    assert list(Publisher.objects.order_by("pk").values_list("name", flat=True)) == ["Alpha", "Beta", "Locked Gamma"]


def test_execute_changed_selection_writes_nothing(client_user_bulk_publisher_change, bulk_publishers):
    response = client_user_bulk_publisher_change.post(
        "/bulk-publisher/archive/",
        {"cv_bulk_stage": "execute", "cv_bulk_ids": [bulk_publishers[0].pk, bulk_publishers[2].pk]},
    )
    assert response.status_code == 200
    message = "The eligible selection changed. Review it and confirm again."
    assert response.context["form"].non_field_errors() == [message]
    assert message in soup(response).text_content()
    assert list(Publisher.objects.order_by("pk").values_list("name", flat=True)) == ["Alpha", "Beta", "Locked Gamma"]
    assert not list(get_messages(response.wsgi_request))


def test_bulk_public_namespace():
    from crud_views.lib import bulk

    assert bulk.__all__ == ["BulkConfirmForm", "BulkFormViewPermissionRequired", "BulkSelectionMixin"]
    assert not hasattr(bulk, "BulkFormView")
    assert not hasattr(bulk, "BulkMixin")
    assert "per request" in bulk.BulkFormViewPermissionRequired.__doc__
    assert "not configured by a subclass" in bulk.BulkFormViewPermissionRequired.__doc__
    assert "post" not in bulk.BulkSelectionMixin.__dict__


@pytest.mark.parametrize("path", ["/publisher/", "/bulk-publisher/"])
def test_nonparticipant_table_content_is_unchanged(
    client_user_bulk_publisher_change, bulk_publishers, monkeypatch, path
):
    from django.template import RequestContext, Template
    from django.template.loader import get_template

    from tests.test1.app.views_bulk import BulkPublisherListView

    monkeypatch.setattr(BulkPublisherListView, "cv_bulk_actions", ())
    response = client_user_bulk_publisher_change.get(path)
    assert response.status_code == 200
    assert not soup(response).cssselect("[data-cv-bulk], [data-cv-bulk-item]")
    view = response.context["view"]
    context = {"view": view, "table": view.get_table(**view.get_table_kwargs())}
    old = Template("{% load django_tables2 %}\n\n{% render_table table %}\n")
    new = get_template("crud_views/view_list_table.content.html")
    rendered = new.render(context, request=response.wsgi_request)
    context["table"] = view.get_table(**view.get_table_kwargs())
    assert rendered == old.render(RequestContext(response.wsgi_request, context))


def _table_response(client, monkeypatch, kind):
    import django_tables2 as tables

    from crud_views.lib.table import Table, TableWithViewContext
    from crud_views.lib.views import ListViewTableMixin
    from tests.test1.app.views_bulk import BulkPublisherListView

    class DefaultTable(Table):
        id = tables.Column()
        name = tables.Column()

    class SequencedTable(DefaultTable):
        class Meta:
            sequence = ("name", "...", "actions")

    class ExcludedActionsTable(DefaultTable):
        class Meta:
            exclude = ("actions",)

    class NoActionsTable(TableWithViewContext):
        id = tables.Column()
        name = tables.Column()

    table_classes = {
        "default": DefaultTable,
        "meta": SequencedTable,
        "keyword": DefaultTable,
        "excluded": ExcludedActionsTable,
        "no_actions": NoActionsTable,
    }
    monkeypatch.setattr(BulkPublisherListView, "table_class", table_classes[kind])
    if kind == "keyword":
        monkeypatch.setattr(
            ListViewTableMixin, "get_table_kwargs", lambda self: {"view": self, "sequence": ("name", "...", "actions")}
        )
    response = client.get("/bulk-publisher/")
    assert response.status_code == 200
    return [column.name for column in response.context["table"].columns]


def test_table_sequence_default(client_user_bulk_publisher_change, bulk_publishers, monkeypatch):
    assert _table_response(client_user_bulk_publisher_change, monkeypatch, "default") == [
        "cv_bulk_select",
        "id",
        "name",
        "actions",
    ]


def test_table_sequence_meta(client_user_bulk_publisher_change, bulk_publishers, monkeypatch):
    assert _table_response(client_user_bulk_publisher_change, monkeypatch, "meta") == [
        "cv_bulk_select",
        "name",
        "id",
        "actions",
    ]


def test_table_sequence_keyword(client_user_bulk_publisher_change, bulk_publishers, monkeypatch):
    assert _table_response(client_user_bulk_publisher_change, monkeypatch, "keyword") == [
        "cv_bulk_select",
        "name",
        "id",
        "actions",
    ]


def test_table_sequence_excluded_actions(client_user_bulk_publisher_change, bulk_publishers, monkeypatch):
    assert _table_response(client_user_bulk_publisher_change, monkeypatch, "excluded") == [
        "cv_bulk_select",
        "id",
        "name",
    ]


def test_table_sequence_without_actions(client_user_bulk_publisher_change, bulk_publishers, monkeypatch):
    assert _table_response(client_user_bulk_publisher_change, monkeypatch, "no_actions") == [
        "cv_bulk_select",
        "id",
        "name",
    ]


def test_review_hidden_ids_ignore_number_localization(client_user_bulk_publisher_change, settings):
    from django.template import Context, Template
    from django.utils.translation import override

    settings.USE_THOUSAND_SEPARATOR = True
    Publisher.objects.create(pk=12345, name="Alpha")
    Publisher.objects.create(pk=12346, name="Locked Beta")
    client = client_user_bulk_publisher_change
    with override("de"):
        assert Template("{{ pk }}").render(Context({"pk": 12345})) == "12.345"
        page = soup(client.get("/bulk-publisher/"))
        assert [box.get("value") for box in page.cssselect('input[name="cv_bulk_ids"]')] == ["12345", "12346"]
        response = client.post("/bulk-publisher/archive/", {"cv_bulk_stage": "review", "cv_bulk_ids": [12345, 12346]})
        assert response.status_code == 200
        page = soup(response)
        selected = [field.get("value") for field in page.cssselect('input[name="cv_bulk_ids"]')]
        excluded = [field.get("value") for field in page.cssselect('input[name="cv_bulk_blocked_ids"]')]
        assert selected == ["12345"]
        assert excluded == ["12346"]
        response = client.post(
            "/bulk-publisher/archive/",
            {
                "cv_bulk_stage": "execute",
                "cv_bulk_ids": selected,
                "cv_bulk_blocked_ids": excluded,
            },
        )
    assert response.status_code == 302
    assert Publisher.objects.get(pk=12345).name == "Alpha (archived)"
    assert Publisher.objects.get(pk=12346).name == "Locked Beta"
