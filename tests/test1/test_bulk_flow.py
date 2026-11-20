"""The table selection, review and execution contract for bulk actions."""

import re

import pytest
from django.contrib.auth.models import Permission
from django.contrib.messages import get_messages
from lxml import html

from tests.test1.app.models import Publisher

pytestmark = pytest.mark.django_db


def soup(response):
    return html.fromstring(response.content)


def max_form_depth(markup):
    depth = maximum = 0
    for tag in re.finditer(r"<\s*(/?)form\b[^>]*>", markup, re.IGNORECASE):
        depth += -1 if tag.group(1) else 1
        maximum = max(maximum, depth)
    return maximum


def review_data(response):
    form = soup(response).cssselect("form.cv-form")[0]
    return {
        name: [field.get("value") for field in form.cssselect(f'input[name="{name}"]')]
        for name in ("cv_bulk_stage", "cv_bulk_ids", "cv_bulk_blocked_ids")
    }


def destination_from_source(client, key="archive"):
    page = soup(client.get("/bulk-publisher/?sort=name&page=1"))
    return page.cssselect(f'button[data-cv-bulk-action="{key}"]')[0].get("formaction")


def test_skip_confirmation_executes(client_user_bulk_publisher_change, bulk_publishers, monkeypatch):
    from tests.test1.app.views_bulk import BulkPublisherArchiveView

    monkeypatch.setattr(BulkPublisherArchiveView, "cv_bulk_confirm", False)
    response = client_user_bulk_publisher_change.post(
        "/bulk-publisher/archive/", {"cv_bulk_stage": "review", "cv_bulk_ids": [bulk_publishers[0].pk]}
    )
    assert response.status_code == 302
    bulk_publishers[0].refresh_from_db()
    assert bulk_publishers[0].name == "Alpha (archived)"
    assert [str(message) for message in get_messages(response.wsgi_request)] == ["1 record processed."]


def test_mixed_selection_overrides_skip(client_user_bulk_publisher_change):
    records = [Publisher.objects.create(name=f"Publisher {i}") for i in range(8)]
    blocked = [Publisher.objects.create(name=f"Locked {i}") for i in range(2)]
    client = client_user_bulk_publisher_change
    response = client.post(
        "/bulk-publisher/archive-now/",
        {"cv_bulk_stage": "review", "cv_bulk_ids": [obj.pk for obj in records + blocked]},
    )
    assert response.status_code == 200
    assert not response.context["form"].is_bound
    assert not Publisher.objects.filter(name__endswith="(archived)").exists()
    alert = soup(response).cssselect('[role="alert"]')[0]
    assert "2 records will be skipped" in alert.text_content()
    for obj in blocked:
        assert obj.name in alert.text_content()
    assert "Locked publishers cannot be archived." in alert.text_content()
    from crud_views.lib.button_classes import get_button_class

    assert alert.get("class") == get_button_class("alert", "warning")
    data = review_data(response)
    assert data["cv_bulk_ids"] == [str(obj.pk) for obj in records]
    assert data["cv_bulk_blocked_ids"] == [str(obj.pk) for obj in blocked]
    response = client.post("/bulk-publisher/archive-now/", data)
    assert response.status_code == 302
    assert Publisher.objects.filter(name__endswith="(archived)").count() == 8
    assert Publisher.objects.filter(name__startswith="Locked").count() == 2


def test_input_form_reviews_then_executes(client_user_bulk_publisher_change, bulk_publishers):
    client = client_user_bulk_publisher_change
    destination = destination_from_source(client, "rename")
    response = client.post(destination, {"cv_bulk_stage": "review", "cv_bulk_ids": [bulk_publishers[0].pk]})
    assert response.status_code == 200
    assert not response.context["form"].is_bound
    form = soup(response).cssselect("form.cv-form")[0]
    assert form.cssselect('input[name="suffix"]')
    assert form.cssselect('button[type="submit"]')[0].text_content().strip() == "Rename"
    assert form.cssselect("[data-cv-cancel-url]")[0].get("data-cv-cancel-url") == (
        "/bulk-publisher/?sort=name&page=1&cv_from_restore=1"
    )
    assert publisher_names() == ["Alpha", "Beta", "Locked Gamma"]
    response = client.post(destination, {**review_data(response), "suffix": " renamed"})
    assert response.status_code == 302
    assert publisher_names() == ["Alpharenamed", "Beta", "Locked Gamma"]
    assert [str(message) for message in get_messages(response.wsgi_request)] == ["1 publishers renamed."]


def test_invalid_input_keeps_both_groups(client_user_bulk_publisher_change, bulk_publishers):
    response = client_user_bulk_publisher_change.post(
        "/bulk-publisher/rename/",
        {
            "cv_bulk_stage": "execute",
            "cv_bulk_ids": [bulk_publishers[0].pk],
            "cv_bulk_blocked_ids": [bulk_publishers[2].pk],
        },
    )
    assert response.status_code == 200
    assert response.context["form"].errors["suffix"] == ["This field is required."]
    assert "This field is required." in soup(response).text_content()
    assert "Alpha" in soup(response).cssselect("form.cv-form > ul")[0].text_content()
    assert "Locked Gamma" in soup(response).cssselect('[role="alert"]')[0].text_content()
    assert publisher_names() == ["Alpha", "Beta", "Locked Gamma"]
    assert not list(get_messages(response.wsgi_request))


@pytest.mark.parametrize("stage", ["review", "execute"])
def test_all_blocked_page_is_cancel_only(client_user_bulk_publisher_change, bulk_publishers, stage):
    client = client_user_bulk_publisher_change
    response = client.post(
        destination_from_source(client), {"cv_bulk_stage": stage, "cv_bulk_ids": [bulk_publishers[2].pk]}
    )
    assert response.status_code == 200
    assert not response.context["form"].is_bound
    form = soup(response).cssselect("form.cv-form")[0]
    assert not form.cssselect('button[type="submit"]')
    controls = form.cssselect("[data-cv-cancel-url]")
    assert len(controls) == 1
    assert controls[0].get("data-cv-cancel-url") == "/bulk-publisher/?sort=name&page=1&cv_from_restore=1"
    assert "Locked Gamma" in form.cssselect('[role="alert"]')[0].text_content()
    assert "Locked publishers cannot be archived." in form.text_content()
    assert "None of the selected records can be processed." in form.text_content()
    assert "The eligible selection changed." not in form.text_content()
    assert publisher_names() == ["Alpha", "Beta", "Locked Gamma"]


def test_all_blocked_page_keeps_cancel_without_cancel_target(
    client_user_bulk_publisher_change, bulk_publishers, monkeypatch
):
    from crud_views.lib.button_classes import get_button_class
    from tests.test1.app.views_bulk import BulkPublisherListView

    client = client_user_bulk_publisher_change
    destination = destination_from_source(client)
    monkeypatch.setattr(BulkPublisherListView, "cv_has_access", classmethod(lambda cls, user, obj=None: False))
    response = client.post(destination, {"cv_bulk_stage": "review", "cv_bulk_ids": [bulk_publishers[2].pk]})
    assert response.status_code == 200
    form = soup(response).cssselect("form.cv-form")[0]
    controls = form.cssselect("[data-cv-cancel-url]")
    assert len(controls) == 1
    button = controls[0]
    assert button.tag == "button" and button.get("type") == "button"
    assert button.text_content().strip() == "Cancel"
    assert button.get("class") == get_button_class("form", "cancel")
    assert button.get("data-cv-cancel-url") == response.context["view"].get_success_url()
    assert not form.cssselect('button[type="submit"]')
    response = client.post(destination, {"cv_bulk_stage": "review", "cv_bulk_ids": [bulk_publishers[0].pk]})
    form = soup(response).cssselect("form.cv-form")[0]
    assert form.cssselect('button[type="submit"]')[0].text_content().strip() == "Confirm"
    assert not form.cssselect("[data-cv-cancel-url]")


def test_eligibility_loss_requires_new_confirmation(client_user_bulk_publisher_change, bulk_publishers):
    client = client_user_bulk_publisher_change
    response = client.post(
        "/bulk-publisher/archive/", {"cv_bulk_stage": "review", "cv_bulk_ids": [obj.pk for obj in bulk_publishers[:2]]}
    )
    Publisher.objects.filter(pk=bulk_publishers[1].pk).update(name="Locked Beta")
    response = client.post("/bulk-publisher/archive/", review_data(response))
    assert response.status_code == 200
    assert "The eligible selection changed. Review it and confirm again." in soup(response).text_content()
    assert publisher_names() == ["Alpha", "Locked Beta", "Locked Gamma"]
    data = review_data(response)
    assert data["cv_bulk_ids"] == [str(bulk_publishers[0].pk)]
    assert data["cv_bulk_blocked_ids"] == [str(bulk_publishers[1].pk)]
    response = client.post("/bulk-publisher/archive/", data)
    assert response.status_code == 302
    assert publisher_names() == ["Alpha (archived)", "Locked Beta", "Locked Gamma"]


def test_excluded_record_stays_excluded(client_user_bulk_publisher_change, bulk_publishers):
    client = client_user_bulk_publisher_change
    data = {
        "cv_bulk_stage": "review",
        "cv_bulk_ids": [bulk_publishers[0].pk],
        "cv_bulk_blocked_ids": [bulk_publishers[1].pk],
    }
    response = client.post("/bulk-publisher/archive/", data)
    assert response.status_code == 200
    assert "Excluded from this confirmation; select it again from the list." in soup(response).text_content()
    assert review_data(response)["cv_bulk_blocked_ids"] == [str(bulk_publishers[1].pk)]
    data["cv_bulk_stage"] = "execute"
    assert client.post("/bulk-publisher/archive/", data).status_code == 302
    assert publisher_names() == ["Alpha (archived)", "Beta", "Locked Gamma"]


def test_now_eligible_candidate_can_execute_directly(client_user_bulk_publisher_change, bulk_publishers):
    client = client_user_bulk_publisher_change
    data = {"cv_bulk_stage": "review", "cv_bulk_ids": [bulk_publishers[2].pk]}
    response = client.post("/bulk-publisher/archive/", data)
    assert response.context["bulk_review"].blocked
    Publisher.objects.filter(pk=bulk_publishers[2].pk).update(name="Gamma")
    data["cv_bulk_stage"] = "execute"
    assert client.post("/bulk-publisher/archive/", data).status_code == 302
    assert publisher_names() == ["Alpha", "Beta", "Gamma (archived)"]


def test_unavailable_record_has_no_visible_label_or_id(client_user_bulk_publisher_change, bulk_publishers):
    response = client_user_bulk_publisher_change.post(
        "/bulk-publisher/archive/", {"cv_bulk_stage": "review", "cv_bulk_ids": [987654321, bulk_publishers[2].pk]}
    )
    rows = soup(response).cssselect('[role="alert"] li')
    assert rows[0].text_content().strip() == "This item is unavailable for this action."
    assert "987654321" not in soup(response).text_content()
    assert "Locked Gamma" in rows[1].text_content()
    assert "Locked publishers cannot be archived." in rows[1].text_content()


def test_review_layout_lists_every_record(client_user_bulk_publisher_change):
    records = [Publisher.objects.create(name=f"Publisher {i}") for i in range(30)]
    client = client_user_bulk_publisher_change
    data = {"cv_bulk_stage": "review", "cv_bulk_ids": [obj.pk for obj in records]}
    response = client.post("/bulk-publisher/archive/", data)
    page = soup(response)
    assert not page.cssselect('[role="alert"]')
    assert len(page.cssselect("form.cv-form > ul > li")) == 30
    assert "To process: 30" in page.text_content()
    data["cv_bulk_ids"].append(Publisher.objects.create(name="Locked Extra").pk)
    response = client.post("/bulk-publisher/archive/", data)
    form = soup(response).cssselect("form.cv-form")[0]
    assert not form.cssselect("ul a, [role=alert] a")
    markup = response.content.decode()
    assert markup.index('role="alert"') < markup.index("To process: 30") < markup.index('type="submit"')


def test_review_escapes_names_and_reasons_and_holds_one_form(client_user_bulk_publisher_change, monkeypatch):
    from django.utils.html import escape

    from tests.test1.app.views_bulk import BulkPublisherArchiveView

    names = ['<b>Bold</b> & "quoted"', "Locked <i>Italic</i>"]
    reason = "<em>policy</em> &"
    records = [Publisher.objects.create(name=name) for name in names]
    monkeypatch.setattr(
        BulkPublisherArchiveView, "cv_bulk_check", lambda self, obj: [reason] if obj.pk == records[1].pk else []
    )
    response = client_user_bulk_publisher_change.post(
        "/bulk-publisher/archive/", {"cv_bulk_stage": "review", "cv_bulk_ids": [obj.pk for obj in records]}
    )
    markup = response.content.decode()
    for value in (*names, reason):
        assert str(escape(value)) in markup
        assert value not in markup
    page = soup(response)
    assert not page.cssselect("form.cv-form li b, form.cv-form li i, form.cv-form li em")
    assert names[0] in page.cssselect("form.cv-form > ul > li")[0].text_content()
    blocked = page.cssselect('[role="alert"] li')[0].text_content()
    assert names[1] in blocked and reason in blocked
    assert len(page.cssselect("form.cv-form")) == 1
    assert max_form_depth(markup) == 1
    start = re.search(r'<form\b[^>]*class="cv-form"[^>]*>', markup).end()
    form_markup = markup[start : markup.index("</form>", start)]
    for name in ("cv_bulk_stage", "cv_bulk_ids", "cv_bulk_blocked_ids"):
        assert f'name="{name}"' in form_markup
    assert "Confirm" in form_markup


def test_review_snippet_overrides_keep_transport(client_user_bulk_publisher_change, bulk_publishers):
    from tests.test1.test_form_frame import _theme_templates

    with _theme_templates(
        {
            "crud_views/snippets/bulk/eligible.html": "<p>Eligible override {{ bulk_review.objects|length }}</p>",
            "crud_views/snippets/bulk/blocked.html": "<p>Blocked override {{ bulk_review.blocked|length }}</p>",
        }
    ):
        response = client_user_bulk_publisher_change.post(
            "/bulk-publisher/archive/",
            {"cv_bulk_stage": "review", "cv_bulk_ids": [bulk_publishers[0].pk, bulk_publishers[2].pk]},
        )
    assert "Eligible override 1" in soup(response).text_content()
    assert "Blocked override 1" in soup(response).text_content()
    assert review_data(response) == {
        "cv_bulk_stage": ["execute"],
        "cv_bulk_ids": [str(bulk_publishers[0].pk)],
        "cv_bulk_blocked_ids": [str(bulk_publishers[2].pk)],
    }


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

    assert button.get("class") == get_button_class("form", "submit", "label")
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
    assert "Alpha" in soup(response).cssselect("form.cv-form > ul")[0].text_content()
    assert "Locked Gamma" in soup(response).cssselect('[role="alert"]')[0].text_content()
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


def publisher_names():
    return list(Publisher.objects.order_by("pk").values_list("name", flat=True))


def forbid_resolution(monkeypatch):
    from unittest.mock import Mock

    from tests.test1.app.views_bulk import BulkPublisherArchiveView

    hooks = []
    for name in ("_review_selection", "cv_bulk_has_permission", "cv_bulk_check"):
        hook = Mock(side_effect=AssertionError(f"{name} must not run"))
        monkeypatch.setattr(BulkPublisherArchiveView, name, hook)
        hooks.append(hook)
    return hooks


@pytest.mark.parametrize("stage", ["review", "execute"])
@pytest.mark.parametrize("selection", ["empty", "oversized", "mixed"])
def test_selection_mistakes_warn_before_loading(
    client_user_bulk_publisher_change, bulk_publishers, monkeypatch, stage, selection
):
    from django.contrib.messages import WARNING

    data = {"cv_bulk_stage": stage}
    if selection == "oversized":
        data["cv_bulk_ids"] = list(range(1, 102))
    elif selection == "mixed":
        data["cv_bulk_ids"] = list(range(1, 61))
        data["cv_bulk_blocked_ids"] = list(range(61, 102))
    hooks = forbid_resolution(monkeypatch)
    before = publisher_names()
    response = client_user_bulk_publisher_change.post("/bulk-publisher/archive/", data)
    assert response.status_code == 302
    assert response.url == "/bulk-publisher/"
    expected = "Select at least one record." if selection == "empty" else "Select at most 100 records."
    assert [(message.level, str(message)) for message in get_messages(response.wsgi_request)] == [(WARNING, expected)]
    assert publisher_names() == before
    for hook in hooks:
        hook.assert_not_called()


@pytest.mark.parametrize("count,limit", [(100, 100), (120, 150)])
def test_selection_within_destination_limit_is_reviewed(client_user_bulk_publisher_change, monkeypatch, count, limit):
    from tests.test1.app.views_bulk import BulkPublisherArchiveView

    records = Publisher.objects.bulk_create([Publisher(name=f"Publisher {index}") for index in range(count)])
    if limit != 100:
        monkeypatch.setattr(BulkPublisherArchiveView, "cv_bulk_max", limit)
    response = client_user_bulk_publisher_change.post(
        "/bulk-publisher/archive/", {"cv_bulk_stage": "review", "cv_bulk_ids": [obj.pk for obj in records]}
    )
    assert response.status_code == 200
    assert len(response.context["bulk_review"].objects) == count
    assert not response.context["form"].is_bound
    assert publisher_names() == [obj.name for obj in records]
    assert not list(get_messages(response.wsgi_request))


def test_warning_returns_to_signed_source_query(client_user_bulk_publisher_change, bulk_publishers):
    from urllib.parse import parse_qs, urlsplit

    client = client_user_bulk_publisher_change
    page = soup(client.get("/bulk-publisher/?sort=name&page=1"))
    destination = page.cssselect('button[data-cv-bulk-action="archive"]')[0].get("formaction")
    response = client.post(destination, {"cv_bulk_stage": "review"})
    assert response.status_code == 302
    assert urlsplit(response.url).path == "/bulk-publisher/"
    assert parse_qs(urlsplit(response.url).query) == {"sort": ["name"], "page": ["1"], "cv_from_restore": ["1"]}
    assert [str(message) for message in get_messages(response.wsgi_request)] == ["Select at least one record."]
    assert publisher_names() == ["Alpha", "Beta", "Locked Gamma"]


def test_plain_get_redirects_silently(client_user_bulk_publisher_change, bulk_publishers):
    client = client_user_bulk_publisher_change
    page = soup(client.get("/bulk-publisher/?sort=name&page=1"))
    destination = page.cssselect('button[data-cv-bulk-action="archive"]')[0].get("formaction")
    response = client.get(destination)
    assert response.status_code == 302
    assert response.url == "/bulk-publisher/?sort=name&page=1&cv_from_restore=1"
    assert not list(get_messages(response.wsgi_request))
    response = client.get("/bulk-publisher/archive/")
    assert response.status_code == 302
    assert response.url == "/bulk-publisher/"
    assert not list(get_messages(response.wsgi_request))
    assert publisher_names() == ["Alpha", "Beta", "Locked Gamma"]


@pytest.mark.parametrize("stage", [None, ["review", "execute"], "other"])
def test_invalid_stage_is_bad_request(client_user_bulk_publisher_change, bulk_publishers, stage):
    data = {"cv_bulk_ids": [bulk_publishers[0].pk]}
    if stage is not None:
        data["cv_bulk_stage"] = stage
    response = client_user_bulk_publisher_change.post("/bulk-publisher/archive/", data)
    assert response.status_code == 400
    assert publisher_names() == ["Alpha", "Beta", "Locked Gamma"]
    assert not list(get_messages(response.wsgi_request))


@pytest.mark.parametrize("value", ["abc", "", "1.0", "99999999999999999999999"])
@pytest.mark.parametrize("stage", ["review", "execute"])
def test_invalid_id_is_bad_request(client_user_bulk_publisher_change, bulk_publishers, value, stage):
    response = client_user_bulk_publisher_change.post(
        "/bulk-publisher/archive/", {"cv_bulk_stage": stage, "cv_bulk_ids": [value]}
    )
    assert response.status_code == 400
    assert publisher_names() == ["Alpha", "Beta", "Locked Gamma"]
    assert not list(get_messages(response.wsgi_request))


def test_overlapping_ids_are_bad_request(client_user_bulk_publisher_change, bulk_publishers):
    pk = bulk_publishers[0].pk
    response = client_user_bulk_publisher_change.post(
        "/bulk-publisher/archive/", {"cv_bulk_stage": "review", "cv_bulk_ids": [pk], "cv_bulk_blocked_ids": [pk]}
    )
    assert response.status_code == 400
    assert publisher_names() == ["Alpha", "Beta", "Locked Gamma"]
    assert not list(get_messages(response.wsgi_request))


def test_normalized_ids_deduplicate_before_review_and_execute(client_user_bulk_publisher_change):
    Publisher.objects.create(pk=1, name="Alpha")
    client = client_user_bulk_publisher_change
    data = {"cv_bulk_stage": "review", "cv_bulk_ids": ["01", " 1", "1"]}
    response = client.post("/bulk-publisher/archive/", data)
    assert response.status_code == 200
    assert response.context["bulk_review"].ids == ("1",)
    assert publisher_names() == ["Alpha"]
    data["cv_bulk_stage"] = "execute"
    response = client.post("/bulk-publisher/archive/", data)
    assert response.status_code == 302
    assert publisher_names() == ["Alpha (archived)"]
    assert [str(message) for message in get_messages(response.wsgi_request)] == ["1 record processed."]


def _database_rejected_id(client, monkeypatch, records, stage):
    from unittest.mock import Mock

    from django.db import DataError
    from django.db.models import QuerySet

    from tests.test1.app.views_bulk import BulkPublisherArchiveView

    class DatabaseRejectedQuerySet(QuerySet):
        def _fetch_all(self):
            raise DataError("simulated database rejection")

    monkeypatch.setattr(
        BulkPublisherArchiveView, "_selection_queryset", lambda self: DatabaseRejectedQuerySet(Publisher)
    )
    permission = Mock(side_effect=AssertionError("permission hook must not run"))
    check = Mock(side_effect=AssertionError("business hook must not run"))
    monkeypatch.setattr(BulkPublisherArchiveView, "cv_bulk_has_permission", permission)
    monkeypatch.setattr(BulkPublisherArchiveView, "cv_bulk_check", check)
    response = client.post("/bulk-publisher/archive/", {"cv_bulk_stage": stage, "cv_bulk_ids": [records[0].pk]})
    assert response.status_code == 400
    assert publisher_names() == ["Alpha", "Beta", "Locked Gamma"]
    assert not list(get_messages(response.wsgi_request))
    permission.assert_not_called()
    check.assert_not_called()


def test_database_rejected_id_is_bad_request_on_review(client_user_bulk_publisher_change, bulk_publishers, monkeypatch):
    _database_rejected_id(client_user_bulk_publisher_change, monkeypatch, bulk_publishers, "review")


def test_database_rejected_id_is_bad_request_on_execute(
    client_user_bulk_publisher_change, bulk_publishers, monkeypatch
):
    _database_rejected_id(client_user_bulk_publisher_change, monkeypatch, bulk_publishers, "execute")


def test_read_ids_rejects_nul_character_in_selected_ids():
    from django.core.exceptions import BadRequest
    from django.db.models import CharField
    from django.http import QueryDict

    from crud_views.lib.bulk import _read_ids

    post = QueryDict("", mutable=True)
    post.setlist("cv_bulk_ids", ["A\x001"])
    with pytest.raises(BadRequest, match=r"Invalid selected object IDs\."):
        _read_ids(post, CharField(max_length=20, primary_key=True))


def test_read_ids_rejects_nul_character_in_excluded_ids():
    from django.core.exceptions import BadRequest
    from django.db.models import CharField
    from django.http import QueryDict

    from crud_views.lib.bulk import _read_ids

    post = QueryDict("", mutable=True)
    post.setlist("cv_bulk_ids", ["valid"])
    post.setlist("cv_bulk_blocked_ids", ["A\x001"])
    with pytest.raises(BadRequest, match=r"Invalid selected object IDs\."):
        _read_ids(post, CharField(max_length=20, primary_key=True))


def _nul_character_id(client, monkeypatch, stage):
    hooks = forbid_resolution(monkeypatch)
    response = client.post("/bulk-publisher/archive/", {"cv_bulk_stage": stage, "cv_bulk_ids": ["1\x00"]})
    assert response.status_code == 400
    assert publisher_names() == ["Alpha", "Beta", "Locked Gamma"]
    assert not list(get_messages(response.wsgi_request))
    for hook in hooks:
        hook.assert_not_called()


def test_nul_character_id_is_bad_request_on_review(client_user_bulk_publisher_change, bulk_publishers, monkeypatch):
    _nul_character_id(client_user_bulk_publisher_change, monkeypatch, "review")


def test_nul_character_id_is_bad_request_on_execute(client_user_bulk_publisher_change, bulk_publishers, monkeypatch):
    _nul_character_id(client_user_bulk_publisher_change, monkeypatch, "execute")
